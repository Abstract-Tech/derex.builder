"""Classes to build docker images using Buildah.
"""
from .schema import buildah_schema
from derex.builder import logger
from derex.builder.builders.base import BaseBuilder
from derex.builder.builders.base import create_builder
from typing import Dict
from typing import List
from typing import Union

import json
import logging
import os
import py.path


class ImageFound:
    pass


class BuildahBuilder(BaseBuilder):
    json_schema = buildah_schema

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scripts = self.conf["scripts"]
        self.source = self.conf["source"]
        self.copy = self.conf.get("copy", {})

    def hash(self) -> str:
        """Return a hash representing this builder.
        The hash is built from the yaml configuration, the content of the scripts
        and the base config/image tag.
        """
        elements = [
            self.__class__.__name__,
            self.hash_conf(),
            self.get_source_target(self.source, path=self.path),
            self.hash_files(self.scripts),
        ]
        return self.mkhash("\n".join(elements))

    def build(self):
        """Builds the image specified by this builder.
        """
        logger.info(f"Building {self.path}")
        base_image = self.resolve_base_image(self.source, self.path)
        container = self.buildah("from", base_image, print_output=False)
        buildah_run = lambda *args: self.buildah_run(container, args)
        script_dir = "/opt/derex/bin"
        buildah_run("mkdir", "-p", script_dir)

        def copy(local_src, dest):
            with py.path.local(self.path).as_cwd():
                src = str(py.path.local(local_src))
            logger.info(self.buildah("copy", container, src, dest))

        for src, dest in self.copy.items():
            copy(src, dest)
        for script in self.scripts:
            src = os.path.join(self.path, script)
            dest = os.path.join(script_dir, script)
            copy(src, dest)
            logger.info(f"Running {script}")
            buildah_run("chmod", "a+x", dest)
            buildah_run(dest)
        logger.info(f"Finished running scripts")
        self.buildah("commit", "--rm", container, self.dest)
