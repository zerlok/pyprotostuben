import typing as t
from dataclasses import dataclass
from pathlib import Path

import click

from pyprotostuben.codegen.servicify.entrypoint import inspect_source_dir
from pyprotostuben.codegen.servicify.generator import BrokRPCServicifyCodeGenerator
from pyprotostuben.codegen.servicify.model import GeneratorContext


@dataclass(frozen=True, kw_only=True)
class CLIContext:
    working_dir: Path


pass_cli_context = click.make_pass_decorator(CLIContext)


@click.group()
@click.pass_context
@click.option(
    "-C",
    "working_dir",
    type=click.Path(exists=True, readable=True, resolve_path=True, path_type=Path),
    default=Path.cwd(),
)
def cli(context: click.Context, working_dir: Path) -> None:
    # sys.path.append(str(working_dir.cwd()))

    context.obj = CLIContext(
        working_dir=working_dir,
    )


ARG_SRC = click.argument(
    "src",
    type=click.Path(exists=True, readable=True, resolve_path=True, path_type=Path),
)

OPT_OUT = click.option(
    "-o",
    "--output",
    type=click.Path(writable=True, resolve_path=True, path_type=Path),
    default=None,
)


@cli.command()
@pass_cli_context
@ARG_SRC
@click.argument(
    "kind",
    type=click.Choice(["brokrpc"]),
)
@OPT_OUT
@click.option(
    "-p",
    "--package",
    type=str,
    default=None,
)
def gen(context: CLIContext, src: Path, kind: str, output: Path, package: t.Optional[str]) -> None:
    """Generate code for specified python package."""

    gen_context = GeneratorContext(
        entrypoints=list(inspect_source_dir(src)),
        output=output or src,
        package=package,
    )

    gen = BrokRPCServicifyCodeGenerator()
    for file in gen.generate(gen_context):
        file.path.parent.mkdir(parents=True, exist_ok=True)
        with file.path.open("w") as fd:
            fd.write(file.content)


@cli.command()
@ARG_SRC
def show(src: Path) -> None:
    """Show info about the package"""

    for entrypoint in inspect_source_dir(src):
        if entrypoint.groups:
            click.echo(f"+ {entrypoint.module.qualname}")

        for gi, group in enumerate(entrypoint.groups, start=1):
            click.echo(f"{'|' if gi < len(entrypoint.groups) else '`'}---+ {group.name}")
            for mi, method in enumerate(group.methods, start=1):
                click.echo(f"    {'|' if mi < len(group.methods) else '`'}--- {method.name}{method.signature}")
                if method.doc:
                    click.echo(f"          {method.doc}")

        if entrypoint.groups:
            click.echo("")


if __name__ == "__main__":
    cli()
