from pyprotostuben.codegen.echo import RequestEchoCodeGenerator
from pyprotostuben.codegen.mypy.generator import MypyStubCodeGenerator
from pyprotostuben.codegen.run import run_codegen
from pyprotostuben.logging import Logger


def gen_mypy_stub() -> None:
    Logger.configure()
    run_codegen(MypyStubCodeGenerator())


def echo() -> None:
    Logger.configure()
    run_codegen(RequestEchoCodeGenerator())
