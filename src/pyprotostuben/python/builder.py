# Skip `too many arguments rule`, because it is a builder. Methods are invoked with key only args.
# ruff: noqa: PLR0913

import abc
import ast
import enum
import typing as t
from collections import deque
from dataclasses import dataclass
from functools import cache, cached_property

from pyprotostuben.python.info import ModuleInfo, PackageInfo, TypeInfo

TypeRef = t.Union[ast.expr, TypeInfo]


class PredefTrait:
    @cached_property
    def typing_module(self) -> ModuleInfo:
        return ModuleInfo(None, "typing")

    @cached_property
    def dataclasses_module(self) -> ModuleInfo:
        return ModuleInfo(None, "dataclasses")

    @cached_property
    def builtins_module(self) -> ModuleInfo:
        return ModuleInfo(None, "builtins")

    @cached_property
    def abc_module(self) -> ModuleInfo:
        return ModuleInfo(None, "abc")

    @cached_property
    def contextlib_module(self) -> ModuleInfo:
        return ModuleInfo(None, "contextlib")

    @cached_property
    def async_context_manager_decorator(self) -> TypeInfo:
        return TypeInfo.build(self.contextlib_module, "asynccontextmanager")

    @cached_property
    def context_manager_decorator(self) -> TypeInfo:
        return TypeInfo.build(self.contextlib_module, "contextmanager")

    @cached_property
    def none_ref(self) -> TypeInfo:
        return TypeInfo.build(self.builtins_module, "NoneType")

    @cached_property
    def bool_ref(self) -> TypeInfo:
        return TypeInfo.build(self.builtins_module, "bool")

    @cached_property
    def int_ref(self) -> TypeInfo:
        return TypeInfo.build(self.builtins_module, "int")

    @cached_property
    def float_ref(self) -> TypeInfo:
        return TypeInfo.build(self.builtins_module, "float")

    @cached_property
    def str_ref(self) -> TypeInfo:
        return TypeInfo.build(self.builtins_module, "str")

    @cached_property
    def list_ref(self) -> TypeInfo:
        return TypeInfo.build(self.builtins_module, "list")

    @cached_property
    def dict_ref(self) -> TypeInfo:
        return TypeInfo.build(self.builtins_module, "dict")

    @cached_property
    def set_ref(self) -> TypeInfo:
        return TypeInfo.build(self.builtins_module, "set")

    @cached_property
    def property_ref(self) -> TypeInfo:
        return TypeInfo.build(self.builtins_module, "property")

    @cached_property
    def classmethod_ref(self) -> TypeInfo:
        return TypeInfo.build(self.builtins_module, "classmethod")

    @cached_property
    def abc_meta_ref(self) -> TypeInfo:
        return TypeInfo.build(self.abc_module, "ABCMeta")

    @cached_property
    def abstractmethod_ref(self) -> TypeInfo:
        return TypeInfo.build(self.abc_module, "abstractmethod")

    @cached_property
    def generic_ref(self) -> TypeInfo:
        return TypeInfo.build(self.typing_module, "Generic")

    @cached_property
    def final_type_ref(self) -> TypeInfo:
        return TypeInfo.build(self.typing_module, "Final")

    @cached_property
    def final_decorator_ref(self) -> TypeInfo:
        return TypeInfo.build(self.typing_module, "final")

    @cached_property
    def class_var_ref(self) -> TypeInfo:
        return TypeInfo.build(self.typing_module, "ClassVar")

    @cached_property
    def type_ref(self) -> TypeInfo:
        return TypeInfo.build(self.typing_module, "Type")

    @cached_property
    def tuple_ref(self) -> TypeInfo:
        return TypeInfo.build(self.typing_module, "Tuple")

    @cached_property
    def container_ref(self) -> TypeInfo:
        return TypeInfo.build(self.typing_module, "Container")

    @cached_property
    def sequence_ref(self) -> TypeInfo:
        return TypeInfo.build(self.typing_module, "Sequence")

    @cached_property
    def mutable_sequence_ref(self) -> TypeInfo:
        return TypeInfo.build(self.typing_module, "MutableSequence")

    @cached_property
    def dataclass_decorator_ref(self) -> TypeInfo:
        return TypeInfo.build(self.dataclasses_module, "dataclass")

    @cached_property
    def typed_dict_ref(self) -> TypeInfo:
        return TypeInfo.build(self.typing_module, "TypedDict")

    @cached_property
    def mapping_ref(self) -> TypeInfo:
        return TypeInfo.build(self.typing_module, "Mapping")

    @cached_property
    def mutable_mapping_ref(self) -> TypeInfo:
        return TypeInfo.build(self.typing_module, "MutableMapping")

    @cached_property
    def optional_ref(self) -> TypeInfo:
        return TypeInfo.build(self.typing_module, "Optional")

    @cached_property
    def union_ref(self) -> TypeInfo:
        return TypeInfo.build(self.typing_module, "Union")

    @cached_property
    def context_manager_ref(self) -> TypeInfo:
        return TypeInfo.build(self.typing_module, "ContextManager")

    @cached_property
    def async_context_manager_ref(self) -> TypeInfo:
        return TypeInfo.build(self.typing_module, "AsyncContextManager")

    @cached_property
    def iterator_ref(self) -> TypeInfo:
        return TypeInfo.build(self.typing_module, "Iterator")

    @cached_property
    def async_iterator_ref(self) -> TypeInfo:
        return TypeInfo.build(self.typing_module, "AsyncIterator")

    @cached_property
    def iterable_ref(self) -> TypeInfo:
        return TypeInfo.build(self.typing_module, "Iterable")

    @cached_property
    def async_iterable_ref(self) -> TypeInfo:
        return TypeInfo.build(self.typing_module, "AsyncIterable")

    @cached_property
    def literal_ref(self) -> TypeInfo:
        return TypeInfo.build(self.typing_module, "Literal")

    @cached_property
    def no_return_ref(self) -> TypeInfo:
        return TypeInfo.build(self.typing_module, "NoReturn")

    @cached_property
    def overload_decorator_ref(self) -> TypeInfo:
        return TypeInfo.build(self.typing_module, "overload")

    @cached_property
    def override_decorator_ref(self) -> TypeInfo:
        return TypeInfo.build(self.typing_module, "override")


@cache
def get_predef_trait() -> PredefTrait:
    return PredefTrait()


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


class ModuleASTSubscriber(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def notify_module(self, info: ModuleInfo, content: ast.Module) -> None:
        raise NotImplementedError


def get_attrs(expr: ast.expr) -> t.Sequence[str]:
    queue = deque([expr])
    parts = list[str]()

    while queue:
        item = queue.pop()

        if isinstance(item, ast.Attribute):
            queue.append(item.value)
            parts.append(item.attr)

        elif isinstance(item, ast.Name):
            parts.append(item.id)

    return tuple(reversed(parts))


class ModuleASTBuilder:
    def __init__(
        self,
        info: ModuleInfo,
        subscribers: t.Optional[t.Sequence[ModuleASTSubscriber]] = None,
    ) -> None:
        self.__info = info
        self.__subscribers = list(subscribers or ())

        self.__body = list[ast.stmt]()
        self.__resolver = ModuleDependencyResolver(info)
        self.__predef = get_predef_trait()

    @property
    def info(self) -> ModuleInfo:
        return self.__info

    def ref(self, ref: TypeRef) -> ast.expr:
        if not isinstance(ref, TypeInfo):
            return ref

        if ref == self.__predef.none_ref:
            return self.none_ref()

        resolved = self.__resolver.resolve(ref)

        return self.attr(*(resolved.module.parts if resolved.module is not None else ()), *resolved.ns)

    def attr(self, head: t.Union[str, ast.expr], *tail: str) -> ast.expr:
        expr: ast.expr = ast.Name(id=head) if isinstance(head, str) else head
        for attr in tail:
            expr = ast.Attribute(attr=attr, value=expr)

        return expr

    def attr_stub(
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
            annotation=self.final_ref(self.ref(annotation)) if is_final else self.ref(annotation),
            value=default,
            simple=1,
        )

    def docstring(self, *lines: str) -> ast.stmt:
        return ast.Expr(value=self.const("\n".join(lines)))

    def pos_arg(self, name: str, annotation: TypeRef, default: t.Optional[ast.expr] = None) -> FuncArgInfo:
        return FuncArgInfo(
            name=name,
            kind=FuncArgInfo.Kind.POS,
            annotation=annotation,
            default=default,
        )

    def kw_arg(self, name: str, annotation: TypeRef, default: t.Optional[ast.expr] = None) -> FuncArgInfo:
        return FuncArgInfo(
            name=name,
            kind=FuncArgInfo.Kind.KW_ONLY,
            annotation=annotation,
            default=default,
        )

    def func_def(
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
        is_overload: bool = False,
        is_override: bool = False,
    ) -> ast.stmt:
        decorator_list = self._build_decorators(
            [
                self.__predef.overload_decorator_ref if is_overload else None,
                self.__predef.final_decorator_ref if is_final else None,
                self.__predef.override_decorator_ref if is_override else None,
            ],
            decorators,
            [
                self.context_manager_decorator_ref(is_async=is_async) if is_context_manager else None,
            ],
        )

        if is_async:
            return ast.AsyncFunctionDef(  # type: ignore[call-overload,no-any-return,unused-ignore]
                # type_comment and type_params has default value each in 3.12 and not available in 3.9
                name=name,
                args=self._build_func_args(args),
                decorator_list=decorator_list,
                returns=self.iterator_ref(self.ref(returns), is_async=is_async)
                if is_context_manager
                else self.ref(returns),
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
            returns=self.iterator_ref(self.ref(returns), is_async=is_async)
            if is_context_manager
            else self.ref(returns),
            # NOTE: Seems like it is allowed to pass `None`, but ast typing says it isn't
            lineno=t.cast(int, None),
        )

    def func_stub(
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
        is_overload: bool = False,
        is_override: bool = False,
    ) -> ast.stmt:
        return self.func_def(
            name=name,
            decorators=decorators,
            args=args,
            returns=returns,
            doc=doc,
            body=self._build_stub_body(doc),
            is_final=is_final,
            is_async=is_async,
            is_context_manager=is_context_manager,
            is_overload=is_overload,
            is_override=is_override,
        )

    def class_def(
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
        head_decorators = [self.__predef.final_decorator_ref if is_final else None]

        # NOTE: type_params has default value in 3.12 and not available in 3.9
        return ast.ClassDef(  # type: ignore[call-arg,unused-ignore]
            name=name,
            decorator_list=self._build_decorators(head_decorators, decorators),
            bases=[self.ref(base) for base in (bases or ())],
            keywords=[ast.keyword(arg=key, value=self.ref(value)) for key, value in (keywords or {}).items()],
            body=self._build_body(doc, body),
        )

    def abstract_class_def(
        self,
        *,
        name: str,
        decorators: t.Optional[t.Sequence[TypeRef]] = None,
        bases: t.Optional[t.Sequence[TypeRef]] = None,
        doc: t.Optional[str] = None,
        body: t.Optional[t.Sequence[ast.stmt]] = None,
    ) -> ast.stmt:
        return self.class_def(
            name=name,
            decorators=decorators,
            bases=bases,
            keywords={"metaclass": self.__predef.abc_meta_ref},
            doc=doc,
            body=body,
        )

    def dataclass_def(
        self,
        *,
        name: str,
        frozen: bool = False,
        kw_only: bool = False,
        fields: t.Optional[t.Mapping[str, TypeRef]] = None,
        decorators: t.Optional[t.Sequence[TypeRef]] = None,
        bases: t.Optional[t.Sequence[TypeRef]] = None,
        doc: t.Optional[str] = None,
        body: t.Optional[t.Sequence[ast.stmt]] = None,
        is_final: bool = False,
    ) -> ast.stmt:
        return self.class_def(
            name=name,
            decorators=[
                self.call(
                    func=self.__predef.dataclass_decorator_ref,
                    kwargs={"frozen": self.const(frozen), "kw_only": self.const(kw_only)},
                ),
                *(decorators or ()),
            ],
            bases=bases,
            doc=doc,
            body=[
                *(body or ()),
                *(
                    self.attr_stub(
                        name=name,
                        annotation=annotation,
                    )
                    for name, annotation in fields.items()
                ),
            ]
            if fields
            else [self.pass_stmt()],
            is_final=is_final,
        )

    def typed_dict_def(
        self,
        *,
        name: str,
        items: t.Mapping[str, TypeRef],
        is_final: bool = False,
    ) -> ast.stmt:
        # TODO: support inline typed dict (it is in experimental feature).
        #  https://mypy.readthedocs.io/en/stable/typed_dict.html#inline-typeddict-types
        return self.class_def(
            name=name,
            bases=[self.__predef.typed_dict_ref],
            body=[
                self.attr_stub(
                    name=name,
                    annotation=annotation,
                )
                for name, annotation in items.items()
            ]
            if items
            else [self.pass_stmt()],
            is_final=is_final,
        )

    def method_def(
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
        is_overload: bool = False,
        is_override: bool = False,
    ) -> ast.stmt:
        return self.func_def(
            name=name,
            decorators=decorators,
            args=[FuncArgInfo(name="self", kind=FuncArgInfo.Kind.POS, annotation=None, default=None), *(args or [])],
            returns=returns,
            doc=doc,
            body=body,
            is_final=is_final,
            is_async=is_async,
            is_context_manager=is_context_manager,
            is_overload=is_overload,
            is_override=is_override,
        )

    def method_stub(
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
        is_overload: bool = False,
        is_override: bool = False,
    ) -> ast.stmt:
        return self.method_def(
            name=name,
            decorators=decorators,
            args=args,
            returns=returns,
            doc=doc,
            body=self._build_stub_body(doc),
            is_final=is_final,
            is_async=is_async,
            is_context_manager=is_context_manager,
            is_overload=is_overload,
            is_override=is_override,
        )

    def abstract_method_def(
        self,
        *,
        name: str,
        args: t.Optional[t.Sequence[FuncArgInfo]] = None,
        returns: TypeRef,
        doc: t.Optional[str] = None,
        is_async: bool = False,
        is_context_manager: bool = False,
        is_overload: bool = False,
    ) -> ast.stmt:
        return self.method_def(
            name=name,
            decorators=[self.__predef.abstractmethod_ref],
            args=args,
            returns=self.context_manager_ref(returns, is_async=is_async) if is_context_manager else returns,
            doc=doc,
            body=[self.raise_not_implemented_error()],
            is_async=is_async,
            is_overload=is_overload,
        )

    def abstract_method_stub(
        self,
        *,
        name: str,
        args: t.Optional[t.Sequence[FuncArgInfo]] = None,
        returns: TypeRef,
        doc: t.Optional[str] = None,
        is_async: bool = False,
        is_context_manager: bool = False,
        is_overload: bool = False,
    ) -> ast.stmt:
        return self.method_stub(
            name=name,
            decorators=[self.__predef.abstractmethod_ref],
            args=args,
            returns=self.context_manager_ref(returns, is_async=is_async) if is_context_manager else returns,
            doc=doc,
            is_async=is_async,
            is_overload=is_overload,
        )

    def class_method_def(
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
        is_overload: bool = False,
        is_override: bool = False,
    ) -> ast.stmt:
        return self.func_def(
            name=name,
            decorators=[*(decorators or ()), self.__predef.classmethod_ref],
            args=[FuncArgInfo(name="cls", kind=FuncArgInfo.Kind.POS, annotation=None, default=None), *(args or [])],
            returns=returns,
            doc=doc,
            body=body,
            is_final=is_final,
            is_async=is_async,
            is_context_manager=is_context_manager,
            is_overload=is_overload,
            is_override=is_override,
        )

    def class_method_stub(
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
        is_overload: bool = False,
        is_override: bool = False,
    ) -> ast.stmt:
        return self.class_method_def(
            name=name,
            decorators=decorators,
            args=args,
            returns=returns,
            doc=None,
            body=self._build_stub_body(doc),
            is_final=is_final,
            is_async=is_async,
            is_context_manager=is_context_manager,
            is_overload=is_overload,
            is_override=is_override,
        )

    def property_getter_stub(
        self,
        *,
        name: str,
        annotation: TypeRef,
        doc: t.Optional[str] = None,
    ) -> ast.stmt:
        return self.method_stub(
            name=name,
            decorators=[self.__predef.property_ref],
            returns=annotation,
            doc=doc,
            is_async=False,
        )

    def property_setter_stub(
        self,
        *,
        name: str,
        annotation: TypeRef,
        doc: t.Optional[str] = None,
    ) -> ast.stmt:
        return self.method_stub(
            name=name,
            decorators=[self.attr(name, "setter")],
            args=[self.pos_arg(name="value", annotation=annotation)],
            returns=self.none_ref(),
            doc=doc,
            is_async=False,
        )

    def init_def(
        self,
        args: t.Sequence[FuncArgInfo],
        body: t.Sequence[ast.stmt],
        doc: t.Optional[str] = None,
    ) -> ast.stmt:
        return self.method_def(
            name="__init__",
            args=args,
            body=body,
            returns=self.none_ref(),
            doc=doc,
            is_async=False,
        )

    def init_attrs_def(
        self,
        args: t.Sequence[FuncArgInfo],
        doc: t.Optional[str] = None,
    ) -> ast.stmt:
        return self.method_def(
            name="__init__",
            args=args,
            body=[self.assign("self", f"__{arg.name}", value=self.attr(arg.name)) for arg in args],
            returns=self.none_ref(),
            doc=doc,
            is_async=False,
        )

    def init_stub(
        self,
        args: t.Sequence[FuncArgInfo],
        doc: t.Optional[str] = None,
    ) -> ast.stmt:
        return self.init_def(args=args, body=self._build_stub_body(doc), doc=doc)

    @t.overload
    def assign(self, head: TypeRef, *, value: TypeRef) -> ast.stmt: ...

    @t.overload
    def assign(self, head: str, *tail: str, value: TypeRef) -> ast.stmt: ...

    def assign(self, head: t.Union[str, TypeRef], *tail: str, value: TypeRef) -> ast.stmt:
        return ast.Assign(
            targets=[self.ref(head) if isinstance(head, (ast.expr, TypeInfo)) else self.attr(head, *tail)],
            value=self.ref(value),
            # NOTE: Seems like it is allowed to pass `None`, but ast typing says it's not.
            lineno=t.cast(int, None),
        )

    def call(
        self,
        *,
        func: TypeRef,
        args: t.Optional[t.Sequence[TypeRef]] = None,
        kwargs: t.Optional[t.Mapping[str, TypeRef]] = None,
        is_async: bool = False,
    ) -> ast.expr:
        expr = ast.Call(
            func=self.ref(func),
            args=[self.ref(arg) for arg in (args or ())],
            keywords=[
                ast.keyword(
                    arg=key,
                    value=self.ref(value),
                )
                for key, value in (kwargs or {}).items()
            ],
        )

        return ast.Await(value=expr) if is_async else expr

    def call_stmt(
        self,
        *,
        func: TypeRef,
        args: t.Optional[t.Sequence[TypeRef]] = None,
        kwargs: t.Optional[t.Mapping[str, TypeRef]] = None,
        is_async: bool = False,
    ) -> ast.stmt:
        return ast.Expr(value=self.call(func=func, args=args, kwargs=kwargs, is_async=is_async))

    def method_call(
        self,
        *,
        obj: TypeRef,
        name: str,
        args: t.Optional[t.Sequence[TypeRef]] = None,
        kwargs: t.Optional[t.Mapping[str, TypeRef]] = None,
        is_async: bool = False,
    ) -> ast.expr:
        return self.call(
            func=ast.Attribute(value=self.ref(obj), attr=name),
            args=args,
            kwargs=kwargs,
            is_async=is_async,
        )

    def with_stmt(
        self,
        *,
        items: t.Sequence[tuple[str, TypeRef]],
        body: t.Sequence[ast.stmt],
        is_async: bool = False,
    ) -> t.Union[ast.With, ast.AsyncWith]:
        with_items = [
            ast.withitem(
                context_expr=self.ref(expr),
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

    def yield_stmt(self, value: ast.expr) -> ast.stmt:
        return ast.Expr(value=ast.Yield(value=value))

    def return_stmt(self, value: ast.expr) -> ast.Return:
        return ast.Return(value=value)

    def pass_stmt(self) -> ast.Pass:
        return ast.Pass()

    def ternary_not_none_expr(
        self,
        body: ast.expr,
        test: ast.expr,
        or_else: t.Optional[ast.expr] = None,
    ) -> ast.expr:
        return ast.IfExp(
            test=ast.Compare(left=test, ops=[ast.IsNot()], comparators=[self.none_ref()]),
            body=body,
            orelse=or_else if or_else is not None else self.none_ref(),
        )

    def tuple_expr(self, *items: ast.expr) -> ast.expr:
        return ast.Tuple(elts=list(items))

    @t.overload
    def set_expr(self, items: ast.expr, target: ast.expr, item: ast.expr) -> ast.expr: ...

    @t.overload
    def set_expr(self, items: t.Collection[ast.expr]) -> ast.expr: ...

    def set_expr(
        self,
        items: t.Union[ast.expr, t.Collection[ast.expr]],
        target: t.Optional[ast.expr] = None,
        item: t.Optional[ast.expr] = None,
    ) -> ast.expr:
        if isinstance(items, ast.expr):
            assert target is not None
            assert item is not None

            return ast.SetComp(
                elt=item,
                generators=[ast.comprehension(target=target, iter=items, ifs=[], is_async=False)],
            )

        return ast.Set(
            elts=[self.ref(item) for item in items],
        )

    @t.overload
    def list_expr(self, items: ast.expr, target: ast.expr, item: ast.expr) -> ast.expr: ...

    @t.overload
    def list_expr(self, items: t.Sequence[ast.expr]) -> ast.expr: ...

    def list_expr(
        self,
        items: t.Union[ast.expr, t.Sequence[ast.expr]],
        target: t.Optional[ast.expr] = None,
        item: t.Optional[ast.expr] = None,
    ) -> ast.expr:
        if isinstance(items, ast.expr):
            assert target is not None
            assert item is not None

            return ast.ListComp(
                elt=item,
                generators=[ast.comprehension(target=target, iter=items, ifs=[], is_async=False)],
            )

        return ast.List(
            elts=[self.ref(item) for item in items],
        )

    @t.overload
    def dict_expr(self, items: ast.expr, target: ast.expr, key: ast.expr, value: ast.expr) -> ast.expr: ...

    @t.overload
    def dict_expr(self, items: t.Mapping[ast.expr, ast.expr]) -> ast.expr: ...

    def dict_expr(
        self,
        items: t.Union[ast.expr, t.Mapping[ast.expr, ast.expr]],
        target: t.Optional[ast.expr] = None,
        key: t.Optional[ast.expr] = None,
        value: t.Optional[ast.expr] = None,
    ) -> ast.expr:
        if isinstance(items, ast.expr):
            assert target is not None
            assert key is not None
            assert value is not None

            return ast.DictComp(
                key=key,
                value=value,
                generators=[ast.comprehension(target=target, iter=items, ifs=[], is_async=False)],
            )

        return ast.Dict(
            keys=list(items.keys()),
            values=list(items.values()),
        )

    def context_manager_decorator_ref(self, *, is_async: bool = False) -> ast.expr:
        return self.ref(
            self.__predef.async_context_manager_decorator if is_async else self.__predef.context_manager_decorator
        )

    def raise_not_implemented_error(self) -> ast.Raise:
        return ast.Raise(exc=ast.Name(id="NotImplementedError"), cause=None)

    def generic_ref(self, generic: TypeRef, *args: TypeRef) -> ast.expr:
        if len(args) == 0:
            return self.ref(generic)

        if len(args) == 1:
            return ast.Subscript(value=self.ref(generic), slice=self.ref(args[0]))

        return ast.Subscript(value=self.ref(generic), slice=ast.Tuple(elts=[self.ref(arg) for arg in args]))

    def final_ref(self, inner: TypeRef) -> ast.expr:
        return self.generic_ref(self.__predef.final_type_ref, inner)

    def class_var_ref(self, inner: TypeRef) -> ast.expr:
        return self.generic_ref(self.__predef.class_var_ref, inner)

    def type_ref(self, inner: TypeRef) -> ast.expr:
        return self.generic_ref(self.__predef.type_ref, inner)

    def tuple_ref(self, *args: TypeRef) -> ast.expr:
        return self.generic_ref(self.__predef.tuple_ref, *args)

    def mapping_ref(self, key: TypeRef, value: TypeRef, *, mutable: bool = False) -> ast.expr:
        return self.generic_ref(self.__predef.mutable_mapping_ref if mutable else self.__predef.mapping_ref, key, value)

    def sequence_ref(self, inner: TypeRef, *, mutable: bool = False) -> ast.expr:
        return self.generic_ref(self.__predef.mutable_sequence_ref if mutable else self.__predef.sequence_ref, inner)

    def optional_ref(self, inner: TypeRef) -> ast.expr:
        return self.generic_ref(self.__predef.optional_ref, inner)

    def union_ref(self, *args: TypeRef) -> ast.expr:
        return self.generic_ref(self.__predef.union_ref, *args)

    def container_ref(self, inner: TypeRef) -> ast.expr:
        return self.generic_ref(self.__predef.container_ref, inner)

    def context_manager_ref(self, inner: TypeRef, *, is_async: bool = False) -> ast.expr:
        return self.generic_ref(
            self.__predef.async_context_manager_ref if is_async else self.__predef.context_manager_ref,
            inner,
        )

    def iterator_ref(self, inner: TypeRef, *, is_async: bool = False) -> ast.expr:
        return self.generic_ref(self.__predef.async_iterator_ref if is_async else self.__predef.iterator_ref, inner)

    def literal_ref(self, *items: ast.expr) -> ast.expr:
        if not items:
            return self.no_return_ref()

        return self.generic_ref(self.__predef.literal_ref, *items)

    def no_return_ref(self) -> ast.expr:
        return self.ref(self.__predef.no_return_ref)

    def overload_ref(self) -> ast.expr:
        return self.ref(self.__predef.overload_decorator_ref)

    def none_ref(self) -> ast.expr:
        return ast.Constant(value=None)

    def bool_ref(self) -> ast.expr:
        return self.ref(self.__predef.bool_ref)

    def int_ref(self) -> ast.expr:
        return self.ref(self.__predef.int_ref)

    def float_ref(self) -> ast.expr:
        return self.ref(self.__predef.float_ref)

    def str_ref(self) -> ast.expr:
        return self.ref(self.__predef.str_ref)

    def const(self, value: object) -> ast.Constant:
        return ast.Constant(value=value)

    def import_stmt(self, module: ModuleInfo) -> ast.Import:
        return ast.Import(names=[ast.alias(name=module.qualname)])

    def append(self, stmt: t.Optional[ast.stmt]) -> None:
        if stmt is not None:
            self.__body.append(stmt)

    @t.overload
    def extend(self, *parts: t.Optional[ast.stmt]) -> None: ...

    @t.overload
    def extend(self, *parts: t.Optional[t.Iterable[t.Optional[ast.stmt]]]) -> None: ...

    @t.overload
    def extend(self, *parts: t.Optional[t.Iterable[t.Optional[t.Iterable[t.Optional[ast.stmt]]]]]) -> None: ...

    def extend(
        self,
        *parts: t.Union[
            t.Optional[ast.stmt],
            t.Optional[t.Iterable[t.Optional[ast.stmt]]],
            t.Optional[t.Iterable[t.Optional[t.Iterable[t.Optional[ast.stmt]]]]],
        ],
    ) -> None:
        inlined = list[ast.stmt]()

        for part in parts:
            queue = deque([part])

            while queue:
                item = queue.pop()

                if isinstance(item, t.Iterable):
                    queue.extend(item)
                elif item is not None:
                    inlined.append(item)

        self.__body.extend(reversed(inlined))

    def build(
        self,
        doc: t.Optional[str] = None,
        body: t.Optional[t.Iterable[t.Optional[ast.stmt]]] = None,
    ) -> ast.Module:
        self.extend(body)

        module = ast.Module(
            body=self._build_body(
                doc,
                [
                    *(self.import_stmt(dep) for dep in self.__resolver.get_dependencies()),
                    *self.__body,
                ],
            ),
            type_ignores=[],
        )

        for sub in self.__subscribers:
            sub.notify_module(self.__info, module)

        return module

    def _build_decorators(
        self,
        *decorators: t.Optional[t.Sequence[t.Union[ast.expr, TypeInfo, None]]],
    ) -> list[ast.expr]:
        return [self.ref(dec) for block in (decorators or ()) if block for dec in (block or ()) if dec is not None]

    def _build_func_args(self, args: t.Optional[t.Sequence[FuncArgInfo]]) -> ast.arguments:
        return ast.arguments(
            posonlyargs=[],
            args=[
                ast.arg(
                    arg=arg.name,
                    annotation=self.ref(arg.annotation) if arg.annotation is not None else None,
                )
                for arg in (args or [])
                if arg.kind is FuncArgInfo.Kind.POS
            ],
            defaults=[
                self.ref(arg.default)
                for arg in (args or [])
                if arg.kind is FuncArgInfo.Kind.POS and arg.default is not None
            ],
            kwonlyargs=[
                ast.arg(
                    arg=arg.name,
                    annotation=self.ref(arg.annotation) if arg.annotation is not None else None,
                )
                for arg in (args or [])
                if arg.kind is FuncArgInfo.Kind.KW_ONLY
            ],
            kw_defaults=[
                self.ref(arg.default) if arg.default is not None else None
                for arg in (args or [])
                if arg.kind is FuncArgInfo.Kind.KW_ONLY
            ],
        )

    def _build_body(self, doc: t.Optional[str], body: t.Optional[t.Sequence[ast.stmt]]) -> list[ast.stmt]:
        result: list[ast.stmt] = list(body or ())
        if doc:
            result.insert(0, self.docstring(doc))

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


class PackageASTBuilder(ModuleASTSubscriber):
    def __init__(self, info: t.Optional[PackageInfo] = None) -> None:
        self.__info = info
        self.__modules: dict[ModuleInfo, ModuleASTBuilder] = {}
        self.__built: dict[ModuleInfo, ast.Module] = {}

    def notify_module(self, info: ModuleInfo, content: ast.Module) -> None:
        self.__built[info] = content

    @property
    def info(self) -> t.Optional[PackageInfo]:
        return self.__info

    def package(self, info: t.Optional[PackageInfo]) -> ModuleASTBuilder:
        return self.module(ModuleInfo(info, "__init__"))

    def module(self, info: ModuleInfo) -> ModuleASTBuilder:
        builder = self.__modules.get(info)

        if builder is None:
            target = ModuleInfo(
                parent=PackageInfo.build_or_none(
                    *(self.__info.parts if self.__info is not None else ()),
                    *(info.package.parts if info.package is not None else ()),
                ),
                name=info.name,
            )

            builder = self.__modules[info] = ModuleASTBuilder(target, [self])

        return builder

    def build(self) -> t.Sequence[tuple[ModuleInfo, ast.Module]]:
        return sorted(self.__built.items(), key=self._get_qualname)

    def _get_qualname(self, pair: tuple[ModuleInfo, ast.Module]) -> str:
        return pair[0].qualname
