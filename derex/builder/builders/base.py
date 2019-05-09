"""Base class and utility methods for yaml-based image definitions.
"""
import hashlib
import json
import os
from abc import ABC, abstractmethod

import yaml
from zope.dottedname.resolve import resolve


class BaseBuilder(ABC):
    """A builder takes a configuration directory and executes it to build a docker image.
    """

    def __init__(self, path: str):
        """
        :param file_path: A path to a directory containing a spec yaml file and other support files.
        """
        self.path = path
        self.conf = load_conf(path)

    @abstractmethod
    def run(self):
        """Run the builder based on its configuration.
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


def create_builder(path: str) -> BaseBuilder:
    """Given a path to a builder configuration, it instantiates the relevant builder.
    """
    conf = load_conf((path))
    return resolve(conf["builder"]["class"])(path)


def load_conf(path: str) -> dict:
    return yaml.load(
        open(os.path.join(path, "spec.yml")), Loader=yaml.FullLoader  # type: ignore
    )
