"""Base class for yaml-based image definitions
"""
import os
from abc import ABC, abstractmethod

import yaml


class BaseBuilder(ABC):
    """A builder takes a configuration directory and executes it to build a docker image.
    """

    def __init__(self, path: str):
        """
        :param file_path: A path to a directory containing a spec yaml file and other support files.
        """
        self.path = path
        self.conf = yaml.load(
            open(os.path.join(path, "spec.yml")), Loader=yaml.FullLoader
        )

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
