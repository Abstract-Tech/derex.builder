import os
from tempfile import TemporaryDirectory

from derex.builder import logger
from derex.builder.builders.base import BaseBuilder, create_builder

from .schema import wheel_compiler_schema


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
            base_run = lambda *args: self.buildah(
                "run", *(volumes + [base_container] + list(args))
            )
            builder_run = lambda *args: self.buildah(
                "run", *(volumes + [builder_container] + list(args))
            )
            builder_run("mkdir", "-p", requirements_dir)
            logger.info(builder_run("pip", "install", "wheel"))
            for requirement in self.requirements:
                src = os.path.join(self.path, requirement)
                dest = os.path.join(requirements_dir, requirement)
                logger.info(self.buildah("copy", builder_container, src, dest))
                logger.info(f"Compiling {requirement}")
                logger.debug(open(src).read())
                logger.info(
                    builder_run(
                        *"pip wheel --wheel-dir=/wheelhouse -r".split(" "), f"{dest}"
                    )
                )
            logger.info(f"Created wheeels:\n{'n'.join(os.listdir(tmp_whs))}")
            logger.info(base_run("sh", "-c", "pip install /wheelhouse/*"))
        self.buildah("commit", "--rm", base_container, self.dest)
        self.buildah("rm", builder_container)

    def docker_image(self):
        pass

    def hash(self):
        return self.hash_files(self.requirements)
