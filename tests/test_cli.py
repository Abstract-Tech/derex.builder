#!/usr/bin/env python
# -*- coding: utf-8 -*-
from click.testing import CliRunner
from derex.builder import cli
from pytest_mock import MockFixture  # type: ignore

from .utils import get_test_path


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
    result = runner.invoke(
        cli.main, ["resolve", get_test_path("fixtures/buildah_base/")]
    )
    assert result.exit_code == 0
    assert resolve.call_count == 1
