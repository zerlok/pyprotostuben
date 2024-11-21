from pyprotostuben.codegen.run import run_codegen
from pyprotostuben.logging import Logger


def gen_mypy_stub() -> None:
    from pyprotostuben.codegen.mypy.plugin import MypyStubProtocPlugin

    Logger.configure()
    run_codegen(MypyStubProtocPlugin())


def gen_brokrpc() -> None:
    from pyprotostuben.codegen.brokrpc.plugin import BrokRPCProtocPlugin

    Logger.configure()
    run_codegen(BrokRPCProtocPlugin())


def echo() -> None:
    from pyprotostuben.codegen.echo import RequestEchoProtocPlugin

    Logger.configure()
    run_codegen(RequestEchoProtocPlugin())
