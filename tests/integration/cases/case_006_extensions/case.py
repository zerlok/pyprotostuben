from pyprotostuben.codegen.brokrpc.plugin import BrokRPCProtocPlugin
from pyprotostuben.codegen.mypy.plugin import MypyStubProtocPlugin
from tests.integration.cases.case import DirCaseProvider

mypy_case = DirCaseProvider(
    filename=__file__,
    plugin=MypyStubProtocPlugin(),
    deps=["buf.build/zerlok/brokrpc:v0.2.1"],
    parameter="no-parallel",
    expected_gen_paths=["foo_pb2.pyi", "bar_pb2_grpc.pyi"],
)

brokrpc_case = DirCaseProvider(
    filename=__file__,
    plugin=BrokRPCProtocPlugin(),
    deps=["buf.build/zerlok/brokrpc:v0.2.1"],
    parameter="no-parallel",
    expected_gen_paths=["bar_brokrpc.py"],
)
