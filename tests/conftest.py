import ast
import typing as t

import pytest
from _pytest.fixtures import SubRequest

from pyprotostuben.python.info import ModuleInfo, PackageInfo


def parse_module_ast(s: str) -> ast.Module:
    """Parse a block of code. The code may be indented, parser will shift the content to the left."""

    lines = list[str]()
    offset: t.Optional[int] = None

    for line in s.split("\n"):
        if offset is None:
            idx, _ = next(((i, c) for i, c in enumerate(line) if not c.isspace()), (None, None))
            if idx is None:
                continue

            offset = idx

        lines.append(line[offset:])

    node = ast.parse("\n".join(lines))
    assert isinstance(node, ast.Module)

    return node


@pytest.fixture
def stub_package_info(request: SubRequest) -> PackageInfo:
    mod = ModuleInfo.from_module(request.module)
    return PackageInfo(mod.package, mod.name)
