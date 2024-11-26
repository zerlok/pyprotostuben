from pyprotostuben.codegen.run import run_codegen
from pyprotostuben.logging import Logger


def gen_mypy_stub() -> None:
    from pyprotostuben.codegen.mypy.plugin import MypyStubProtocPlugin

    Logger.configure()
    run_codegen(MypyStubProtocPlugin())


def gen_brokrpc() -> None:
    # TODO: find a better way to load extension modules and parse custom options in protobuf files
    # https://github.com/protocolbuffers/protobuf/issues/12049#issuecomment-1444187517
    # from brokrpc.spec.v1 import amqp_pb2

    # TODO: consider extensions usage during runtime, not codegen

    from pyprotostuben.codegen.brokrpc.plugin import BrokRPCProtocPlugin

    Logger.configure()
    run_codegen(BrokRPCProtocPlugin())


def echo() -> None:
    from pyprotostuben.codegen.echo import RequestEchoProtocPlugin

    Logger.configure()
    run_codegen(RequestEchoProtocPlugin())
