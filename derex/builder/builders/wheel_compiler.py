from derex.builder.builders.base import BaseBuilder, create_builder


class BuildahWheelCompiler(BaseBuilder):
    """Uses a builder image to compile a set of python wheels,
    and creates a new image by installing them in the base image.
    """

    json_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["builder", "source", "scripts", "dest"],
        "additionalProperties": False,
        "properties": {
            "builder": {"type": "object", "properties": {"class": {"type": "string"}}},
            "scripts": {"type": "array", "items": {"type": "string"}},
            "sources": {
                "type": "object",
                "required": ["builder", "base"],
                "oneOf": [
                    {"type": "string"},
                    {
                        "type": "object",
                        "required": ["type", "path"],
                        "additionalProperties": False,
                        "properties": {
                            "type": {"type": "string", "enum": ["derex-relative"]},
                            "path": {"type": "string"},
                        },
                    },
                ],
            },
            "dest": {"type": "string"},
        },
    }

    def build(self):
        pass

    def docker_image(self):
        pass

    def hash(self):
        pass

    def resolve(self):
        pass
