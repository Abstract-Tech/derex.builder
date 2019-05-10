"""Classes to build docker images using Buildah.
"""
import json
import logging
import os
import subprocess
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
        self.dest = f'{self.conf["dest"]}:{self.docker_tag()}'

    def available_buildah(self) -> bool:
        """Returns True if an image generated with this builder can be found in the local buildah registry.
        """
        image_name = f"localhost/{self.dest}"
        if image_name in self.list_buildah_images():
            logger.debug(f"{image_name} found localy")
            return True
        logger.debug(f"{image_name} could not be found localy")
        return False

    def list_buildah_images(self) -> List[str]:
        """Returns a list of all images locally available to buildah
        """
        images = json.loads(self.buildah("images", "--json"))
        return sum((el["names"] for el in images if el["names"]), [])

    def hash(self) -> str:
        """Return a hash representing this builder.
        The hash is built from the yaml configuration and the content of the scripts.
        """
        return self.hash_files(self.scripts)

    def docker_image(self):
        return self.dest

    def resolve(self):
        """Try to pull or build the image if not already present.
        """
        if not self.available_buildah():
            logger.debug(f"Building {self.dest}")
            self.build()

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

    def buildah(self, *args: str) -> str:
        """Utility function to invoke buildah
        """
        cmd = ["buildah"]
        if os.getuid() != 0:
            cmd = ["sudo"] + cmd
        return subprocess.check_output(cmd + list(args)).decode("utf-8").strip()
