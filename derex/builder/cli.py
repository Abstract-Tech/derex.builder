# -*- coding: utf-8 -*-

"""Console script for derex.builder."""
import sys

import click
from derex.builder.builders.base import create_builder
from jsonschema.exceptions import ValidationError

from . import arguments


@click.group()
def main(args=None):
    """Build docker images based on yaml config files and shell scripts."""


@arguments.path
@main.command()
def resolve(path: str):
    """Build a docker image based on a directory containing a spec.yml file.
    """

    click.echo(f"Building {path}")
    create_builder(path).resolve()


@arguments.path
@main.command()
def validate(path: str):
    """Validate spec.yml yaml configuration in the given directory.
    """
    click.echo(f"Validating {path}/spec.yml")
    try:
        create_builder(path).validate()
    except ValidationError as err:
        click.echo(err)
        return -1
    click.echo(f"All good")
