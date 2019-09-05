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


class ImageFound:
    pass


class BuildahBuilder(BaseBuilder):
    json_schema = buildah_schema

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scripts = self.conf["scripts"]
        self.source = self.conf["source"]
        self.copy = self.conf.get("copy", {})
        self.config = self.conf.get("config", {})

    def hash(self) -> str:
        """Return a hash representing this builder.
        The hash is built from the yaml configuration, the content of the scripts,
        the copied files and the base config/image tag.
        """
        elements = [
            self.__class__.__name__,
            self.hash_conf(),
            self.hash_files(self.copy.keys()),
            self.get_source_target(self.source, path=self.path),
            self.hash_files(self.scripts),
        ]
        return self.mkhash("\n".join(elements))

    def build(self):
        """Builds the image specified by this builder.
        """
        logger.info(f"Building {self.dest} from {self.path}")
        base_image = self.resolve_base_image(self.source, self.path)
        container = self.buildah("from", base_image, print_output=False)

        # To support build-only variables we push them to the container config and
        # re-set them to the empty value immediately before committing the container.
        # TODO revisit if/when buildah supports `--env` in its `run` command.
        set_env_opts = []
        unset_env_opts = []
        for name in self.conf.get("build_env", []):
            value = os.environ.get(name)
            if value is not None:
                set_env_opts += ["--env", f"{name}={value}"]
                unset_env_opts += ["--env", f"{name}="]
        self.buildah("config", *set_env_opts + [container])

        buildah_run = lambda *args: self.buildah_run(container, args)
        script_dir = "/opt/derex/bin"
        buildah_run("mkdir", "-p", script_dir)

        def copy(src, dest):
            logger.info(
                self.buildah("copy", container, os.path.join(self.path, src), dest)
            )

        for src, dest in self.copy.items():
            copy(src, dest)
        for script in self.scripts:
            dest = os.path.join(script_dir, script)
            copy(script, dest)
            logger.info(f"Running {script}")
            buildah_run("chmod", "a+x", dest)
            buildah_run(dest)
        logger.info(f"Finished running scripts")
        if self.config:
            for key, value in self.config.items():
                if key == "env":
                    for varname, varval in value.items():
                        self.buildah(
                            "config", f"--env", f"{varname}={varval}", container
                        )
                else:
                    self.buildah("config", f"--{key}", value, container)

        self.buildah(
            "config", *unset_env_opts + [container]
        )  # Unset build-only variables

        self.buildah("commit", "--rm", container, self.dest)
