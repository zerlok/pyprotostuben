import ast
import enum
import typing as t
from dataclasses import dataclass

from pyprotostuben.codegen.mypy.info import CodeBlock
from pyprotostuben.python.info import NamespaceInfo, ModuleInfo


@dataclass(frozen=True)
class FuncArgInfo:
    class Kind(enum.Enum):
        POS = enum.auto()
        KW_ONLY = enum.auto()

    name: str
    kind: Kind = Kind.POS
    annotation: t.Optional[ast.expr] = None
    default: t.Optional[ast.expr] = None


def build_module(code: CodeBlock) -> ast.Module:
    return ast.Module(
        body=[
            *(
                ast.Import(names=[ast.alias(name=module.qualname)])
                for module in sorted(code.dependencies, key=lambda x: x.qualname)
            ),
            *code.body,
        ],
        type_ignores=[],
    )


def build_func_stub(
    *,
    name: str,
    decorators: t.Optional[t.Sequence[ast.expr]] = None,
    args: t.Optional[t.Sequence[FuncArgInfo]] = None,
    returns: ast.expr,
    is_async: bool = False,
) -> ast.stmt:
    return (ast.AsyncFunctionDef if is_async else ast.FunctionDef)(
        name=name,
        decorator_list=decorators or [],
        args=ast.arguments(
            posonlyargs=[],
            args=[
                ast.arg(
                    arg=arg.name,
                    annotation=arg.annotation,
                )
                for arg in (args or [])
                if arg.kind is FuncArgInfo.Kind.POS
            ],
            # TODO: check if defaults set properly
            defaults=[
                arg.default for arg in (args or []) if arg.kind is FuncArgInfo.Kind.POS and arg.default is not None
            ],
            kwonlyargs=[
                ast.arg(
                    arg=arg.name,
                    annotation=arg.annotation,
                )
                for arg in (args or [])
                if arg.kind is FuncArgInfo.Kind.KW_ONLY
            ],
            kw_defaults=[arg.default for arg in (args or []) if arg.kind is FuncArgInfo.Kind.KW_ONLY],
        ),
        returns=returns,
        body=[ast.Ellipsis()],
        lineno=None,
    )


def build_class_def(
    *,
    name: str,
    decorators: t.Optional[t.Sequence[ast.expr]] = None,
    bases: t.Optional[t.Sequence[ast.expr]] = None,
    keywords: t.Optional[t.Mapping[str, ast.expr]] = None,
    body: t.Optional[t.Sequence[ast.stmt]] = None,
) -> ast.ClassDef:
    return ast.ClassDef(
        name=name,
        decorator_list=decorators or [],
        bases=bases or [],
        keywords=[ast.keyword(arg=key, value=value) for key, value in (keywords or {}).items()],
        body=body or [],
    )


def build_enum_class_def(
    *,
    name: str,
    base: ast.expr,
    decorators: t.Optional[t.Sequence[ast.expr]] = None,
    items: t.Sequence[t.Tuple[str, object]],
) -> ast.ClassDef:
    return build_class_def(
        name=name,
        decorators=decorators,
        bases=[base],
        body=[
            ast.Assign(
                targets=[ast.Name(id=name)],
                value=ast.Constant(value=value),
                lineno=None,
            )
            for name, value in items
        ],
    )


def build_method_stub(
    *,
    name: str,
    decorators: t.Optional[t.Sequence[ast.expr]] = None,
    args: t.Optional[t.Sequence[FuncArgInfo]] = None,
    returns: ast.expr,
    is_async: bool = False,
) -> ast.stmt:
    return build_func_stub(
        name=name,
        decorators=decorators,
        args=[FuncArgInfo("self"), *(args or [])],
        returns=returns,
        is_async=is_async,
    )


def build_init_stub(args: t.Sequence[FuncArgInfo]) -> ast.stmt:
    return build_method_stub(
        name="__init__",
        args=args,
        returns=ast.Constant(value=None),
        is_async=False,
    )


def build_ref(ns: NamespaceInfo) -> ast.expr:
    return build_attr(*ns.parts)


def build_import(module: ModuleInfo) -> ast.stmt:
    return ast.Import(names=[ast.alias(name=module.qualname)])


def build_generic_ref(generic: ast.expr, *args: ast.expr) -> ast.expr:
    first, *other = args

    if not other:
        return ast.Subscript(value=generic, slice=first)

    return ast.Subscript(value=generic, slice=ast.Tuple(elts=[first, *other]))


def build_attr(*refs: str) -> ast.expr:
    *parts, last = refs

    if not parts:
        return ast.Name(id=last)

    expr: ast.expr = ast.Name(id=parts[0])
    for ns in parts[1:]:
        expr = ast.Attribute(attr=ns, value=expr)

    return ast.Attribute(attr=last, value=expr)
