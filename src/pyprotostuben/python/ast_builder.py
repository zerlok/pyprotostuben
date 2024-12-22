# Skip `too many arguments rule`, because it is a builder. Methods are invoked with key only args.
# ruff: noqa: PLR0913

import abc
import ast
import enum
import typing as t
from dataclasses import dataclass, field
from functools import cached_property

from pyprotostuben.python.info import ModuleInfo, PackageInfo, TypeInfo

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

    @abc.abstractmethod
    def get_dependencies(self) -> t.Sequence[ModuleInfo]:
        raise NotImplementedError


class NoDependencyResolver(DependencyResolver):
    def resolve(self, info: TypeInfo) -> TypeInfo:
        return info

    def get_dependencies(self) -> t.Sequence[ModuleInfo]:
        return []


class ModuleDependencyResolver(DependencyResolver):
    def __init__(self, module: ModuleInfo) -> None:
        self.__module = module
        self.__deps: set[ModuleInfo] = set()

    def resolve(self, info: TypeInfo) -> TypeInfo:
        if info.module == self.__module:
            return TypeInfo(None, info.ns)

        if info.module is not None:
            self.__deps.add(info.module)

        return info

    def get_dependencies(self) -> t.Sequence[ModuleInfo]:
        return sorted(self.__deps or (), key=self.__get_dep_sort_key)

    def __get_dep_sort_key(self, module: ModuleInfo) -> str:
        return module.qualname


class ASTBuilder:
    def __init__(self, resolver: t.Optional[DependencyResolver] = None) -> None:
        self.__resolver = resolver if resolver is not None else NoDependencyResolver()

    @cached_property
    def typing_module(self) -> ModuleInfo:
        return ModuleInfo(None, "typing")

    @cached_property
    def builtins_module(self) -> ModuleInfo:
        return ModuleInfo(None, "builtins")

    @cached_property
    def abc_module(self) -> ModuleInfo:
        return ModuleInfo(None, "abc")

    @cached_property
    def contextlib_module(self) -> ModuleInfo:
        return ModuleInfo(None, "contextlib")

    def build_ref(self, ref: TypeRef) -> ast.expr:
        if not isinstance(ref, TypeInfo):
            return ref

        resolved = self.__resolver.resolve(ref)

        return self.build_attr(*(resolved.module.parts if resolved.module is not None else ()), *resolved.ns)

    def build_attr(self, head: str, *tail: str) -> ast.expr:
        expr: ast.expr = ast.Name(id=head)
        for attr in tail:
            expr = ast.Attribute(attr=attr, value=expr)

        return expr

    def build_docstring(self, *lines: str) -> ast.stmt:
        return ast.Expr(value=self.build_const("\n".join(lines)))

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
        is_final: bool = False,
        is_async: bool = False,
        is_context_manager: bool = False,
    ) -> ast.stmt:
        decorator_list = self._build_decorators(
            [
                TypeInfo.build(self.typing_module, "final") if is_final else None,
            ],
            decorators,
            [
                self.build_context_manager_decorator_ref(is_async=is_async) if is_context_manager else None,
            ],
        )

        if is_async:
            return ast.AsyncFunctionDef(  # type: ignore[call-overload,no-any-return,unused-ignore]
                # type_comment and type_params has default value each in 3.12 and not available in 3.9
                name=name,
                args=self._build_func_args(args),
                decorator_list=decorator_list,
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
            decorator_list=decorator_list,
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
        is_final: bool = False,
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
            is_final=is_final,
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
        is_final: bool = False,
    ) -> ast.stmt:
        head_decorators = [TypeInfo.build(self.typing_module, "final") if is_final else None]

        # NOTE: type_params has default value in 3.12 and not available in 3.9
        return ast.ClassDef(  # type: ignore[call-arg,unused-ignore]
            name=name,
            decorator_list=self._build_decorators(head_decorators, decorators),
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
    ) -> ast.stmt:
        return self.build_class_def(
            name=name,
            decorators=decorators,
            bases=bases,
            keywords={
                "metaclass": TypeInfo.build(self.abc_module, "ABCMeta"),
            },
            doc=doc,
            body=body,
        )

    def build_typed_dict_def(
        self,
        *,
        name: str,
        items: t.Mapping[str, TypeRef],
        is_final: bool = False,
    ) -> ast.stmt:
        # TODO: support inline typed dict (it is in experimental feature).
        #  https://mypy.readthedocs.io/en/stable/typed_dict.html#inline-typeddict-types
        return self.build_class_def(
            name=name,
            bases=[self.build_ref(TypeInfo.build(self.typing_module, "TypedDict"))],
            body=[
                self.build_attr_stub(
                    name=name,
                    annotation=annotation,
                )
                for name, annotation in items.items()
            ]
            if items
            else [self.build_pass_stmt()],
            is_final=is_final,
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
        is_final: bool = False,
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
            is_final=is_final,
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
        is_final: bool = False,
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
            is_final=is_final,
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
            decorators=[TypeInfo.build(self.abc_module, "abstractmethod")],
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
            decorators=[TypeInfo.build(self.abc_module, "abstractmethod")],
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
        is_final: bool = False,
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
            is_final=is_final,
            is_async=is_async,
            is_context_manager=is_context_manager,
        )

    def build_class_method_stub_def(
        self,
        *,
        name: str,
        decorators: t.Optional[t.Sequence[TypeRef]] = None,
        args: t.Optional[t.Sequence[FuncArgInfo]] = None,
        returns: TypeRef,
        doc: t.Optional[str] = None,
        is_final: bool = False,
        is_async: bool = False,
        is_context_manager: bool = False,
    ) -> ast.stmt:
        return self.build_class_method_def(
            name=name,
            decorators=decorators,
            args=args,
            returns=returns,
            doc=None,
            body=self._build_stub_body(doc),
            is_final=is_final,
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
            decorators=[self.build_attr(name, "setter")],
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

    def build_init_attrs_def(
        self,
        args: t.Sequence[FuncArgInfo],
        doc: t.Optional[str] = None,
    ) -> ast.stmt:
        return self.build_method_def(
            name="__init__",
            args=args,
            body=[self.build_assign("self", f"__{arg.name}", value=self.build_attr(arg.name)) for arg in args],
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

    @t.overload
    def build_assign(self, head: TypeRef, *, value: TypeRef) -> ast.stmt: ...

    @t.overload
    def build_assign(self, head: str, *tail: str, value: TypeRef) -> ast.stmt: ...

    def build_assign(self, head: t.Union[str, TypeRef], *tail: str, value: TypeRef) -> ast.stmt:
        return ast.Assign(
            targets=[self.build_ref(head) if isinstance(head, (ast.expr, TypeInfo)) else self.build_attr(head, *tail)],
            value=self.build_ref(value),
            # NOTE: Seems like it is allowed to pass `None`, but ast typing says it's not.
            lineno=t.cast(int, None),
        )

    def build_attr_stub(
        self,
        *,
        name: str,
        annotation: TypeRef,
        default: t.Optional[ast.expr] = None,
        is_final: bool = False,
    ) -> ast.stmt:
        # TODO: add docstring
        return ast.AnnAssign(
            target=ast.Name(id=name),
            annotation=self.build_final_ref(self.build_ref(annotation)) if is_final else self.build_ref(annotation),
            value=default,
            simple=1,
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
        items: t.Sequence[tuple[str, TypeRef]],
        body: t.Sequence[ast.stmt],
        is_async: bool = False,
    ) -> t.Union[ast.With, ast.AsyncWith]:
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

    def build_return_stmt(self, value: ast.expr) -> ast.Return:
        return ast.Return(value=value)

    def build_pass_stmt(self) -> ast.Pass:
        return ast.Pass()

    def build_context_manager_decorator_ref(self, *, is_async: bool = False) -> ast.expr:
        return self.build_ref(
            TypeInfo.build(self.contextlib_module, "asynccontextmanager" if is_async else "contextmanager")
        )

    def build_raise_not_implemented_error(self) -> ast.Raise:
        return ast.Raise(exc=ast.Name(id="NotImplementedError"), cause=None)

    def build_generic_ref(self, generic: TypeRef, *args: TypeRef) -> ast.expr:
        if len(args) == 0:
            return self.build_ref(generic)

        if len(args) == 1:
            return ast.Subscript(value=self.build_ref(generic), slice=self.build_ref(args[0]))

        return ast.Subscript(value=self.build_ref(generic), slice=ast.Tuple(elts=[self.build_ref(arg) for arg in args]))

    def build_final_ref(self, inner: TypeRef) -> ast.expr:
        return self.build_generic_ref(TypeInfo.build(self.typing_module, "Final"), inner)

    def build_class_var_ref(self, inner: TypeRef) -> ast.expr:
        return self.build_generic_ref(TypeInfo.build(self.typing_module, "ClassVar"), inner)

    def build_type_ref(self, inner: TypeRef) -> ast.expr:
        return self.build_generic_ref(TypeInfo.build(self.typing_module, "Type"), inner)

    def build_tuple_ref(self, *args: TypeRef) -> ast.expr:
        return self.build_generic_ref(TypeInfo.build(self.typing_module, "Tuple"), *args)

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

    def build_union_ref(self, *args: TypeRef) -> ast.expr:
        return self.build_generic_ref(TypeInfo.build(self.typing_module, "Union"), *args)

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

    def build_const(self, value: object) -> ast.Constant:
        return ast.Constant(value=value)

    def build_import(self, module: ModuleInfo) -> ast.Import:
        return ast.Import(names=[ast.alias(name=module.qualname)])

    def build_module(
        self,
        doc: t.Optional[str] = None,
        body: t.Optional[t.Sequence[ast.stmt]] = None,
    ) -> ast.Module:
        return ast.Module(
            body=self._build_body(
                doc,
                [
                    *(self.build_import(dep) for dep in self.__resolver.get_dependencies()),
                    *(body or ()),
                ],
            ),
            type_ignores=[],
        )

    def _build_decorators(
        self,
        *decorators: t.Optional[t.Sequence[t.Union[ast.expr, TypeInfo, None]]],
    ) -> list[ast.expr]:
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

    def _build_body(self, doc: t.Optional[str], body: t.Optional[t.Sequence[ast.stmt]]) -> list[ast.stmt]:
        result: list[ast.stmt] = list(body or ())
        if doc:
            result.insert(0, self.build_docstring(doc))

        return result

    def _build_stub_body(self, doc: t.Optional[str]) -> list[ast.stmt]:
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


@dataclass(kw_only=True)
class ModuleContext:
    info: ModuleInfo
    builder: ASTBuilder
    docs: list[str] = field(default_factory=list)
    body: list[ast.stmt] = field(default_factory=list)


class ModuleSubscriber(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def notify_module(self, info: ModuleInfo, content: ast.Module) -> None:
        raise NotImplementedError


class ModuleBuilder:
    def __init__(self, info: ModuleInfo, *subscribers: ModuleSubscriber) -> None:
        self.__context = ModuleContext(
            info=info,
            builder=ASTBuilder(ModuleDependencyResolver(info)),
        )
        self.__docs = list(docs)
        self.__subscribers = set(subscribers)

    @property
    def builder(self) -> ASTBuilder:
        return self.__context.

    def subscribe(self, *subscribers: ModuleSubscriber) -> None:
        self.__subscribers.update(subscribers)

    def unsubscribe(self, *subscribers: ModuleSubscriber) -> None:
        self.__subscribers.difference_update(subscribers)

    def build_module(self, doc: t.Optional[str] = None, body: t.Optional[t.Sequence[ast.stmt]] = None) -> ast.Module:
        module = super().build_module(doc, body)

        for subscriber in self.__subscribers:
            subscriber.notify_module(self.__info, module)

        return module


class PackageBuilder:
    def __init__(self, root: t.Optional[PackageInfo] = None) -> None:
        self.__root = root
        self.__modules: dict[ModuleInfo, ModuleContext] = {}

    def package(self, info: PackageInfo, doc: t.Optional[str] = None) -> ASTBuilder:
        return self.module(ModuleInfo(info, "__init__"), doc)

    def module(self, info: ModuleInfo, doc: t.Optional[str] = None) -> ASTBuilder:
        context = self.__modules.get(info)

        if context is None:
            target = ModuleInfo(
                parent=PackageInfo.build_or_none(
                    *(self.__root.parts if self.__root is not None else ()),
                    *info.package.parts,
                ),
                name=info.name,
            )

            context = self.__modules[info] = ModuleContext(
                info=target,
                builder=ASTBuilder(ModuleDependencyResolver(target)),
            )

        if doc:
            context.docs.append(doc)

        return context.builder

    def extend(
        self,
        info: ModuleInfo,
        *blocks: t.Optional[t.Union[ast.stmt, t.Iterable[t.Optional[ast.stmt]]]],
    ) -> None:
        if not blocks:
            return

        self.__modules[info].body.extend(
            stmt
            for block in blocks
            if block
            for stmt in (block if not isinstance(block, ast.stmt) else (block,))
            if stmt is not None
        )

    def build(self) -> t.Iterable[tuple[ModuleInfo, ast.Module]]:
        for context in self.__modules.values():
            module_ast = context.builder.build_module(doc="\n".join(context.docs), body=context.body)
            yield context.info, module_ast
