from derex.builder.builders.base import BaseBuilder, create_builder

from .schema import wheel_compiler_schema


class BuildahWheelCompiler(BaseBuilder):
    """Uses a builder image to compile a set of python wheels,
    and creates a new image by installing them in the base image.
    """

    json_schema = wheel_compiler_schema

    def build(self):
        pass

    def docker_image(self):
        pass

    def hash(self):
        pass

    def resolve(self):
        pass
