# -*- coding: utf-8 -*-

"""Console script for derex.builder."""
import sys

import click
from derex.builder.builders.base import create_builder


@click.group()
def main(args=None):
    """Build docker images based on yaml config files and shell scripts."""


@click.argument("path")
@main.command()
def resolve(path: str):
    """Build a docker image based on a directory containing a spec.yml file.
    """

    click.echo(f"Building {path}")
    create_builder(path).resolve()
