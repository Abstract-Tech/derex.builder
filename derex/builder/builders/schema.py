pointer = {
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
    ]
}
BASE_PROPERTIES = {
    "builder": {"type": "object", "properties": {"class": {"type": "string"}}},
    "dest": {"type": "string"},
    "build_env": {"type": "array", "items": {"type": "string"}},
    "config": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "entrypoint": {"type": "string"},
            "workingdir": {"type": "string"},
            "cmd": {"type": "string"},
            "env": {"type": "object", "patternProperties": {".*": {"type": "string"}}},
        },
    },
}
BASE_KEYS = ["builder", "dest"]

buildah_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["source", "scripts"] + BASE_KEYS,
    "additionalProperties": False,
    "properties": dict(
        BASE_PROPERTIES,
        scripts={"type": "array", "items": {"type": "string"}},
        source=pointer,
        copy={"type": "object"},
    ),
}

wheel_compiler_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["sources", "requirements"] + BASE_KEYS,
    "additionalProperties": False,
    "properties": dict(
        BASE_PROPERTIES,
        requirements={"type": "array", "items": pointer},
        sources={
            "type": "object",
            "required": ["builder", "base"],
            "properties": {"builder": pointer, "base": pointer},
        },
    ),
}
