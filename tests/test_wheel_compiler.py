#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Wheel compiler"""


from .utils import get_builder_path
from derex.builder.builders.base import create_builder
from derex.builder.builders.buildah import BuildahBuilder
from jsonschema.exceptions import ValidationError
from pathlib import PosixPath
from pytest_mock import MockFixture

import docker
import os
import pytest


@pytest.mark.slowtest
@pytest.mark.buildah
def test_wheel_compiler():
    rapidjson = create_builder(get_builder_path("rapidjson"))
    rapidjson.resolve()
    rapidjson.push_to_docker()
    client = docker.from_env()
    res = client.containers.run(
        rapidjson.dest,
        "python -c 'import rapidjson; print(rapidjson.dumps([\"foobar\"]))'",
    )
    assert res == b'["foobar"]\n'
