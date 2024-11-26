from pyprotostuben.codegen.mypy.plugin import MypyStubProtocPlugin
from tests.integration.cases.case import DirCaseProvider

mypy_case = DirCaseProvider(
    __file__,
    MypyStubProtocPlugin(),
    parameter="no-parallel",
    expected_gen_source="expected_gen",
)
mypy_case_with_descriptors = DirCaseProvider(
    __file__,
    MypyStubProtocPlugin(),
    parameter="no-parallel,include-descriptors",
    expected_gen_source="expected_gen_descriptors",
)
