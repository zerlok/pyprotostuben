from pyprotostuben.codegen.mypy.plugin import MypyStubProtocPlugin

from tests.integration.case import SimpleCaseProvider

mypy_case = SimpleCaseProvider(
    __file__,
    MypyStubProtocPlugin(),
    expected_gen_paths=["greeting_pb2.pyi", "greeting_pb2_grpc.pyi"],
)
