# Skip `too many arguments rule`, because it is a builder. Methods are invoked with key only args.
# ruff: noqa: PLR0913

import abc
import ast
import enum
import typing as t
from dataclasses import dataclass
from functools import cached_property

from pyprotostuben.python.info import ModuleInfo, TypeInfo

TypeRef = t.Union[ast.expr, TypeInfo]


@dataclass(frozen=True)
class FuncArgInfo:
    class Kind(enum.Enum):
        POS = enum.auto()
        KW_ONLY = enum.auto()

    name: str
    kind: Kind
    annotation: t.Optional[TypeRef]
    default: t.Optional[ast.expr]


class DependencyResolver(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def resolve(self, info: TypeInfo) -> TypeInfo:
        raise NotImplementedError


class ASTBuilder:
    def __init__(self, resolver: DependencyResolver) -> None:
        self.__resolver = resolver

    @cached_property
    def typing_module(self) -> ModuleInfo:
        return ModuleInfo(None, "typing")

    @cached_property
    def builtins_module(self) -> ModuleInfo:
        return ModuleInfo(None, "builtins")

    @cached_property
    def contextlib_module(self) -> ModuleInfo:
        return ModuleInfo(None, "contextlib")

    def build_ref(self, ref: TypeRef) -> ast.expr:
        if not isinstance(ref, TypeInfo):
            return ref

        resolved = self.__resolver.resolve(ref)

        return self.build_name(*(resolved.module.parts if resolved.module is not None else ()), *resolved.ns)

    def build_name(self, head: str, *tail: str) -> ast.expr:
        expr: ast.expr = ast.Name(id=head)
        for attr in tail:
            expr = ast.Attribute(attr=attr, value=expr)

        return expr

    def build_docstring(self, *lines: str) -> ast.stmt:
        return ast.Expr(value=ast.Constant(value="\n".join(lines)))

    def build_pos_arg(self, name: str, annotation: TypeRef, default: t.Optional[ast.expr] = None) -> FuncArgInfo:
        return FuncArgInfo(
            name=name,
            kind=FuncArgInfo.Kind.POS,
            annotation=annotation,
            default=default,
        )

    def build_kw_arg(self, name: str, annotation: TypeRef, default: t.Optional[ast.expr] = None) -> FuncArgInfo:
        return FuncArgInfo(
            name=name,
            kind=FuncArgInfo.Kind.KW_ONLY,
            annotation=annotation,
            default=default,
        )

    def build_func_def(
        self,
        *,
        name: str,
        decorators: t.Optional[t.Sequence[TypeRef]] = None,
        args: t.Optional[t.Sequence[FuncArgInfo]] = None,
        returns: TypeRef,
        doc: t.Optional[str] = None,
        body: t.Sequence[ast.stmt],
        is_async: bool = False,
        is_context_manager: bool = False,
    ) -> ast.stmt:
        head_decorators = [self.build_context_manager_decorator_ref(is_async=is_async) if is_context_manager else None]

        if is_async:
            return ast.AsyncFunctionDef(  # type: ignore[call-overload,no-any-return,unused-ignore]
                # type_comment and type_params has default value each in 3.12 and not available in 3.9
                name=name,
                args=self._build_func_args(args),
                decorator_list=self._build_decorators(head_decorators, decorators),
                returns=self.build_iterator_ref(self.build_ref(returns), is_async=is_async)
                if is_context_manager
                else self.build_ref(returns),
                body=self._build_body(doc, body),
                # NOTE: Seems like it is allowed to pass `None`, but ast typing says it's not.
                lineno=t.cast(int, None),
            )

        return ast.FunctionDef(  # type: ignore[call-overload,no-any-return,unused-ignore]
            # type_comment and type_params has default value each in 3.12 and not available in 3.9
            name=name,
            decorator_list=self._build_decorators(head_decorators, decorators),
            args=self._build_func_args(args),
            body=self._build_body(doc, body),
            returns=self.build_iterator_ref(self.build_ref(returns), is_async=is_async)
            if is_context_manager
            else self.build_ref(returns),
            # NOTE: Seems like it is allowed to pass `None`, but ast typing says it isn't
            lineno=t.cast(int, None),
        )

    def build_func_stub(
        self,
        *,
        name: str,
        decorators: t.Optional[t.Sequence[TypeRef]] = None,
        args: t.Optional[t.Sequence[FuncArgInfo]] = None,
        returns: TypeRef,
        doc: t.Optional[str] = None,
        is_async: bool = False,
        is_context_manager: bool = False,
    ) -> ast.stmt:
        return self.build_func_def(
            name=name,
            decorators=decorators,
            args=args,
            returns=returns,
            doc=doc,
            body=self._build_stub_body(doc),
            is_async=is_async,
            is_context_manager=is_context_manager,
        )

    def build_class_def(
        self,
        *,
        name: str,
        decorators: t.Optional[t.Sequence[TypeRef]] = None,
        bases: t.Optional[t.Sequence[TypeRef]] = None,
        keywords: t.Optional[t.Mapping[str, TypeRef]] = None,
        doc: t.Optional[str] = None,
        body: t.Optional[t.Sequence[ast.stmt]] = None,
    ) -> ast.ClassDef:
        # type_params has default value in 3.12 and not available in 3.9
        return ast.ClassDef(  # type: ignore[call-arg,unused-ignore]
            name=name,
            decorator_list=self._build_decorators(decorators),
            bases=[self.build_ref(base) for base in (bases or ())],
            keywords=[ast.keyword(arg=key, value=self.build_ref(value)) for key, value in (keywords or {}).items()],
            body=self._build_body(doc, body),
        )

    def build_abstract_class_def(
        self,
        *,
        name: str,
        decorators: t.Optional[t.Sequence[TypeRef]] = None,
        bases: t.Optional[t.Sequence[TypeRef]] = None,
        doc: t.Optional[str] = None,
        body: t.Optional[t.Sequence[ast.stmt]] = None,
    ) -> ast.ClassDef:
        return self.build_class_def(
            name=name,
            decorators=decorators,
            bases=bases,
            keywords={
                "metaclass": TypeInfo.build(ModuleInfo(None, "abc"), "ABCMeta"),
            },
            doc=doc,
            body=body,
        )

    def build_method_def(
        self,
        *,
        name: str,
        decorators: t.Optional[t.Sequence[TypeRef]] = None,
        args: t.Optional[t.Sequence[FuncArgInfo]] = None,
        returns: TypeRef,
        doc: t.Optional[str] = None,
        body: t.Sequence[ast.stmt],
        is_async: bool = False,
        is_context_manager: bool = False,
    ) -> ast.stmt:
        return self.build_func_def(
            name=name,
            decorators=decorators,
            args=[FuncArgInfo(name="self", kind=FuncArgInfo.Kind.POS, annotation=None, default=None), *(args or [])],
            returns=returns,
            doc=doc,
            body=body,
            is_async=is_async,
            is_context_manager=is_context_manager,
        )

    def build_method_stub(
        self,
        *,
        name: str,
        decorators: t.Optional[t.Sequence[TypeRef]] = None,
        args: t.Optional[t.Sequence[FuncArgInfo]] = None,
        returns: TypeRef,
        doc: t.Optional[str] = None,
        is_async: bool = False,
        is_context_manager: bool = False,
    ) -> ast.stmt:
        return self.build_method_def(
            name=name,
            decorators=decorators,
            args=args,
            returns=returns,
            doc=doc,
            body=self._build_stub_body(doc),
            is_async=is_async,
            is_context_manager=is_context_manager,
        )

    def build_abstract_method_def(
        self,
        *,
        name: str,
        args: t.Optional[t.Sequence[FuncArgInfo]] = None,
        returns: TypeRef,
        doc: t.Optional[str] = None,
        is_async: bool = False,
        is_context_manager: bool = False,
    ) -> ast.stmt:
        return self.build_method_def(
            name=name,
            decorators=[TypeInfo.build(ModuleInfo(None, "abc"), "abstractmethod")],
            args=args,
            returns=self.build_context_manager_ref(returns, is_async=is_async) if is_context_manager else returns,
            doc=doc,
            body=[self.build_raise_not_implemented_error()],
            is_async=is_async,
        )

    def build_abstract_method_stub(
        self,
        *,
        name: str,
        args: t.Optional[t.Sequence[FuncArgInfo]] = None,
        returns: TypeRef,
        doc: t.Optional[str] = None,
        is_async: bool = False,
        is_context_manager: bool = False,
    ) -> ast.stmt:
        return self.build_method_stub(
            name=name,
            decorators=[TypeInfo.build(ModuleInfo(None, "abc"), "abstractmethod")],
            args=args,
            returns=self.build_context_manager_ref(returns, is_async=is_async) if is_context_manager else returns,
            doc=doc,
            is_async=is_async,
        )

    def build_class_method_def(
        self,
        *,
        name: str,
        decorators: t.Optional[t.Sequence[TypeRef]] = None,
        args: t.Optional[t.Sequence[FuncArgInfo]] = None,
        returns: TypeRef,
        doc: t.Optional[str] = None,
        body: t.Sequence[ast.stmt],
        is_async: bool = False,
        is_context_manager: bool = False,
    ) -> ast.stmt:
        return self.build_func_def(
            name=name,
            decorators=[*(decorators or ()), TypeInfo.build(self.builtins_module, "classmethod")],
            args=[FuncArgInfo(name="cls", kind=FuncArgInfo.Kind.POS, annotation=None, default=None), *(args or [])],
            returns=returns,
            doc=doc,
            body=body,
            is_async=is_async,
            is_context_manager=is_context_manager,
        )

    def build_property_getter_stub(
        self,
        *,
        name: str,
        annotation: TypeRef,
        doc: t.Optional[str] = None,
    ) -> ast.stmt:
        return self.build_method_stub(
            name=name,
            decorators=[TypeInfo.build(self.builtins_module, "property")],
            returns=annotation,
            doc=doc,
            is_async=False,
        )

    def build_property_setter_stub(
        self,
        *,
        name: str,
        annotation: TypeRef,
        doc: t.Optional[str] = None,
    ) -> ast.stmt:
        return self.build_method_stub(
            name=name,
            decorators=[TypeInfo.build(None, name, "setter")],
            args=[self.build_pos_arg(name="value", annotation=annotation)],
            returns=self.build_none_ref(),
            doc=doc,
            is_async=False,
        )

    def build_init_def(
        self,
        args: t.Sequence[FuncArgInfo],
        body: t.Sequence[ast.stmt],
        doc: t.Optional[str] = None,
    ) -> ast.stmt:
        return self.build_method_def(
            name="__init__",
            args=args,
            body=body,
            returns=self.build_none_ref(),
            doc=doc,
            is_async=False,
        )

    def build_init_stub(
        self,
        args: t.Sequence[FuncArgInfo],
        doc: t.Optional[str] = None,
    ) -> ast.stmt:
        return self.build_init_def(args=args, body=self._build_stub_body(doc), doc=doc)

    def build_attr_stub(
        self,
        *,
        name: str,
        annotation: TypeRef,
        default: t.Optional[ast.expr] = None,
    ) -> ast.stmt:
        # TODO: add docstring
        return ast.AnnAssign(
            target=ast.Name(id=name),
            annotation=self.build_ref(annotation),
            value=default,
            simple=1,
        )

    def build_attr_assign(self, target: TypeRef, value: TypeRef) -> ast.stmt:
        return ast.Assign(
            targets=[self.build_ref(target)],
            value=self.build_ref(value),
            # NOTE: Seems like it is allowed to pass `None`, but ast typing says it's not.
            lineno=t.cast(int, None),
        )

    def build_call(
        self,
        *,
        func: TypeRef,
        args: t.Optional[t.Sequence[TypeRef]] = None,
        kwargs: t.Optional[t.Mapping[str, TypeRef]] = None,
        is_async: bool = False,
    ) -> ast.expr:
        expr = ast.Call(
            func=self.build_ref(func),
            args=[self.build_ref(arg) for arg in (args or ())],
            keywords=[
                ast.keyword(
                    arg=key,
                    value=self.build_ref(value),
                )
                for key, value in (kwargs or {}).items()
            ],
        )

        return ast.Await(value=expr) if is_async else expr

    def build_call_stmt(
        self,
        *,
        func: TypeRef,
        args: t.Optional[t.Sequence[TypeRef]] = None,
        kwargs: t.Optional[t.Mapping[str, TypeRef]] = None,
        is_async: bool = False,
    ) -> ast.stmt:
        return ast.Expr(value=self.build_call(func=func, args=args, kwargs=kwargs, is_async=is_async))

    def build_with_stmt(
        self,
        *,
        items: t.Sequence[t.Tuple[str, TypeRef]],
        body: t.Sequence[ast.stmt],
        is_async: bool = False,
    ) -> ast.stmt:
        with_items = [
            ast.withitem(
                context_expr=self.build_ref(expr),
                optional_vars=ast.Name(id=name),
            )
            for name, expr in items
        ]

        return (
            ast.AsyncWith(
                items=with_items,
                body=list(body),
                # NOTE: Seems like it is allowed to pass `None`, but ast typing says it's not.
                lineno=t.cast(int, None),
            )
            if is_async
            else ast.With(
                items=with_items,
                body=list(body),
                # NOTE: Seems like it is allowed to pass `None`, but ast typing says it's not.
                lineno=t.cast(int, None),
            )
        )

    def build_yield_stmt(self, value: ast.expr) -> ast.stmt:
        return ast.Expr(value=ast.Yield(value=value))

    def build_return_stmt(self, value: ast.expr) -> ast.stmt:
        return ast.Return(value=value)

    def build_context_manager_decorator_ref(self, *, is_async: bool = False) -> ast.expr:
        return self.build_ref(
            TypeInfo.build(self.contextlib_module, "asynccontextmanager" if is_async else "contextmanager")
        )

    def build_raise_not_implemented_error(self) -> ast.stmt:
        return ast.Raise(exc=ast.Name(id="NotImplementedError"), cause=None)

    def build_generic_ref(self, generic: TypeRef, *args: TypeRef) -> ast.expr:
        if len(args) == 0:
            return self.build_ref(generic)

        if len(args) == 1:
            return ast.Subscript(value=self.build_ref(generic), slice=self.build_ref(args[0]))

        return ast.Subscript(value=self.build_ref(generic), slice=ast.Tuple(elts=[self.build_ref(arg) for arg in args]))

    def build_mapping_ref(self, key: TypeRef, value: TypeRef, *, mutable: bool = False) -> ast.expr:
        return self.build_generic_ref(
            TypeInfo.build(self.typing_module, "MutableMapping" if mutable else "Mapping"),
            key,
            value,
        )

    def build_sequence_ref(self, inner: TypeRef, *, mutable: bool = False) -> ast.expr:
        return self.build_generic_ref(
            TypeInfo.build(self.typing_module, "MutableSequence" if mutable else "Sequence"),
            inner,
        )

    def build_optional_ref(self, inner: TypeRef) -> ast.expr:
        return self.build_generic_ref(
            TypeInfo.build(self.typing_module, "Optional"),
            inner,
        )

    def build_context_manager_ref(self, inner: TypeRef, *, is_async: bool = False) -> ast.expr:
        return self.build_generic_ref(
            TypeInfo.build(self.typing_module, "AsyncContextManager" if is_async else "ContextManager"),
            inner,
        )

    def build_iterator_ref(self, inner: TypeRef, *, is_async: bool = False) -> ast.expr:
        return self.build_generic_ref(
            TypeInfo.build(self.typing_module, "AsyncIterator" if is_async else "Iterator"),
            inner,
        )

    def build_literal_ref(self, *items: ast.expr) -> ast.expr:
        if not items:
            return self.build_no_return_ref()

        return self.build_generic_ref(TypeInfo.build(self.typing_module, "Literal"), *items)

    def build_no_return_ref(self) -> ast.expr:
        return self.build_ref(TypeInfo.build(self.typing_module, "NoReturn"))

    def build_overload_ref(self) -> ast.expr:
        return self.build_ref(TypeInfo.build(self.typing_module, "overload"))

    def build_none_ref(self) -> ast.expr:
        return ast.Constant(value=None)

    def build_bool_ref(self) -> ast.expr:
        return self.build_ref(TypeInfo.build(self.builtins_module, "bool"))

    def build_int_ref(self) -> ast.expr:
        return self.build_ref(TypeInfo.build(self.builtins_module, "int"))

    def build_float_ref(self) -> ast.expr:
        return self.build_ref(TypeInfo.build(self.builtins_module, "float"))

    def build_str_ref(self) -> ast.expr:
        return self.build_ref(TypeInfo.build(self.builtins_module, "str"))

    def build_import(self, module: ModuleInfo) -> ast.stmt:
        return ast.Import(names=[ast.alias(name=module.qualname)])

    def build_module(
        self,
        doc: t.Optional[str] = None,
        deps: t.Optional[t.Collection[ModuleInfo]] = None,
        body: t.Optional[t.Sequence[ast.stmt]] = None,
    ) -> ast.Module:
        return ast.Module(
            body=self._build_body(
                doc,
                [
                    *(self.build_import(dep) for dep in sorted(deps or (), key=lambda d: d.qualname)),
                    *(body or ()),
                ],
            ),
            type_ignores=[],
        )

    def _build_decorators(
        self,
        *decorators: t.Optional[t.Sequence[t.Union[ast.expr, TypeInfo, None]]],
    ) -> t.List[ast.expr]:
        return [
            self.build_ref(dec) for block in (decorators or ()) if block for dec in (block or ()) if dec is not None
        ]

    def _build_func_args(self, args: t.Optional[t.Sequence[FuncArgInfo]]) -> ast.arguments:
        return ast.arguments(
            posonlyargs=[],
            args=[
                ast.arg(
                    arg=arg.name,
                    annotation=self.build_ref(arg.annotation) if arg.annotation is not None else None,
                )
                for arg in (args or [])
                if arg.kind is FuncArgInfo.Kind.POS
            ],
            defaults=[
                self.build_ref(arg.default)
                for arg in (args or [])
                if arg.kind is FuncArgInfo.Kind.POS and arg.default is not None
            ],
            kwonlyargs=[
                ast.arg(
                    arg=arg.name,
                    annotation=self.build_ref(arg.annotation) if arg.annotation is not None else None,
                )
                for arg in (args or [])
                if arg.kind is FuncArgInfo.Kind.KW_ONLY
            ],
            kw_defaults=[
                self.build_ref(arg.default) if arg.default is not None else None
                for arg in (args or [])
                if arg.kind is FuncArgInfo.Kind.KW_ONLY
            ],
        )

    def _build_body(self, doc: t.Optional[str], body: t.Optional[t.Sequence[ast.stmt]]) -> t.List[ast.stmt]:
        result: t.List[ast.stmt] = list(body or ())
        if doc:
            result.insert(0, self.build_docstring(doc))

        return result

    def _build_stub_body(self, doc: t.Optional[str]) -> t.List[ast.stmt]:
        return (
            [
                ast.Expr(value=ast.Constant(value=...)),
            ]
            if doc
            else [
                # NOTE: Ellipsis is ok for function body, but ast typing says it's not.
                t.cast(ast.stmt, ast.Constant(value=...))
            ]
        )
