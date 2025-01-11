import ast
import typing as t

import pytest
from _pytest.fixtures import SubRequest

from pyprotostuben.python.info import ModuleInfo, PackageInfo


def parse_ast(s: str) -> ast.AST:
    # code may be indented, so normalize it (e.g. the following code strings will be parsed as equivalent AST).
    # my_code1 = """
    #            class Foo:
    #                bar: Bar
    #            """
    # my_code2 = """class Foo:
    #     bar: Bar"""
    # my_code3 = """class Foo:\n    bar: Bar"""

    lines = list[str]()
    offset: t.Optional[int] = None

    for line in s.split("\n"):
        if offset is None:
            idx, _ = next(((i, c) for i, c in enumerate(line) if not c.isspace()), (None, None))
            if idx is None:
                continue

            offset = idx

        lines.append(line[offset:])

    return ast.parse("\n".join(lines))


@pytest.fixture
def stub_package_info(request: SubRequest) -> PackageInfo:
    mod = ModuleInfo.from_module(request.module)
    return PackageInfo(mod.package, mod.name)
