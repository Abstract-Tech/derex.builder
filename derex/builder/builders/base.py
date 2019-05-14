"""Base class and utility methods for yaml-based image definitions.
"""
from abc import ABC
from abc import abstractmethod
from derex.builder import logger
from jsonschema import validate
from pathlib import PosixPath
from typing import Dict
from typing import List
from typing import Tuple
from typing import Union
from urllib.error import HTTPError
from zope.dottedname.resolve import resolve

import hashlib
import json
import os
import subprocess
import urllib.request
import yaml


CACHES = {
    "/var/cache/pip-alpine": "PIP_CACHE",
    "/var/cache/apk": "APK_CACHE",
    "/var/cache/npm": "NPM_CACHE",
}


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
        if self.dest in self.list_buildah_images():
            logger.debug(f"{self.dest} found localy")
            return True
        logger.debug(f"{self.dest} could not be found localy")
        return False

    def list_buildah_images(self) -> List[str]:
        """Returns a list of all images locally available to buildah
        """
        # Get a list of all images
        images = json.loads(self.buildah("images", "--json", print_output=False))
        # Collect all their tags
        tags = sum((el["names"] for el in images if el["names"]), [])

        # Remove the first path component from image names
        return sorted([tag.split("/", 1)[1] for tag in tags])

    def buildah(self, *args: str, print_output=True) -> str:
        """Utility function to invoke buildah
        """
        cmd = ["buildah"]
        if os.getuid() != 0:
            cmd = ["sudo"] + cmd
        res: List[str] = []
        for line in self.run(cmd + list(args)):
            if print_output:
                logger.info(line.rstrip())
            res += [line]
        return "".join(res).rstrip()

    def buildah_run(
        self, container: str, args: List[str], extra_args: Union[List[str], Tuple] = ()
    ):
        """Runs a command inside the container after adding cache directories.
        """
        caches = self.ensure_caches()
        volumes: List[str] = []
        for source, dest in caches.items():
            volumes += ["-v", f"{source}:{dest}"]
        return self.buildah(
            *(["run"] + list(extra_args) + volumes + [container] + list(args))
        )

    def ensure_caches(self):
        """Make sure the cache directories exist.
        """
        caches = {}
        for dest, varname in CACHES.items():
            source = os.environ.get(varname)
            if source:
                if not os.path.isdir(source):
                    logger.warning(f"Creating cache directory {source}")
                    try:
                        os.mkdir(source)
                        caches[source] = dest
                    except PermissionError:  # Please (xkcd #149)
                        logger.warn(
                            f"If you don't want to use this directory, specify a different one in the {varname} environment variable, or set the variable to an empty string to disable this feature"
                        )
                        try:
                            subprocess.check_output(("sudo", "mkdir", source))
                            caches[source] = dest
                        except subprocess.CalledProcessError:
                            logger.error(
                                f"Error creating {source}. Continuing without it."
                            )
                else:  # path exists
                    caches[source] = dest
        return caches

    def run(self, cmd):
        logger.info(f"executing {' '.join(cmd)}\n")
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        while True:
            line = process.stdout.readline().decode("utf-8")
            if not line:
                break
            yield line

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
    def resolve_base_image(cls, source: Union[str, Dict], path: str) -> str:
        """Makes sure the base image is available and returns its name.
        """
        if not isinstance(source, str):
            return cls.get_source_target(source, path, resolve=True)
        else:  # The source is a string, so it should be available in the docker hub
            return source  # We might pull the image here

    @classmethod
    def get_source_target(
        cls, source: Union[str, Dict], path: str, resolve=False
    ) -> str:
        """Given a source specification and the path returns the target
        of the pointed builder.
        # TODO this should be a function, not an abstract method?
        """
        if not isinstance(source, str):
            builder = create_builder(cls.resolve_source_path(source, path))
            if resolve == True:
                builder.resolve()
            return builder.dest
        else:
            return source

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
