from pyprotostuben.codegen.mypy.plugin import MypyStubProtocPlugin

from tests.integration.case import SimpleCaseProvider

mypy_case = SimpleCaseProvider(__file__, MypyStubProtocPlugin())
