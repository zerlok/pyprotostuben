import inspect
import typing as t
from dataclasses import dataclass
from pathlib import Path

import click

from pyprotostuben.codegen.servicify.entrypoint import inspect_source_dir
from pyprotostuben.codegen.servicify.generator.fastapi import FastAPIServicifyCodeGenerator
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
    context.obj = CLIContext(
        working_dir=working_dir,
    )


ARG_SOURCE = click.argument(
    "src",
    type=click.Path(exists=True, readable=True, resolve_path=True, path_type=Path),
)

OPT_OUTPUT = click.option(
    "-o",
    "--output",
    type=click.Path(writable=True, resolve_path=True, path_type=Path),
    default=None,
)

OPT_IGNORE_MODULE_ON_IMPORT_ERROR = click.option(
    "--ignore-module-on-import-error",
    type=bool,
    is_flag=True,
    default=False,
)


GenKind = t.Literal["brokrpc"]


@cli.command()
@pass_cli_context
@ARG_SOURCE
@click.argument(
    "kind",
    type=click.Choice(t.get_args(GenKind)),
)
@OPT_OUTPUT
@click.option(
    "-p",
    "--package",
    type=str,
    default=None,
)
@OPT_IGNORE_MODULE_ON_IMPORT_ERROR
@click.option(
    "--dry-run",
    type=bool,
    is_flag=True,
    default=False,
)
def gen(
    context: CLIContext,
    src: Path,
    kind: GenKind,
    output: t.Optional[Path],
    package: t.Optional[str],
    dry_run: bool,
    ignore_module_on_import_error: bool,
) -> None:
    """Generate code for specified python package."""

    gen_context = GeneratorContext(
        entrypoints=list(inspect_source_dir(src, ignore_module_on_import_error=ignore_module_on_import_error)),
        source=src,
        output=src if output is None else output if output.is_absolute() else src.joinpath(output),
        package=package,
    )

    # gen = BrokRPCServicifyCodeGenerator()
    gen = FastAPIServicifyCodeGenerator()
    for file in gen.generate(gen_context):
        if dry_run:
            continue

        file.path.parent.mkdir(parents=True, exist_ok=True)
        with file.path.open("w") as fd:
            fd.write(file.content)


@cli.command()
@ARG_SOURCE
@OPT_IGNORE_MODULE_ON_IMPORT_ERROR
def show(
    src: Path,
    ignore_module_on_import_error: bool,
) -> None:
    """Show info about the package"""

    for entrypoint in inspect_source_dir(src, ignore_module_on_import_error=ignore_module_on_import_error):
        if entrypoint.methods:
            type_ = entrypoint.type_
            click.echo(
                f"* {entrypoint.name} ({type_.module.qualname}:{'.'.join(type_.ns)}) "
                f"{' ' if entrypoint.doc else ''}{entrypoint.doc or ''}"
            )

            for method in entrypoint.methods:
                signature = inspect.Signature(parameters=method.params, return_annotation=method.returns)
                click.echo(f"   * {method.name}{signature}: {method.doc or ''}")

            click.echo("")


if __name__ == "__main__":
    cli()
