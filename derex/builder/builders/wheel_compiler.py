from .schema import wheel_compiler_schema
from derex.builder import logger
from derex.builder.builders.base import BaseBuilder
from derex.builder.builders.base import create_builder
from derex.builder.builders.base import load_conf
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List

import os


WHEELS_CACHE = os.environ.get("WHEELS_CACHE")
WC_VOLUMES: List[str] = []
if WHEELS_CACHE is not None:
    if Path(WHEELS_CACHE).is_dir():
        WC_VOLUMES = ["-v", f"{WHEELS_CACHE}:/wheels_cache"]
    else:
        logger.error(
            f'The directory "{WHEELS_CACHE} specified in WHEELS_CACHE does not exist"'
        )


class BuildahWheelCompiler(BaseBuilder):
    """Use a builder image to compile a set of python wheels,
    and create a new image by installing them in the base image.

    Use the path in the environment variable WHEELS_CACHE as a wheel cache.
    Copy the newly built wheels to the cache (maybe overwriting the already present ones).
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
            volumes = ["-v", f"{tmp_whs}:/wheelhouse"] + WC_VOLUMES
            base_run = lambda *args: self.buildah_run(
                container=base_container, args=list(args), extra_args=volumes
            )
            builder_run = lambda *args: self.buildah_run(
                container=builder_container, args=list(args), extra_args=volumes
            )
            builder_run("mkdir", "-p", requirements_dir)
            builder_run("pip", "install", "wheel")
            for requirement in self.requirements:
                src = os.path.join(self.path, requirement)
                dest = os.path.join(requirements_dir, requirement)
                self.buildah("copy", builder_container, src, dest)
                logger.info(f"Installing {requirement}")
                logger.debug(open(src).read())
                # If numpy is not installed scipy will refuse to compile.
                # There is some build time potentially wasted. Maybe make it optional.
                builder_run(*"pip install -r".split(), dest)
                logger.info(f"Compiling wheels for {requirement}")
                wheel_cache_opts = (
                    "" if WHEELS_CACHE is None else "--find-links /wheels_cache"
                )
                builder_run(
                    *f"pip wheel {wheel_cache_opts} --wheel-dir=/wheelhouse -r".split(),
                    dest,
                )
                if WHEELS_CACHE is not None:
                    builder_run("sh", "-c", "cp -rv /wheelhouse/* /wheels_cache/")
            logger.info(f"Created wheeels:\n{'n'.join(os.listdir(tmp_whs))}")
            base_run("sh", "-c", "pip install /wheelhouse/*")
        self.buildah("commit", "--rm", base_container, self.dest)
        self.buildah("rm", builder_container)

    def hash(self):
        elements = [
            self.__class__.__name__,
            self.hash_conf(),
            self.get_source_target(self.sources["base"], path=self.path),
            self.get_source_target(self.sources["builder"], path=self.path),
            self.hash_files(self.requirements),
        ]
        return self.mkhash("\n".join(elements))
