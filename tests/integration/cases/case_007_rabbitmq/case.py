from pyprotostuben.codegen.brokrpc.plugin import BrokRPCProtocPlugin
from tests.integration.cases.case import DirCaseProvider, skip_if_module_not_found

brokrpc_case = DirCaseProvider(
    filename=__file__,
    plugin=BrokRPCProtocPlugin(),
    marks=[skip_if_module_not_found("brokrpc")],
    deps=["buf.build/zerlok/brokrpc:v0.2.3"],
    parameter="no-parallel,grpc-skip-servicer,grpc-skip-stub",
    expected_gen_paths=["foo_brokrpc.py"],
)
