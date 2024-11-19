from pyprotostuben.codegen.mypy.plugin import MypyStubProtocPlugin

from tests.integration.case import DirCaseProvider

mypy_case = DirCaseProvider(__file__, MypyStubProtocPlugin())
