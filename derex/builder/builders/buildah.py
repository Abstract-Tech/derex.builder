"""Classes to build docker images using Buildah.
"""
import json
import logging
import os
from typing import Dict, List, Union

from derex.builder import logger
from derex.builder.builders.base import BaseBuilder, create_builder

from .schema import buildah_schema


class ImageFound:
    pass


class BuildahBuilder(BaseBuilder):
    json_schema = buildah_schema

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scripts = self.conf["scripts"]
        self.source = self.conf["source"]

    def hash(self) -> str:
        """Return a hash representing this builder.
        The hash is built from the yaml configuration and the content of the scripts.
        """
        return self.hash_files(self.scripts)

    def docker_image(self):
        return self.dest

    def build(self):
        """Builds the image specified by this builder.
        """
        logger.info(f"Building {self.path}")
        base_image = self.resolve_base_image(self.source, self.path)
        container = self.buildah("from", base_image)
        buildah = lambda cmd, *args: self.buildah(cmd, container, *args)
        script_dir = "/opt/derex/bin"
        buildah("run", "mkdir", "-p", script_dir)
        for script in self.scripts:
            src = os.path.join(self.path, script)
            dest = os.path.join(script_dir, script)
            logger.info(buildah("copy", src, dest))
            logger.info(f"Running {script}")
            buildah("run", "chmod", "a+x", dest)
            buildah("run", dest)
        logger.info(f"Finished running scripts")
        self.buildah("commit", "--rm", container, self.dest)

    def push_to_docker(self):
        self.resolve()
        self.buildah("push", self.dest, f"docker-daemon:{self.dest}")
