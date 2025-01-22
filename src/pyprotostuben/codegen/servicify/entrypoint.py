import importlib
import inspect
import sys
import typing as t
from collections import deque
from functools import partial
from pathlib import Path
from types import ModuleType

from pyprotostuben.codegen.servicify.model import (
    EntrypointInfo,
    EntrypointOptions,
    MethodInfo,
    StreamStreamMethodInfo,
    UnaryUnaryMethodInfo,
)
from pyprotostuben.python.info import TypeInfo

P = t.ParamSpec("P")
T = t.TypeVar("T")

__MARK = """__servicify_entrypoint_config__"""


@t.overload
def entrypoint(obj: type[T]) -> type[T]: ...


@t.overload
def entrypoint(*, name: str) -> t.Callable[[type[T]], type[T]]: ...


def entrypoint(
    obj: t.Optional[type[T]] = None,
    name: t.Optional[str] = None,
) -> t.Union[type[T], t.Callable[[type[T]], type[T]]]:
    return (
        _mark_entrypoint(obj, EntrypointOptions())
        if obj is not None
        # NOTE: mypy thinks that `T` of `_mark_entrypoint` is not the same `T` of `entrypoint`
        else t.cast(t.Callable[[type[T]], type[T]], partial(_mark_entrypoint, options=EntrypointOptions(name=name)))
    )


def _mark_entrypoint(obj: type[T], options: EntrypointOptions) -> type[T]:
    setattr(obj, __MARK, options)
    return obj


def get_entrypoint_options(obj: object) -> t.Optional[EntrypointOptions]:
    opts = getattr(obj, __MARK, None)
    assert opts is None or isinstance(opts, EntrypointOptions)
    return opts


def inspect_source_dir(
    src: Path,
    *,
    ignore_module_on_import_error: bool = False,
) -> t.Iterable[EntrypointInfo]:
    sys.path.append(str(src))
    try:
        stack = deque[Path]([src])

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
                    yield from inspect_module(module)

            elif path.is_dir() and not path.stem.startswith("_"):
                for subitem in path.iterdir():
                    stack.append(subitem)

    finally:
        importlib.invalidate_caches()
        sys.path.remove(str(src))


def inspect_module(module: ModuleType) -> t.Iterable[EntrypointInfo]:
    for name, obj in inspect.getmembers(module):
        if not inspect.isclass(obj) or obj.__module__ != module.__name__:
            continue

        opts = get_entrypoint_options(obj)
        if opts is None:
            continue

        type_info = TypeInfo.from_type(obj)

        yield EntrypointInfo(
            name=opts.name if opts.name is not None else name,
            type_=type_info,
            methods=tuple(
                inspect_method(member_name, member)
                for member_name, member in inspect.getmembers(obj)
                if not member_name.startswith("_") and callable(member)
            ),
            doc=inspect.getdoc(obj),
        )


def inspect_method(name: str, func: t.Callable[..., object]) -> MethodInfo:
    signature = inspect.signature(func)

    params = list(signature.parameters.values())[1:]

    # TODO: uncomment
    if len(params) == 1 and (streaming_type := extract_streaming_type(params[0].annotation)) is not None:
        return StreamStreamMethodInfo(
            name=name,
            input_=params[0].replace(annotation=streaming_type),
            output=extract_streaming_type(signature.return_annotation),
            doc=inspect.getdoc(func),
        )

    return UnaryUnaryMethodInfo(
        name=name,
        # skip `self`
        params=params,
        returns=signature.return_annotation,
        doc=inspect.getdoc(func),
    )


def extract_streaming_type(obj: object) -> t.Optional[type[object]]:
    origin = t.get_origin(obj)
    if not isinstance(origin, type) or not issubclass(origin, (t.Iterator, t.AsyncIterator)):
        return None

    args = t.get_args(obj)
    assert len(args) == 1

    return args[0]
