"""Base class and utility methods for yaml-based image definitions.
"""
import hashlib
import json
import os
from abc import ABC, abstractmethod
from typing import Dict

import yaml
from derex.builder import logger
from jsonschema import validate
from zope.dottedname.resolve import resolve


class BaseBuilder(ABC):
    """A builder takes a configuration directory and executes it to build a docker image.
    """

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

    @abstractmethod
    def resolve(self):
        """Makes sure that the image represented by this builder is locally available.
        """

    def docker_tag(self) -> str:
        """Returns a string usable as docker tag, derived from the hash.
        """
        return self.hash()[:10]

    @abstractmethod
    def docker_image(self) -> str:
        """Returns a string usable as docker image, derived from the configuration and the tag.
        """

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
            return builder.docker_image()
        else:  # The source is a string, so it should be available in the docker hub
            return source  # We might pull the image here


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
