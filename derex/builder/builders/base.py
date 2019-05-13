"""Base class and utility methods for yaml-based image definitions.
"""
import hashlib
import json
import os
import subprocess
import urllib.request
from abc import ABC, abstractmethod
from pathlib import PosixPath
from typing import Dict, List
from urllib.error import HTTPError

import yaml
from derex.builder import logger
from jsonschema import validate
from zope.dottedname.resolve import resolve


class BaseBuilder(ABC):
    """A builder takes a configuration directory and executes it to build a docker image.
    """

    @property
    def dest(self):
        return f'{self.conf["dest"]}:{self.docker_tag()}'

    def __init__(self, path: str):
        """
        :param file_path: A path to a directory containing a spec yaml file and other support files.
        """
        logger.info(f"Instantiating builder for {path}")
        self.path = self.sanitize_path(path)
        self.conf = load_conf(path)
        self.validate()

    def sanitize_path(self, path: str) -> str:
        """Makes sure a path is valid and points to a directory.
        It also removes a trailing slash if present.
        """
        if path.endswith("/"):
            return path[:-1]
        return path

    def validate(self):
        """Check that all resources referenced from the yaml file actually exist.
        """
        validate(self.conf, self.json_schema)

    @abstractmethod
    def build(self):
        """Build the docker image based on the given configuration.
        Concrete classes should override this method.
        """

    @abstractmethod
    def hash(self) -> str:
        """Return a hash representing this builder.
        The hash should be constructed so that any change that would
        result in a functionally different image changes the hash.
        """

    def resolve(self):
        """Try to pull or build the image if not already present.
        """
        if not self.available_buildah():
            logger.debug(f"Image {self.dest} not found locally")
            if self.available_docker_registry():
                logger.info(f"Pulling {self.dest} from docker registry")
                self.buildah("pull", self.dest)
            else:
                logger.info(f"Building {self.dest}")
                self.build()

    def available_docker_registry(self):
        # TODO: refator so this is available without calling `split`
        image_name = self.dest.split(":")[0]

        token_url = f"https://auth.docker.io/token?service=registry.docker.io&scope=repository:{image_name}:pull"
        try:
            token = json.loads(urllib.request.urlopen(token_url).read())["token"]
            url = f"https://registry-1.docker.io/v2/{image_name}/tags/list"
            req = urllib.request.Request(
                url, headers={"Authorization": f"Bearer {token}"}
            )
            response = urllib.request.urlopen(req)
        except HTTPError as e:
            logger.error(e)
            return False
        parsed_response = json.loads(response.read())
        if self.docker_tag() in parsed_response["tags"]:
            logger.debug(f"Found {self.dest} on docker registry")
            return True

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

    def buildah(self, *args: str) -> str:
        """Utility function to invoke buildah
        """
        cmd = ["buildah"]
        if os.getuid() != 0:
            cmd = ["sudo"] + cmd
        return subprocess.check_output(cmd + list(args)).decode("utf-8").strip()

    def docker_tag(self) -> str:
        """Returns a string usable as docker tag, derived from the hash.
        """
        return self.hash()[:10]

    def hash_conf(self) -> str:
        """Return a hash representing this builder's config.
        The hash is constructed after parsing the file, so comments
        or key ordering is not relevant to hashing
        """
        return self.mkhash(json.dumps(self.conf, sort_keys=True))

    def mkhash(self, input: str) -> str:
        """Given a string, calculate its hash.
        """
        m = hashlib.sha256()
        m.update(input.encode("utf-8"))
        return m.hexdigest()

    def hash_files(self, files: List[str]):
        """Given a list of files relative to the spec.yaml file,
        return a hash that includes their contents and the contents of the specs.
        """
        texts = [self.hash_conf()]
        for filename in files:
            path = PosixPath(self.path, filename)
            texts.append(path.read_text())
        return self.mkhash("\n".join(texts))

    @classmethod
    def resolve_source_path(cls, source: Dict, path: str) -> str:
        """Given the `source` part of a configuration, find the directory it refers to.
        """
        if source["type"] == "derex-relative":
            return os.path.join(os.path.dirname(path), source["path"])
        else:  # The JSON schema validation should guarantee we never get here
            raise ConfigurationError(
                f'Unknown type: {source["type"]}'
            )  # pragma: no cover

    @classmethod
    def resolve_base_image(cls, source: Dict, path: str) -> str:
        """Makes sure the base image is available and returns its name.
        """
        if not isinstance(source, str):
            builder = create_builder(cls.resolve_source_path(source, path))
            builder.resolve()
            return builder.dest
        else:  # The source is a string, so it should be available in the docker hub
            return source  # We might pull the image here

    def push_to_docker(self):
        """Push the result of this build to the local docker daemon.
        Build the image if necessary.
        """
        self.resolve()
        self.buildah("push", self.dest, f"docker-daemon:{self.dest}")


def create_builder(path: str) -> BaseBuilder:
    """Given a path to a builder configuration, it instantiates the relevant builder.
    """
    conf = load_conf((path))
    return resolve(conf["builder"]["class"])(path)


def load_conf(path: str) -> Dict:
    return yaml.load(
        open(os.path.join(path, "spec.yml")), Loader=yaml.FullLoader  # type: ignore
    )


class ConfigurationError(Exception):
    pass
