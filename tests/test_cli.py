#!/usr/bin/env python
# -*- coding: utf-8 -*-
from click.testing import CliRunner
from derex.builder import cli
from pytest_mock import MockFixture

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


def test_command_validate():
    return_codes = {
        0: ["buildah_base", "buildah_dependent"],
        1: ["buildah_invalid", "buildah_invalid_2"],
    }
    runner = CliRunner()
    for return_code, confs in return_codes.items():
        for conf in confs:
            result = runner.invoke(
                cli.main, ["validate", get_test_path(f"fixtures/{conf}")]
            )
            assert result.exit_code == return_code
