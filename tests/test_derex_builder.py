#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `derex.builder` package."""

import os
from pathlib import PosixPath

import pkg_resources

import docker  # type: ignore
import pytest  # type: ignore
from click.testing import CliRunner
from derex.builder import cli
from derex.builder.builders.buildah import BuildahBuilder


def get_test_path(resource_path: str) -> str:
    """Returns an absolute path to a file in the tests folder.

    :param resource_path:str: A path relative to the tests/ directory

    :raises: FileNotFoundError if the given `resource_path` does not point to an existing file.
    """
    if pkg_resources.resource_isdir(__name__, resource_path):
        # There's no way to ask the path of a directory AFAICT
        filename = pkg_resources.resource_listdir(__name__, resource_path)[0]
        path = pkg_resources.resource_filename(__name__, f"{resource_path}/{filename}")
        return os.path.dirname(path)
    return pkg_resources.resource_filename(__name__, resource_path)


def test_command_line_interface():
    """Test the CLI."""
    runner = CliRunner()
    result = runner.invoke(cli.main)
    assert result.exit_code == 0
    assert "derex.builder.cli.main" in result.output
    help_result = runner.invoke(cli.main, ["--help"])
    assert help_result.exit_code == 0
    assert "--help  Show this message and exit." in help_result.output


def test_buildah_builder(buildah_base: BuildahBuilder):
    buildah_base.run()

    # Check the generated docker image
    client = docker.from_env()
    response = client.containers.run(
        "derex/hello_world:latest", "cat /hello.txt", remove=True
    )
    assert response == b"Hello world\n"
    client.images.remove("derex/hello_world:latest")


def test_hash_conf(buildah_base: BuildahBuilder):
    initial = buildah_base.hash_conf()
    buildah_base.conf["foo"] = "bar"
    assert buildah_base.hash_conf() != initial


def test_hash(buildah_base: BuildahBuilder, tmp_path: PosixPath):
    tmp_file = tmp_path / "script.sh"
    tmp_file.write_text("foo")
    buildah_base.conf["scripts"] = [tmp_file.as_posix()]
    initial = buildah_base.hash()
    tmp_file.write_text("bar")
    assert buildah_base.hash() != initial


@pytest.fixture
def buildah_base() -> BuildahBuilder:
    buildah_base_spec = get_test_path("fixtures/buildah_base/")
    return BuildahBuilder(buildah_base_spec)
