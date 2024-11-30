
from pyprotostuben.codegen.brokrpc.plugin import BrokRPCProtocPlugin
from pyprotostuben.codegen.mypy.plugin import MypyStubProtocPlugin
from tests.integration.cases.case import DirCaseProvider, skip_if_module_not_found

mypy_stub_paths = ["greeting_pb2.pyi", "greeting_pb2_grpc.pyi"]

mypy_case = DirCaseProvider(
    filename=__file__,
    plugin=MypyStubProtocPlugin(),
    parameter="no-parallel",
    expected_gen_paths=mypy_stub_paths,
)
mypy_case_multiprocessing = DirCaseProvider(
    filename=__file__,
    plugin=MypyStubProtocPlugin(),
    expected_gen_paths=mypy_stub_paths,
)

brokrpc_case = DirCaseProvider(
    filename=__file__,
    plugin=BrokRPCProtocPlugin(),
    marks=[skip_if_module_not_found("brokrpc")],
    parameter="no-parallel",
    expected_gen_paths=["greeting_brokrpc.py"],
)
