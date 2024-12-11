import importlib
import inspect
import typing as t
from collections import deque
from dataclasses import dataclass
from pathlib import Path

from pyprotostuben.python.info import ModuleInfo, TypeInfo

P = t.ParamSpec("P")
T = t.TypeVar("T")


@dataclass(frozen=True, kw_only=True)
class MethodInfo:
    name: str
    signature: inspect.Signature


@dataclass(frozen=True, kw_only=True)
class EntrypointInfo(TypeInfo):
    methods: t.Sequence[MethodInfo]


__ENTRYPOINT_MARK = f"""__{__name__.replace(".", "_")}_entrypoint__"""


def entrypoint(obj: type[T]) -> type[T]:
    setattr(obj, __ENTRYPOINT_MARK, True)
    return obj


def is_entrypoint(obj: object) -> bool:
    return hasattr(obj, __ENTRYPOINT_MARK)


def inspect_package(path: Path) -> t.Iterable[EntrypointInfo]:
    stack: t.Deque[Path] = deque([path])

    while stack:
        item = stack.pop()

        if item.is_file() and item.suffix == ".py" and not item.stem.startswith("_"):
            yield from inspect_module(item)

        elif item.is_dir() and not item.stem.startswith("_"):
            for subitem in item.iterdir():
                stack.append(subitem)


def inspect_module(path: Path) -> t.Iterable[EntrypointInfo]:
    module_path = path.relative_to(Path.cwd())
    module = importlib.import_module(".".join(module_path.parts[:-1]) + f".{module_path.stem}")

    for name, obj in inspect.getmembers(module):
        if not is_entrypoint(obj):
            continue

        yield EntrypointInfo(
            module=ModuleInfo.from_module(module),
            ns=[obj.__name__],
            methods=[
                MethodInfo(
                    name=name,
                    signature=inspect.signature(member),
                )
                for name, member in inspect.getmembers(obj)
                if not name.startswith("_") and callable(member)
            ],
        )
