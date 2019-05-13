#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""builder"""

from .utils import get_builder_path
from derex.builder.builders.buildah import BuildahBuilder
from jsonschema.exceptions import ValidationError
from pathlib import PosixPath
from pytest_mock import MockFixture

import docker
import os
import pytest


@pytest.mark.slowtest
@pytest.mark.buildah
def test_buildah_builder(buildah_base: BuildahBuilder):
    buildah_base.build()
    buildah_base.push_to_docker()

    # Check the generated docker image
    client = docker.from_env()
    response = client.containers.run(buildah_base.dest, "cat /hello.txt", remove=True)
    assert response == b"Hello world\n"
    client.images.remove(buildah_base.dest)

    images = buildah_base.list_buildah_images()
    assert f"library/{buildah_base.source}" in images


def test_hash_conf(buildah_base: BuildahBuilder):
    initial = buildah_base.hash_conf()
    buildah_base.conf["foo"] = "bar"
    assert buildah_base.hash_conf() != initial


def test_hash(buildah_base: BuildahBuilder, tmp_path: PosixPath):
    tmp_file = tmp_path / "script.sh"
    tmp_file.write_text("foo")
    buildah_base.scripts = [tmp_file.as_posix()]
    initial = buildah_base.hash()
    tmp_file.write_text("bar")
    assert buildah_base.hash() != initial


@pytest.mark.slowtest
@pytest.mark.buildah
def test_resolve(buildah_base: BuildahBuilder, mocker: MockFixture):
    list_buildah_images = mocker.patch(
        "derex.builder.builders.buildah.BuildahBuilder.list_buildah_images"
    )
    list_buildah_images.return_value = []  # When the image is not available locally...
    build = mocker.patch("derex.builder.builders.buildah.BuildahBuilder.build")
    buildah_base.resolve()
    build.assert_called_once()  # ...it will be built

    # If the image is present locally it will not be built
    list_buildah_images.return_value = [f"localhost/{buildah_base.dest}"]
    buildah_base.resolve()
    build.reset_mock()
    build.assert_not_called()


def test_create_builder(buildah_base):
    from derex.builder.builders.base import create_builder, ConfigurationError

    buildah_base_spec = get_builder_path("base")
    base = create_builder(buildah_base_spec + "/")
    assert base.hash() == buildah_base.hash()
    assert type(base) == type(buildah_base)

    buildah_invalid_spec = get_builder_path("invalid")
    with pytest.raises(ValidationError):
        invalid = create_builder(buildah_invalid_spec)


@pytest.mark.slowtest
@pytest.mark.buildah
def test_dependent_container():
    # Make sure a trailing slash doesn't spoil the party
    buildah_dependent_spec = get_builder_path("dependent") + "/"
    buildah_dependent = BuildahBuilder(buildah_dependent_spec)

    buildah_dependent.build()
    buildah_dependent.push_to_docker()
    # Check the generated docker image
    client = docker.from_env()
    response = client.containers.run(
        buildah_dependent.dest, "cat /hello_all.txt", remove=True
    )
    assert response == b"Hello all\n"
    client.images.remove(buildah_dependent.dest)


def test_sudo_only_if_necessary(buildah_base: BuildahBuilder, mocker: MockFixture):
    check_output = mocker.patch("derex.builder.builders.base.subprocess.check_output")
    getuid = mocker.patch("derex.builder.builders.buildah.os.getuid")
    getuid.return_value = 1000
    buildah_base.buildah()
    assert check_output.call_args[0][0] == ["sudo", "buildah"]
    getuid.return_value = 0
    buildah_base.buildah()
    assert check_output.call_args[0][0] == ["buildah"]


@pytest.fixture
def buildah_base() -> BuildahBuilder:
    buildah_base_spec = get_builder_path("base")
    return BuildahBuilder(buildah_base_spec)
