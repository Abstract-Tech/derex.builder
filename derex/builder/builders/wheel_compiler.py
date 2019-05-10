from derex.builder.builders.base import BaseBuilder, create_builder

from .schema import wheel_compiler_schema


class BuildahWheelCompiler(BaseBuilder):
    """Uses a builder image to compile a set of python wheels,
    and creates a new image by installing them in the base image.
    """

    json_schema = wheel_compiler_schema

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sources = self.conf["sources"]
        self.requirements = self.conf["requirements"]
        self.dest = f'{self.conf["dest"]}:{self.docker_tag()}'

    def build(self):
        pass

    def docker_image(self):
        pass

    def hash(self):
        return self.hash_files(self.requirements)

    def resolve(self):
        pass
