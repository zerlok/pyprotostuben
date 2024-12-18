from __future__ import annotations

import importlib
import inspect
import sys
import typing as t
from collections import deque
from pathlib import Path
from types import ModuleType

from pyprotostuben.codegen.servicify.model import EntrypointInfo, GroupInfo, MethodInfo
from pyprotostuben.python.info import ModuleInfo, TypeInfo

P = t.ParamSpec("P")
T = t.TypeVar("T")

__ENTRYPOINT_MARK = f"""__{__name__.replace(".", "_")}_entrypoint__"""


def entrypoint(obj: type[T]) -> type[T]:
    setattr(obj, __ENTRYPOINT_MARK, True)
    return obj


def is_entrypoint(obj: object) -> bool:
    return hasattr(obj, __ENTRYPOINT_MARK)


def inspect_source_dir(
    src: Path,
    *,
    ignore_module_on_import_error: bool = False,
) -> t.Iterable[EntrypointInfo]:
    sys.path.append(str(src))
    try:
        stack: t.Deque[Path] = deque([src])

        while stack:
            path = stack.pop()

            if path.is_file() and path.suffix == ".py" and not path.stem.startswith("_"):
                module_path = path.relative_to(src)
                module_qualname = ".".join(module_path.parts[:-1]) + f".{module_path.stem}"

                try:
                    module = importlib.import_module(module_qualname)

                except ImportError:
                    if not ignore_module_on_import_error:
                        raise

                else:
                    yield inspect_module(module)

            elif path.is_dir() and not path.stem.startswith("_"):
                for subitem in path.iterdir():
                    stack.append(subitem)

    finally:
        sys.path.remove(str(src))


def inspect_module(module: ModuleType) -> EntrypointInfo:
    module_info = ModuleInfo.from_module(module)

    groups: t.List[GroupInfo] = []

    for name, obj in inspect.getmembers(module):
        if not is_entrypoint(obj):
            continue

        groups.append(
            GroupInfo(
                info=TypeInfo(module_info, ns=[name]),
                methods=[
                    MethodInfo(
                        name=name,
                        signature=inspect.signature(member),
                        doc=inspect.getdoc(member),
                    )
                    for name, member in inspect.getmembers(obj)
                    if not name.startswith("_") and callable(member)
                ],
            )
        )

    return EntrypointInfo(
        module=module_info,
        groups=groups,
    )
