from .schema import wheel_compiler_schema
from derex.builder import logger
from derex.builder.builders.base import BaseBuilder
from derex.builder.builders.base import create_builder
from derex.builder.builders.base import load_conf
from tempfile import TemporaryDirectory

import os


class BuildahWheelCompiler(BaseBuilder):
    """Uses a builder image to compile a set of python wheels,
    and creates a new image by installing them in the base image.
    """

    json_schema = wheel_compiler_schema

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sources = self.conf["sources"]
        self.requirements = self.conf["requirements"]

    def build(self):
        logger.info(f"Building {self.path}")
        base_image = self.resolve_base_image(self.sources["base"], self.path)
        builder_image = self.resolve_base_image(self.sources["builder"], self.path)
        base_container = self.buildah("from", base_image)
        builder_container = self.buildah("from", builder_image)
        requirements_dir = "/etc/derex.builder.requirements"
        with TemporaryDirectory("wheelhouse") as tmp_whs:
            volumes = ["-v", f"{tmp_whs}:/wheelhouse"]
            base_run = lambda *args: self.buildah_run(
                container=base_container, args=list(args), extra_args=volumes
            )
            builder_run = lambda *args: self.buildah_run(
                container=builder_container, args=list(args), extra_args=volumes
            )
            builder_run("mkdir", "-p", requirements_dir)
            logger.info(builder_run("pip", "install", "wheel"))
            for requirement in self.requirements:
                src = os.path.join(self.path, requirement)
                dest = os.path.join(requirements_dir, requirement)
                logger.info(self.buildah("copy", builder_container, src, dest))
                logger.info(f"Installing {requirement}")
                logger.debug(open(src).read())
                # If numpy is not installed scipy will refuse to compile.
                # There is some build time potentially wasted. Maybe make it optional.
                logger.info(builder_run(*"pip install -r".split(" "), f"{dest}"))
                logger.info(f"Compiling wheels for {requirement}")
                logger.info(
                    builder_run(
                        *"pip wheel --wheel-dir=/wheelhouse -r".split(" "), f"{dest}"
                    )
                )
            logger.info(f"Created wheeels:\n{'n'.join(os.listdir(tmp_whs))}")
            logger.info(base_run("sh", "-c", "pip install /wheelhouse/*"))
        self.buildah("commit", "--rm", base_container, self.dest)
        self.buildah("rm", builder_container)

    def hash(self):
        return self.hash_files(self.requirements)
