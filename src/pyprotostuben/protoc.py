from pyprotostuben.codegen.echo import RequestEchoProtocPlugin
from pyprotostuben.codegen.mypy.plugin import MypyStubProtocPlugin
from pyprotostuben.codegen.run import run_codegen
from pyprotostuben.logging import Logger


def gen_mypy_stub() -> None:
    Logger.configure()
    run_codegen(MypyStubProtocPlugin())


def echo() -> None:
    Logger.configure()
    run_codegen(RequestEchoProtocPlugin())
