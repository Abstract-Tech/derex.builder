#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Wheel compiler"""


import os
from pathlib import PosixPath

import docker
import pytest
from derex.builder.builders.base import create_builder
from derex.builder.builders.buildah import BuildahBuilder
from jsonschema.exceptions import ValidationError
from pytest_mock import MockFixture

from .utils import get_builder_path


def test_wheel_compiler():
    rapidjson = create_builder(get_builder_path("rapidjson"))
    rapidjson.resolve()
    client = docker.from_env()
    res = client.containers.run(
        rapidjson.dest,
        "python -c 'import rapidjson; print(rapidjson.dumps([\"foobar\"]))'",
    )
    assert res == b'["foobar"]\n'
