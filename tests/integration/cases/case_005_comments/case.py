from pyprotostuben.codegen.mypy.plugin import MypyStubProtocPlugin
from tests.integration.cases.case import DirCaseProvider

mypy_case = DirCaseProvider(
    filename=__file__,
    plugin=MypyStubProtocPlugin(),
    parameter="no-parallel",
)
