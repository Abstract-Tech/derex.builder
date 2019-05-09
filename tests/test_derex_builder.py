#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `derex.builder` package."""

import os

import docker  # type: ignore
import pkg_resources
import pytest  # type: ignore
from click.testing import CliRunner

from derex.builder import cli


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


def test_buildah_builder():
    from derex.builder.builders.buildah import BuildahBuilder

    test_builder_spec = get_test_path("fixtures/buildah_base/")
    test_builder = BuildahBuilder(test_builder_spec)
    test_builder.run()

    # Check the generated docker image
    client = docker.from_env()
    response = client.containers.run(
        "derex/hello_world:latest", "cat /hello.txt", remove=True
    )
    assert response == b"Hello world\n"
    client.images.remove("derex/hello_world:latest")
