#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""cli"""
from .utils import get_builder_path
from click.testing import CliRunner
from derex.builder import cli
from pytest_mock import MockFixture


def test_command_line_interface():
    """Test the CLI."""
    runner = CliRunner()
    result = runner.invoke(cli.main)
    assert result.exit_code == 0
    assert "Build docker images" in result.output
    help_result = runner.invoke(cli.main, ["--help"])
    assert help_result.exit_code == 0
    assert "--help  Show this message and exit." in help_result.output


def test_command_build(mocker: MockFixture):
    runner = CliRunner()
    resolve = mocker.patch("derex.builder.builders.buildah.BuildahBuilder.resolve")
    result = runner.invoke(cli.main, ["resolve", get_builder_path("base")])
    assert result.exit_code == 0
    assert resolve.call_count == 1


def test_command_validate():
    return_codes = {0: ["base", "dependent"], 1: ["invalid", "invalid_2"]}
    runner = CliRunner()
    for return_code, confs in return_codes.items():
        for conf in confs:
            result = runner.invoke(cli.main, ["validate", get_builder_path(conf)])
            assert result.exit_code == return_code


def test_command_image():
    from derex.builder.builders.buildah import BuildahBuilder

    runner = CliRunner()
    path = get_builder_path("base")
    builder = BuildahBuilder(path)
    result = runner.invoke(cli.main, ["image", path], catch_exceptions=False)
    assert result.exception is None
    assert result.output.rstrip() == builder.dest
