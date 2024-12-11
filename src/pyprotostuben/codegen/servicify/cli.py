import sys
from pathlib import Path

import click

from pyprotostuben.codegen.servicify.entrypoint import inspect_package
from pyprotostuben.codegen.servicify.generator import GeneratorContext, ServicifyCodeGenerator


@click.group()
def cli() -> None:
    sys.path.append(str(Path.cwd()))


ARG_SRC = click.argument(
    "src",
    type=click.Path(exists=True, readable=True, resolve_path=True, path_type=Path),
)

ARG_OUT = click.option(
    "-o",
    "--output",
    type=click.Path(writable=True, resolve_path=True, path_type=Path),
    default=Path.cwd(),
)


@cli.command()
@ARG_SRC
@click.argument(
    "kind",
    type=click.Choice(["fastapi", "grpcio"]),
)
@ARG_OUT
def gen(src: Path, kind: str, output: Path) -> None:
    """Generate code for specified python package."""
    gen = ServicifyCodeGenerator()
    for file in gen.generate(GeneratorContext(entrypoints=list(inspect_package(src)), output=output)):
        file.path.parent.mkdir(parents=True, exist_ok=True)
        with file.path.open("w") as fd:
            fd.write(file.content)


@cli.command()
@ARG_SRC
def show(src: Path) -> None:
    """Show info about the package"""

    for entrypoint in inspect_package(src):
        click.echo(f"- {entrypoint.module.qualname} {entrypoint.ns}")
        for method in entrypoint.methods:
            click.echo(f"   - {method.name} {method.signature}")

        click.echo("")
