import click

path = click.argument("path", type=click.Path(exists=True))
