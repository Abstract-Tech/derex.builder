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

buildah_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["builder", "source", "scripts", "dest"],
    "additionalProperties": False,
    "properties": {
        "builder": {"type": "object", "properties": {"class": {"type": "string"}}},
        "scripts": {"type": "array", "items": {"type": "string"}},
        "source": pointer,
        "dest": {"type": "string"},
    },
}

wheel_compiler_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["builder", "sources", "dest", "requirements"],
    "additionalProperties": False,
    "properties": {
        "builder": {"type": "object", "properties": {"class": {"type": "string"}}},
        "requirements": {"type": "array", "items": pointer},
        "sources": {
            "type": "object",
            "required": ["builder", "base"],
            "properties": {"builder": pointer, "base": pointer},
        },
        "dest": {"type": "string"},
    },
}
