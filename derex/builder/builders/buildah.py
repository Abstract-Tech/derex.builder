"""Classes to build docker images using Buildah.
"""
from derex.builder.builders.base import BaseBuilder
from typing import Union
import subprocess
import json
import os
import logging

logger = logging.getLogger(__name__)


class ImageFound:
    pass


class BuildahBuilder(BaseBuilder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scripts = self.conf['scripts']
        self.source = self.conf['source']
        self.dest = self.conf['dest'] + ':latest'

    def validate(self):
        """Check that all resources referenced from the yaml file actually exist.
        """

    def run(self) -> Union[ImageFound, None]:
        images = json.loads(self.buildah('images', '--json'))
        if f'localhost/{self.dest}' in sum((el['names'] for el in images if el['names']), []):
            return ImageFound
        container = self.buildah('from', self.source)
        buildah = lambda cmd, *args: self.buildah(cmd, container, *args)
        script_dir = '/opt/derex/bin'
        buildah('run', 'mkdir', '-p', script_dir)
        for script in self.scripts:
            src = os.path.join(self.path, script)
            dest = os.path.join(script_dir, script)
            logger.info(buildah('copy', src, dest))
            buildah('run', 'chmod', 'a+x', dest)
            buildah('run', dest)
        self.buildah('commit', '--rm', container, self.dest)
        self.buildah('push', self.dest, f'docker-daemon:{self.dest}')
        self.buildah('rmi', self.dest)

    def buildah(self, *args):
        """Utility function to invoke buildah
        """
        return subprocess.check_output(['sudo', 'buildah'] + list(args)).decode('utf-8').strip()


