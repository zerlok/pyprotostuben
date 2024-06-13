import ast
import enum
import typing as t
from dataclasses import dataclass

from pyprotostuben.python.info import ModuleInfo


@dataclass(frozen=True)
class ArgInfo:
    class Kind(enum.Enum):
        POS = enum.auto()
        KW_ONLY = enum.auto()

    name: str
    kind: Kind = Kind.POS
    annotation: t.Optional[ast.expr] = None
    default: t.Optional[ast.expr] = None


class ASTBuilder:
    def build_module(self, *body: ast.stmt) -> ast.Module:
        return ast.Module(body=list(body), type_ignores=[])

    def build_class_def(
        self,
        *,
        name: str,
        decorators: t.Optional[t.Sequence[ast.expr]] = None,
        bases: t.Optional[t.Sequence[ast.expr]] = None,
        keywords: t.Optional[t.Sequence[ast.keyword]] = None,
        body: t.Optional[t.Sequence[ast.stmt]] = None,
    ) -> ast.ClassDef:
        return ast.ClassDef(
            name=name,
            decorator_list=decorators or [],
            bases=bases or [],
            keywords=keywords or [],
            body=body or [],
        )

    def build_enum_def(
        self,
        *,
        name: str,
        base: ast.expr,
        decorators: t.Optional[t.Sequence[ast.expr]] = None,
        items: t.Sequence[t.Tuple[str, object]],
    ) -> ast.ClassDef:
        return self.build_class_def(
            name=name,
            decorators=decorators,
            bases=[
                base,
            ],
            body=[
                ast.Assign(
                    targets=[ast.Name(id=name)],
                    value=ast.Constant(value=value),
                    lineno=None,
                )
                for name, value in items
            ],
        )

    def build_instance_method_stub(
        self,
        *,
        name: str,
        decorators: t.Optional[t.Sequence[ast.expr]] = None,
        args: t.Optional[t.Sequence[ArgInfo]] = None,
        returns: ast.expr,
        is_async: bool = False,
    ) -> ast.stmt:
        return self.build_func_stub(
            name=name,
            decorators=decorators,
            args=[ArgInfo("self"), *(args or [])],
            returns=returns,
            is_async=is_async,
        )

    def build_init_stub(self, args: t.Sequence[ArgInfo]) -> ast.stmt:
        return self.build_instance_method_stub(
            name="__init__",
            args=args,
            returns=self.build_none_expr(),
            is_async=False,
        )

    def build_func_stub(
        self,
        *,
        name: str,
        decorators: t.Optional[t.Sequence[ast.expr]] = None,
        args: t.Optional[t.Sequence[ArgInfo]] = None,
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
                    if arg.kind is ArgInfo.Kind.POS
                ],
                # TODO: check if defaults set properly
                defaults=[
                    arg.default for arg in (args or []) if arg.kind is ArgInfo.Kind.POS and arg.default is not None
                ],
                kwonlyargs=[
                    ast.arg(
                        arg=arg.name,
                        annotation=arg.annotation,
                    )
                    for arg in (args or [])
                    if arg.kind is ArgInfo.Kind.KW_ONLY
                ],
                kw_defaults=[arg.default for arg in (args or []) if arg.kind is ArgInfo.Kind.KW_ONLY],
            ),
            returns=returns,
            body=[ast.Ellipsis()],
            lineno=None,
        )

    def build_field_def(self, name: str, annotation: ast.expr) -> ast.stmt:
        return ast.AnnAssign(target=[ast.Name(id=name)], annotation=annotation, simple=1)

    def build_generic_instance_expr(self, generic: ast.expr, *args: ast.expr) -> ast.expr:
        if not args:
            return generic

        if len(args) == 1:
            return ast.Subscript(value=generic, slice=args[0])

        return ast.Subscript(value=generic, slice=ast.Tuple(elts=list(args)))

    def build_attr_expr(self, *refs: str) -> ast.expr:
        *namespace, name = refs

        if not namespace:
            return ast.Name(id=name)

        expr: ast.expr = ast.Name(id=namespace[0])
        for ns in namespace[1:]:
            expr = ast.Attribute(attr=ns, value=expr)

        return ast.Attribute(attr=name, value=expr)

    def build_import(self, module: ModuleInfo) -> ast.stmt:
        return ast.Import(names=[ast.alias(name=module.qualname)])

    # def build_import_from(self, module: ModuleInfo) -> ast.stmt:
    #     return ast.ImportFrom(module=module.package.qualname, names=[ast.alias(module.name)], level=0)

    def build_none_expr(self) -> ast.expr:
        return self.const(None)

    def build_bool_expr(self) -> ast.expr:
        return self.build_attr_expr("bool")

    def build_int_expr(self) -> ast.expr:
        return self.build_attr_expr("int")

    def build_float_expr(self) -> ast.expr:
        return self.build_attr_expr("float")

    def build_str_expr(self) -> ast.expr:
        return self.build_attr_expr("str")

    def const(self, value: object) -> ast.expr:
        return ast.Constant(value=value)
