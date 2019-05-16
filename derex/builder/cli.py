# -*- coding: utf-8 -*-

"""Console script for derex.builder."""
from . import arguments
from . import logger
from click.exceptions import Abort
from derex.builder.builders.base import create_builder
from jsonschema.exceptions import ValidationError

import click
import click_log
import os
import sys


click_log.basic_config(logger)


@click.group()
def main(args=None):
    """Build docker images based on yaml config files and shell scripts."""


@arguments.path
@main.command()
@click_log.simple_verbosity_option(logger)
def resolve(path: str):
    """Build a docker image based on a directory containing a spec.yml file.
    """

    click.echo(f"Building {path}")
    create_builder(path).resolve()


@arguments.path
@main.command()
def image(path: str):
    """Print a docker image identifier for the given builder.
    If stdout is not a tty omit the trailing newline.
    """
    # Print a newline only when connected to a tty
    nl = os.isatty(sys.stdout.fileno())
    click.echo(create_builder(path).dest, nl=nl)


@arguments.path
@main.command()
@click_log.simple_verbosity_option(logger)
def validate(path: str):
    """Validate spec.yml yaml configuration in the given directory.
    """
    click.echo(f"Validating {path}")
    try:
        create_builder(path).validate()
    except ValidationError as err:
        logger.error(err)
        raise Abort()  # Make sure our exit status code is non-zero
    click.echo(f"All good")
