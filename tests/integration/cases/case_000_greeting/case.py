from pyprotostuben.codegen.brokrpc.plugin import BrokRPCProtocPlugin
from pyprotostuben.codegen.mypy.plugin import MypyStubProtocPlugin
from tests.integration.cases.case import DirCaseProvider

mypy_stub_paths = ["greeting_pb2.pyi", "greeting_pb2_grpc.pyi"]
mypy_case = DirCaseProvider(__file__, MypyStubProtocPlugin(), "no-parallel", expected_gen_paths=mypy_stub_paths)
mypy_case_multiprocessing = DirCaseProvider(__file__, MypyStubProtocPlugin(), expected_gen_paths=mypy_stub_paths)

brokrpc_case = DirCaseProvider(
    __file__, BrokRPCProtocPlugin(), "no-parallel", expected_gen_paths=["greeting_brokrpc.py"]
)
