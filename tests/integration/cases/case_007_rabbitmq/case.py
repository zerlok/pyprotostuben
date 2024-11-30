from pyprotostuben.codegen.brokrpc.plugin import BrokRPCProtocPlugin
from tests.integration.cases.case import DirCaseProvider

brokrpc_case = DirCaseProvider(
    filename=__file__,
    plugin=BrokRPCProtocPlugin(),
    deps=["buf.build/zerlok/brokrpc:v0.2.3"],
    parameter="no-parallel,grpc-skip-servicer,grpc-skip-stub",
    expected_gen_paths=["foo_brokrpc.py"],
)
