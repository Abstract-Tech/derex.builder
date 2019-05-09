"""Classes to build docker images using Buildah.
"""
import json
import logging
import os
import subprocess
from pathlib import PosixPath
from typing import Dict, List, Union

from derex.builder.builders.base import BaseBuilder, create_builder

logger = logging.getLogger(__name__)


class ImageFound:
    pass


class BuildahBuilder(BaseBuilder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scripts = self.conf["scripts"]
        self.source = self.conf["source"]
        self.dest = f'{self.conf["dest"]}:{self.docker_tag()}'

    def validate(self):
        """Check that all resources referenced from the yaml file actually exist.
        """

    def available_buildah(self) -> bool:
        """Returns True if an image generated with this builder can be found in the local buildah registry.
        """
        if f"localhost/{self.dest}" in self.list_buildah_images():
            return True
        return False

    def list_buildah_images(self) -> List[str]:
        """Returns a list of all images locally available to buildah
        """
        images = json.loads(self.buildah("images", "--json"))
        return sum((el["names"] for el in images if el["names"]), [])

    def hash(self) -> str:
        """Return a hash representing this builder.
        The hash should is built from the conf and the content of the scripts.
        """
        texts = [self.hash_conf()]
        for script in self.conf["scripts"]:
            path = PosixPath(self.path, script)
            texts.append(path.read_text())
        return self.mkhash("\n".join(texts))

    def docker_image(self):
        return self.dest

    def resolve_base_image(self) -> str:
        """Makes sure the base image is available and returns its name.
        """
        if not isinstance(self.source, str):
            builder = create_builder(self.resolve_source_path(self.source))
            builder.resolve()
            return builder.docker_image()
        else:  # The source is a string, so it should be available in the docker hub
            return self.source  # We might pull the image here

    def resolve_source_path(self, source: Dict) -> str:
        """Given the `source` part of a configuration, find the directory it refers to.
        """
        if source["type"] == "derex-relative":
            return os.path.join(os.path.dirname(self.path), source["path"])
        else:
            raise ConfigurationError(f'Unknown type: {source["type"]}')

    def resolve(self):
        """Try to pull or build the image if not already present.
        """
        if not self.available_buildah():
            self.run()

    def run(self):
        """Builds the image specified by this builder.
        """
        base_image = self.resolve_base_image()
        container = self.buildah("from", base_image)
        buildah = lambda cmd, *args: self.buildah(cmd, container, *args)
        script_dir = "/opt/derex/bin"
        buildah("run", "mkdir", "-p", script_dir)
        for script in self.scripts:
            src = os.path.join(self.path, script)
            dest = os.path.join(script_dir, script)
            logger.info(buildah("copy", src, dest))
            buildah("run", "chmod", "a+x", dest)
            buildah("run", dest)
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


class ConfigurationError(Exception):
    pass
