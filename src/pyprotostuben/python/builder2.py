from __future__ import annotations

__all__ = [
    "ASTResolver",
    "AttrASTBuilder",
    "BuildContext",
    "CallASTBuilder",
    "ClassBodyASTBuilder",
    "ClassHeaderASTBuilder",
    "Expr",
    "ExpressionASTBuilder",
    "ForHeaderASTBuilder",
    "FuncBodyASTBuilder",
    "FuncHeaderASTBuilder",
    "MethodBodyASTBuilder",
    "MethodHeaderASTBuilder",
    "ModuleASTBuilder",
    "PackageASTBuilder",
    "ScopeASTBuilder",
    "StatementASTBuilder",
    "Stmt",
    "TypeInfoProvider",
    "TypeRef",
    "TypeRefBuilder",
    "get_predefs",
    "module",
    "package",
    "render",
]

import abc
import ast
import typing as t
from collections import defaultdict, deque
from contextlib import contextmanager
from dataclasses import dataclass
from functools import cache, cached_property
from itertools import chain
from types import TracebackType

from pyprotostuben.python.info import ModuleInfo, PackageInfo, TypeInfo

T_co = t.TypeVar("T_co", covariant=True)


class ExpressionASTBuilder(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def build(self) -> ast.expr:
        raise NotImplementedError


class StatementASTBuilder(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def build(self) -> t.Sequence[ast.stmt]:
        raise NotImplementedError


class TypeInfoProvider(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def provide_type_info(self) -> TypeInfo:
        raise NotImplementedError

    @abc.abstractmethod
    def ref(self) -> TypeRefBuilder:
        raise NotImplementedError


Expr = t.Union[ast.expr, ExpressionASTBuilder]
Stmt = t.Union[ast.stmt, StatementASTBuilder, Expr]
TypeRef = t.Union[Expr, type[object], TypeInfo, TypeInfoProvider]


class Predefs:
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
    def none_type_ref(self) -> TypeInfo:
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
def get_predefs() -> Predefs:
    return Predefs()


@dataclass()
class Scope:
    name: t.Optional[str]
    body: t.MutableSequence[ast.stmt]


class BuildContext:
    def __init__(
        self,
        packages: t.MutableSequence[PackageInfo],
        dependencies: t.MutableMapping[ModuleInfo, t.MutableSet[ModuleInfo]],
        scopes: t.MutableSequence[Scope],
    ) -> None:
        self.__packages = packages
        self.__dependencies = dependencies
        self.__scopes = scopes
        self.__module: t.Optional[ModuleInfo] = None

    @property
    def module(self) -> ModuleInfo:
        assert self.__module is not None
        return self.__module

    def enter_package(self, info: PackageInfo) -> t.Self:
        assert self.__module is None
        self.__packages.append(info)
        return self

    def leave_package(self) -> t.Self:
        assert self.__module is None
        self.__packages.pop()
        return self

    def enter_module(self, info: ModuleInfo, body: t.MutableSequence[ast.stmt]) -> Scope:
        assert self.__module is None
        assert len(self.__scopes) == 0
        self.__module = info
        return self.enter_scope(None, body)

    def leave_module(self) -> Scope:
        assert len(self.__scopes) == 1
        scope = self.leave_scope()
        self.__module = None
        return scope

    def enter_scope(self, name: t.Optional[str], body: t.MutableSequence[ast.stmt]) -> Scope:
        scope = Scope(name, body)
        self.__scopes.append(scope)
        return scope

    def leave_scope(self) -> Scope:
        return self.__scopes.pop()

    @property
    def namespace(self) -> t.Sequence[str]:
        return tuple(scope.name for scope in self.__scopes if scope.name is not None)

    @property
    def name(self) -> str:
        return self.namespace[-1]

    @property
    def current_dependencies(self) -> t.MutableSet[ModuleInfo]:
        return self.__dependencies[self.module]

    def get_dependencies(self, info: ModuleInfo) -> t.Collection[ModuleInfo]:
        return self.__dependencies[info]

    @property
    def current_scope(self) -> Scope:
        return self.__scopes[-1]

    @property
    def current_body(self) -> t.MutableSequence[ast.stmt]:
        return self.current_scope.body

    def append_body(self, stmt: t.Optional[ast.stmt]) -> None:
        if stmt is not None:
            self.current_body.append(stmt)

    def extend_body(self, stmts: t.Sequence[t.Optional[ast.stmt]]) -> None:
        self.current_body.extend(stmt for stmt in stmts if stmt is not None)


class ASTResolver:
    def __init__(self, context: BuildContext) -> None:
        self.__context = context

    def expr(self, ref: TypeRef, *tail: str) -> ast.expr:
        if isinstance(ref, ExpressionASTBuilder):
            ref = ref.build()

        if isinstance(ref, ast.expr):
            return self.__chain_attr(ref, *tail)

        if isinstance(ref, TypeInfoProvider):
            ref = ref.provide_type_info()

        if not isinstance(ref, TypeInfo):
            ref = TypeInfo.from_type(ref)

        assert isinstance(ref, TypeInfo), f"{type(ref)}: {ref}"

        if ref.module is not None and ref.module != self.__context.module:
            self.__context.current_dependencies.add(ref.module)

        else:
            ns = self.__context.namespace
            ref = TypeInfo(None, ref.ns if ref.ns[: len(ns)] != ns else ref.ns[len(ns) :])

        head, *middle = (*(ref.module.parts if ref.module is not None else ()), *ref.ns)

        return self.__chain_attr(ast.Name(id=head), *middle, *tail)

    def stmts(
        self,
        *stmts: Stmt,
        docs: t.Optional[t.Sequence[str]] = None,
        pass_if_empty: bool = False,
    ) -> list[ast.stmt]:
        body = list(
            chain.from_iterable(
                stmt.build()
                if isinstance(stmt, StatementASTBuilder)
                else (stmt,)
                if isinstance(stmt, ast.stmt)
                else (ast.Expr(value=self.expr(stmt)),)
                for stmt in stmts
            )
        )

        if docs:
            body.insert(0, ast.Expr(value=ast.Constant(value="\n".join(docs))))

        if not body and pass_if_empty:
            body.append(ast.Pass())

        return body

    def __chain_attr(self, expr: ast.expr, *tail: str) -> ast.expr:
        for attr in tail:
            expr = ast.Attribute(attr=attr, value=expr)

        return expr


class TypeRefBuilder(ExpressionASTBuilder):
    def __init__(self, resolver: ASTResolver, info: TypeInfo) -> None:
        self.__resolver = resolver
        self.__info = info
        self.__wraps: t.Callable[[TypeInfo], ast.expr] = self.__resolver.expr
        self.__base = _BaseASTBuilder(resolver)

    def optional(self) -> TypeRefBuilder:
        inner = self.__wraps

        def wrap(info: TypeInfo) -> ast.expr:
            return self.__base.optional_type(inner(info))

        self.__wraps = wrap

        return self

    def list(self) -> TypeRefBuilder:
        inner = self.__wraps

        def wrap(info: TypeInfo) -> ast.expr:
            return self.__base.generic_type(list, inner(info))

        self.__wraps = wrap

        return self

    def context_manager(self, *, is_async: bool = False) -> TypeRefBuilder:
        inner = self.__wraps

        def wrap(info: TypeInfo) -> ast.expr:
            return self.__base.context_manager_type(inner(info), is_async=is_async)

        self.__wraps = wrap

        return self

    def iterator(self, *, is_async: bool = False) -> TypeRefBuilder:
        inner = self.__wraps

        def wrap(info: TypeInfo) -> ast.expr:
            return self.__base.iterator_type(inner(info), is_async=is_async)

        self.__wraps = wrap

        return self

    def attr(self, *tail: str) -> AttrASTBuilder:
        return AttrASTBuilder(self.__resolver, self, *tail)

    def init(
        self,
        args: t.Optional[t.Sequence[Expr]] = None,
        kwargs: t.Optional[t.Mapping[str, Expr]] = None,
    ) -> CallASTBuilder:
        return self.attr().call(args, kwargs)

    @t.override
    def build(self) -> ast.expr:
        return self.__wraps(self.__info)


class AttrASTBuilder(ExpressionASTBuilder):
    def __init__(self, resolver: ASTResolver, head: t.Union[str, TypeRef], *tail: str) -> None:
        self.__resolver = resolver
        self.__head = head
        self.__tail = tail

    @cached_property
    def parts(self) -> t.Sequence[str]:
        if isinstance(self.__head, str):
            return self.__head, *self.__tail

        queue = deque([self.__head])
        parts = list[str]()

        while queue:
            item = queue.pop()

            if isinstance(item, ast.Attribute):
                queue.append(item.value)
                parts.append(item.attr)

            elif isinstance(item, ast.Name):
                parts.append(item.id)

            elif isinstance(item, AttrASTBuilder):
                parts.extend(reversed(item.parts))

        return *reversed(parts), *self.__tail

    def attr(self, *tail: str) -> t.Self:
        return self.__class__(self.__resolver, self, *tail)

    def call(
        self,
        args: t.Optional[t.Sequence[Expr]] = None,
        kwargs: t.Optional[t.Mapping[str, Expr]] = None,
    ) -> CallASTBuilder:
        return CallASTBuilder(
            resolver=self.__resolver,
            func=self,
            args=args,
            kwargs=kwargs,
        )

    @t.override
    def build(self) -> ast.expr:
        return self.__resolver.expr(
            ast.Name(id=self.__head) if isinstance(self.__head, str) else self.__head,
            *self.__tail,
        )


class CallASTBuilder(ExpressionASTBuilder):
    def __init__(
        self,
        resolver: ASTResolver,
        func: TypeRef,
        args: t.Optional[t.Sequence[Expr]] = None,
        kwargs: t.Optional[t.Mapping[str, Expr]] = None,
    ) -> None:
        self.__resolver = resolver
        self.__func = func
        self.__args = list[Expr]()
        self.__kwargs = dict[str, Expr]()
        self.__is_awaited = False

        for arg in args or ():
            self.arg(arg)

        for name, kwarg in (kwargs or {}).items():
            self.kwarg(name, kwarg)

    def await_(self, *, is_awaited: bool = True) -> t.Self:
        self.__is_awaited = is_awaited
        return self

    def arg(self, expr: Expr) -> t.Self:
        self.__args.append(self.__resolver.expr(expr))
        return self

    def kwarg(self, name: str, expr: Expr) -> t.Self:
        self.__kwargs[name] = expr
        return self

    def attr(self, *tail: str) -> AttrASTBuilder:
        return AttrASTBuilder(self.__resolver, self).attr(*tail)

    def call(
        self,
        args: t.Optional[t.Sequence[Expr]] = None,
        kwargs: t.Optional[t.Mapping[str, Expr]] = None,
    ) -> t.Self:
        return self.__class__(
            resolver=self.__resolver,
            func=self,
            args=args,
            kwargs=kwargs,
        )

    def build(self) -> ast.expr:
        node: ast.expr = ast.Call(
            func=self.__resolver.expr(self.__func),
            args=[self.__resolver.expr(arg) for arg in self.__args],
            keywords=[ast.keyword(arg=key, value=self.__resolver.expr(kwarg)) for key, kwarg in self.__kwargs.items()],
            lineno=0,
        )

        if self.__is_awaited:
            node = ast.Await(value=node)

        return node


class _BaseASTBuilder:
    def __init__(self, resolver: ASTResolver) -> None:
        self._resolver = resolver

    def const(self, value: object) -> ast.expr:
        assert not isinstance(value, ast.AST)
        return ast.Constant(value=value)

    def none(self) -> ast.expr:
        return self.const(None)

    def ternary_not_none_expr(
        self,
        body: Expr,
        test: Expr,
        or_else: t.Optional[Expr] = None,
    ) -> ast.expr:
        return ast.IfExp(
            test=ast.Compare(left=self._expr(test), ops=[ast.IsNot()], comparators=[self.none()]),
            body=self._expr(body),
            orelse=self._expr(or_else) if or_else is not None else self.none(),
        )

    def tuple_expr(self, *items: TypeRef) -> ast.expr:
        return ast.Tuple(elts=[self._expr(item) for item in items])

    @t.overload
    def set_expr(self, items: Expr, target: Expr, item: Expr) -> ast.expr: ...

    @t.overload
    def set_expr(self, items: t.Collection[Expr]) -> ast.expr: ...

    def set_expr(
        self,
        items: t.Union[Expr, t.Collection[Expr]],
        target: t.Optional[Expr] = None,
        item: t.Optional[Expr] = None,
    ) -> ast.expr:
        if isinstance(items, (ast.expr, ExpressionASTBuilder)):
            assert target is not None
            assert item is not None

            return ast.SetComp(
                elt=self._expr(item),
                generators=[
                    ast.comprehension(target=self._expr(target), iter=self._expr(items), ifs=[], is_async=False)
                ],
            )

        return ast.Set(elts=[self._expr(item) for item in items])

    @t.overload
    def list_expr(self, items: Expr, target: Expr, item: Expr) -> ast.expr: ...

    @t.overload
    def list_expr(self, items: t.Sequence[Expr]) -> ast.expr: ...

    def list_expr(
        self,
        items: t.Union[Expr, t.Sequence[Expr]],
        target: t.Optional[Expr] = None,
        item: t.Optional[Expr] = None,
    ) -> ast.expr:
        if isinstance(items, (ast.expr, ExpressionASTBuilder)):
            assert target is not None
            assert item is not None

            return ast.ListComp(
                elt=self._expr(item),
                generators=[
                    ast.comprehension(target=self._expr(target), iter=self._expr(items), ifs=[], is_async=False)
                ],
            )

        return ast.List(elts=[self._expr(item) for item in items])

    @t.overload
    def dict_expr(self, items: Expr, target: Expr, key: Expr, value: Expr) -> ast.expr: ...

    @t.overload
    def dict_expr(self, items: t.Mapping[Expr, Expr]) -> ast.expr: ...

    def dict_expr(
        self,
        items: t.Union[Expr, t.Mapping[Expr, Expr]],
        target: t.Optional[Expr] = None,
        key: t.Optional[Expr] = None,
        value: t.Optional[Expr] = None,
    ) -> ast.expr:
        if isinstance(items, (ast.expr, ExpressionASTBuilder)):
            assert target is not None
            assert key is not None
            assert value is not None

            return ast.DictComp(
                key=self._expr(key),
                value=self._expr(value),
                generators=[
                    ast.comprehension(target=self._expr(target), iter=self._expr(items), ifs=[], is_async=False)
                ],
            )

        return ast.Dict(
            keys=[self._expr(key) for key in items],
            values=[self._expr(value) for value in items.values()],
        )

    def not_(self, expr: Expr) -> ast.expr:
        return ast.UnaryOp(op=ast.Not(), operand=self._expr(expr))

    def attr(self, head: t.Union[str, TypeRef], *tail: str) -> AttrASTBuilder:
        return AttrASTBuilder(self._resolver, head, *tail)

    def call(
        self,
        func: TypeRef,
        args: t.Optional[t.Sequence[Expr]] = None,
        kwargs: t.Optional[t.Mapping[str, Expr]] = None,
    ) -> CallASTBuilder:
        return self.attr(func).call(args, kwargs)

    def type_(self, base: t.Union[type[object], TypeInfo]) -> TypeRefBuilder:
        return TypeRefBuilder(self._resolver, base if isinstance(base, TypeInfo) else TypeInfo.from_type(base))

    def generic_type(self, generic: TypeRef, *args: TypeRef) -> ast.expr:
        if len(args) == 0:
            return self._expr(generic)

        if len(args) == 1:
            return ast.Subscript(value=self._expr(generic), slice=self._expr(args[0]))

        return ast.Subscript(value=self._expr(generic), slice=self.tuple_expr(*args))

    def literal_type(self, *args: t.Union[str, Expr]) -> ast.expr:
        if not args:
            return self._expr(get_predefs().no_return_ref)

        return self.generic_type(
            get_predefs().literal_ref,
            *(self.const(arg) if isinstance(arg, str) else arg for arg in args),
        )

    def optional_type(self, of_type: TypeRef) -> ast.expr:
        return self.generic_type(get_predefs().optional_ref, of_type)

    def sequence_type(self, of_type: TypeRef, *, mutable: bool = False) -> ast.expr:
        return self.generic_type(get_predefs().mutable_sequence_ref if mutable else get_predefs().sequence_ref, of_type)

    def iterator_type(self, of_type: TypeRef, *, is_async: bool = False) -> ast.expr:
        return self.generic_type(get_predefs().async_iterator_ref if is_async else get_predefs().iterator_ref, of_type)

    def context_manager_type(self, of_type: TypeRef, *, is_async: bool = False) -> ast.expr:
        return self.generic_type(
            get_predefs().async_context_manager_ref if is_async else get_predefs().context_manager_ref,
            of_type,
        )

    def ellipsis_stmt(self) -> ast.stmt:
        return ast.Expr(value=ast.Constant(value=...))

    def pass_stmt(self) -> ast.stmt:
        return ast.Pass()

    def _expr(self, expr: TypeRef) -> ast.expr:
        return self._resolver.expr(expr)

    def _stmt(self, *stmts: t.Optional[Stmt]) -> t.Sequence[ast.stmt]:
        return self._resolver.stmts(*(stmt for stmt in stmts if stmt is not None))


class _BaseHeaderASTBuilder(t.Generic[T_co], StatementASTBuilder, metaclass=abc.ABCMeta):
    def __init__(self, context: BuildContext, resolver: ASTResolver, name: t.Optional[str] = None) -> None:
        self._context = context
        self._resolver = resolver
        self._name = name

    def __enter__(self) -> T_co:
        self._context.enter_scope(self._name, [])
        return self._create_scope_builder()

    def __exit__(
        self,
        exc_type: t.Optional[type[BaseException]],
        exc_value: t.Optional[BaseException],
        exc_traceback: t.Optional[TracebackType],
    ) -> None:
        if exc_type is None:
            # 1. build statements using nested context
            stmts = self._resolver.stmts(self)
            # 2. exit nested context
            self._context.leave_scope()
            # 3. fill statements to current scope
            self._context.extend_body(stmts)

    @t.override
    @abc.abstractmethod
    def build(self) -> t.Sequence[ast.stmt]:
        raise NotImplementedError

    @abc.abstractmethod
    def _create_scope_builder(self) -> T_co:
        raise NotImplementedError


class ScopeASTBuilder(_BaseASTBuilder):
    def __init__(self, context: BuildContext, resolver: ASTResolver) -> None:
        super().__init__(resolver)
        self._context = context

    def class_def(self, name: str) -> ClassHeaderASTBuilder:
        return ClassHeaderASTBuilder(self._context, self._resolver, name)

    def func_def(self, name: str) -> FuncHeaderASTBuilder:
        return FuncHeaderASTBuilder(self._context, self._resolver, name)

    def field_def(self, name: str, annotation: TypeRef, default: t.Optional[Expr] = None) -> ast.stmt:
        node = ast.AnnAssign(
            target=ast.Name(id=name),
            annotation=self._expr(annotation),
            value=self._expr(default) if default is not None else None,
            simple=1,
        )
        self._context.append_body(node)

        return node

    def append(self, *stmts: t.Optional[Stmt]) -> None:
        self._context.extend_body(self._stmt(*stmts))

    def assign_stmt(self, target: t.Union[str, Expr], value: Expr) -> ast.stmt:
        node = ast.Assign(
            targets=[self._expr(self.attr(target))],
            value=self._expr(value),
            lineno=0,
        )
        self._context.append_body(node)

        return node

    def if_stmt(self, test: Expr) -> IfStatementASTBuilder:
        return IfStatementASTBuilder(self._context, self._resolver, test)

    def for_stmt(self, target: str, items: Expr) -> ForHeaderASTBuilder:
        return ForHeaderASTBuilder(self._context, self._resolver, target, items)

    def while_stmt(self, test: Expr) -> WhileHeaderASTBuilder:
        return WhileHeaderASTBuilder(self._context, self._resolver, test)

    def break_stmt(self) -> ast.stmt:
        node = ast.Break()
        self._context.append_body(node)
        return node

    def return_stmt(self, value: Expr) -> ast.stmt:
        node = ast.Return(
            value=self._expr(value),
            lineno=0,
        )
        self._context.append_body(node)

        return node

    def yield_stmt(self, value: Expr) -> ast.stmt:
        node = ast.Expr(
            value=ast.Yield(
                value=self._expr(value),
                lineno=0,
            ),
        )
        self._context.append_body(node)

        return node

    def try_stmt(self) -> TryStatementASTBuilder:
        return TryStatementASTBuilder(self._context, self._resolver)

    def raise_stmt(self, err: Expr, cause: t.Optional[Expr] = None) -> ast.stmt:
        node = ast.Raise(exc=self._expr(err), cause=self._expr(cause) if cause is not None else None)
        self._context.append_body(node)
        return node

    def with_stmt(self) -> WithStatementASTBuilder:
        return WithStatementASTBuilder(self._context, self._resolver)


class _BaseScopeBodyASTBuilder(ScopeASTBuilder, StatementASTBuilder):
    def __init__(self, context: BuildContext, resolver: ASTResolver, parent: StatementASTBuilder) -> None:
        super().__init__(context, resolver)
        self.__parent = parent

    def build(self) -> t.Sequence[ast.stmt]:
        return self.__parent.build()


class _BaseChainedASTBuilder(_BaseHeaderASTBuilder[t.Self], metaclass=abc.ABCMeta):
    def _create_scope_builder(self) -> t.Self:
        return self


class _BaseChainPartASTBuilder(_BaseHeaderASTBuilder[ScopeASTBuilder]):
    def __init__(self, context: BuildContext, resolver: ASTResolver, name: t.Optional[str] = None) -> None:
        super().__init__(context, resolver, name)
        self.__stmts = list[ast.stmt]()

    def __enter__(self) -> ScopeASTBuilder:
        self._context.enter_scope(self._name, [])
        return self._create_scope_builder()

    def __exit__(
        self,
        exc_type: t.Optional[type[BaseException]],
        exc_value: t.Optional[BaseException],
        exc_traceback: t.Optional[TracebackType],
    ) -> None:
        if exc_type is None:
            # 1. build statements using nested context
            stmts = self._resolver.stmts(*self._context.current_body)
            # 2. exit nested context
            self._context.leave_scope()
            # 3. fill statements to current chain
            self.__stmts.extend(stmts)

    @t.override
    def build(self) -> t.Sequence[ast.stmt]:
        return self.__stmts

    def _create_scope_builder(self) -> ScopeASTBuilder:
        return _BaseScopeBodyASTBuilder(self._context, self._resolver, self)


class WhileHeaderASTBuilder(_BaseHeaderASTBuilder[ScopeASTBuilder]):
    def __init__(self, context: BuildContext, resolver: ASTResolver, test: Expr) -> None:
        super().__init__(context, resolver)
        self.__test = test

    def build(self) -> t.Sequence[ast.stmt]:
        return [
            ast.While(
                test=self._resolver.expr(self.__test),
                body=list(self._context.current_body),
                orelse=[],
                lineno=0,
            ),
        ]

    def _create_scope_builder(self) -> _BaseScopeBodyASTBuilder:
        return _BaseScopeBodyASTBuilder(self._context, self._resolver, self)


class ForHeaderASTBuilder(_BaseHeaderASTBuilder[ScopeASTBuilder]):
    def __init__(self, context: BuildContext, resolver: ASTResolver, target: str, items: Expr) -> None:
        super().__init__(context, resolver)
        self.__target = target
        self.__items = items
        self.__is_async = False

    def async_(self, *, is_async: bool = True) -> t.Self:
        self.__is_async = is_async
        return self

    def build(self) -> t.Sequence[ast.stmt]:
        stmt = (
            ast.AsyncFor(
                target=ast.Name(id=self.__target),
                iter=self._resolver.expr(self.__items),
                body=list(self._context.current_body),
                orelse=[],
                lineno=0,
            )
            if self.__is_async
            else ast.For(
                target=ast.Name(id=self.__target),
                iter=self._resolver.expr(self.__items),
                body=list(self._context.current_body),
                orelse=[],
                lineno=0,
            )
        )

        return [stmt]

    def _create_scope_builder(self) -> _BaseScopeBodyASTBuilder:
        return _BaseScopeBodyASTBuilder(self._context, self._resolver, self)


class WithStatementASTBuilder(_BaseHeaderASTBuilder[ScopeASTBuilder]):
    def __init__(self, context: BuildContext, resolver: ASTResolver) -> None:
        super().__init__(context, resolver)
        self.__cms = list[Expr]()
        self.__names = list[t.Optional[str]]()
        self.__is_async = False

    def async_(self, *, is_async: bool = True) -> t.Self:
        self.__is_async = is_async
        return self

    def enter(self, cm: Expr, name: t.Optional[str] = None) -> t.Self:
        self.__cms.append(cm)
        self.__names.append(name)
        return self

    def build(self) -> t.Sequence[ast.stmt]:
        items = [
            ast.withitem(self._resolver.expr(cm), optional_vars=ast.Name(id=name) if name is not None else None)
            for cm, name in zip(self.__cms, self.__names)
        ]

        stmt = (
            ast.AsyncWith(
                items=items,
                body=list(self._context.current_body),
                lineno=0,
            )
            if self.__is_async
            else ast.With(
                items=items,
                body=list(self._context.current_body),
                lineno=0,
            )
        )

        return [stmt]

    def _create_scope_builder(self) -> _BaseScopeBodyASTBuilder:
        return _BaseScopeBodyASTBuilder(self._context, self._resolver, self)


class IfStatementASTBuilder(_BaseChainedASTBuilder):
    class _Body(_BaseChainPartASTBuilder):
        pass

    class _Else(_BaseChainPartASTBuilder):
        pass

    def __init__(self, context: BuildContext, resolver: ASTResolver, test: Expr) -> None:
        super().__init__(context, resolver)
        self.__test = test
        self.__body = self._Body(context, resolver)
        self.__else: t.Optional[IfStatementASTBuilder._Else] = None

    def body(self) -> t.ContextManager[ScopeASTBuilder]:
        return self.__body

    def else_(self) -> t.ContextManager[ScopeASTBuilder]:
        part = self._Else(self._context, self._resolver)
        self.__else = part
        return part

    def build(self) -> t.Sequence[ast.stmt]:
        return [
            ast.If(
                test=self._resolver.expr(self.__test),
                body=self._resolver.stmts(self.__body),
                orelse=self._resolver.stmts(self.__else) if self.__else is not None else [],
                lineno=0,
            ),
        ]


class TryStatementASTBuilder(_BaseChainedASTBuilder):
    class _Body(_BaseChainPartASTBuilder):
        pass

    class _Except(_BaseChainPartASTBuilder):
        def __init__(
            self,
            context: BuildContext,
            resolver: ASTResolver,
            types: t.Sequence[TypeRef],
            name: t.Optional[str],
        ) -> None:
            super().__init__(context, resolver)
            self.__types = types
            self.__name = name

        def handler(self) -> ast.ExceptHandler:
            base = _BaseASTBuilder(self._resolver)

            return ast.ExceptHandler(
                type=base.tuple_expr(*self.__types),
                name=self.__name,
                body=self._resolver.stmts(self, pass_if_empty=True),
            )

    class _Else(_BaseChainPartASTBuilder):
        pass

    class _Finally(_BaseChainPartASTBuilder):
        pass

    def __init__(self, context: BuildContext, resolver: ASTResolver) -> None:
        super().__init__(context, resolver)
        self.__body = self._Body(context, resolver)
        self.__excepts = list[TryStatementASTBuilder._Except]()
        self.__else: t.Optional[TryStatementASTBuilder._Else] = None
        self.__finally: t.Optional[TryStatementASTBuilder._Finally] = None

    def body(self) -> t.ContextManager[ScopeASTBuilder]:
        return self.__body

    def except_(self, *types: TypeRef, name: t.Optional[str] = None) -> t.ContextManager[ScopeASTBuilder]:
        part = self._Except(self._context, self._resolver, types, name)
        self.__excepts.append(part)
        return part

    def else_(self) -> t.ContextManager[ScopeASTBuilder]:
        part = self._Else(self._context, self._resolver)
        self.__else = part
        return part

    def finally_(self) -> t.ContextManager[ScopeASTBuilder]:
        part = self._Finally(self._context, self._resolver)
        self.__finally = part
        return part

    def build(self) -> t.Sequence[ast.stmt]:
        if not self.__excepts and self.__finally is None:
            raise RuntimeError("invalid try-except-finally block", self)

        return [
            ast.Try(
                body=self._resolver.stmts(self.__body),
                handlers=[part.handler() for part in self.__excepts],
                orelse=self._resolver.stmts(self.__else) if self.__else is not None else [],
                finalbody=self._resolver.stmts(self.__finally) if self.__finally is not None else [],
            ),
        ]


class ClassBodyASTBuilder(_BaseScopeBodyASTBuilder, TypeInfoProvider):
    def __init__(
        self,
        context: BuildContext,
        resolver: ASTResolver,
        signature: ClassHeaderASTBuilder,
    ) -> None:
        super().__init__(context, resolver, signature)
        self.__signature = signature

    @t.override
    def provide_type_info(self) -> TypeInfo:
        return self.__signature.provide_type_info()

    @t.override
    def ref(self) -> TypeRefBuilder:
        return self.__signature.ref()

    def method_def(self, name: str) -> MethodHeaderASTBuilder:
        return MethodHeaderASTBuilder(self._context, self._resolver, name)

    def init_def(self) -> MethodHeaderASTBuilder:
        return self.method_def("__init__").returns(self.const(None))

    @contextmanager
    def init_self_attrs_def(self, attrs: t.Mapping[str, TypeRef]) -> t.Iterator[MethodBodyASTBuilder]:
        init_def = self.init_def()

        for name, annotation in attrs.items():
            init_def.arg(name=name, annotation=annotation)

        with init_def as init_body:
            for name in attrs:
                init_body.assign_stmt(init_body.self_attr(name), init_body.attr(name))

            yield init_body

    def property_getter_def(self, name: str) -> FuncHeaderASTBuilder:
        return self.func_def(name).arg("self").decorators(get_predefs().property_ref)

    def property_setter_def(self, name: str) -> FuncHeaderASTBuilder:
        return self.func_def(name).arg("self").decorators(self.attr(name, "setter"))


class ClassHeaderASTBuilder(_BaseHeaderASTBuilder[ClassBodyASTBuilder], TypeInfoProvider):
    def __init__(self, context: BuildContext, resolver: ASTResolver, name: str) -> None:
        super().__init__(context, resolver, name)
        self.__info = TypeInfo.build(self._context.module, *self._context.namespace, name)
        self.__bases = list[TypeRef]()
        self.__decorators = list[TypeRef]()
        self.__keywords = dict[str, TypeRef]()
        self.__docs = list[str]()

    @t.override
    def provide_type_info(self) -> TypeInfo:
        return self.__info

    @t.override
    def ref(self) -> TypeRefBuilder:
        return TypeRefBuilder(self._resolver, self.__info)

    def docstring(self, value: t.Optional[str]) -> t.Self:
        if value:
            self.__docs.append(value)
        return self

    def abstract(self) -> t.Self:
        return self.keywords(metaclass=get_predefs().abc_meta_ref)

    def dataclass(self, *, frozen: bool = False, kw_only: bool = False) -> t.Self:
        return self.decorators(
            CallASTBuilder(self._resolver, get_predefs().dataclass_decorator_ref)
            .kwarg(
                "frozen",
                ast.Constant(value=frozen),
            )
            .kwarg(
                "kw_only",
                ast.Constant(value=kw_only),
            )
        )

    def inherits(self, *bases: t.Optional[TypeRef]) -> t.Self:
        self.__bases.extend(base for base in bases if base is not None)
        return self

    def decorators(self, *items: t.Optional[TypeRef]) -> t.Self:
        self.__decorators.extend(item for item in items if item is not None)
        return self

    def keywords(self, **keywords: t.Optional[TypeRef]) -> t.Self:
        self.__keywords.update({key: value for key, value in keywords.items() if value is not None})
        return self

    @t.override
    def build(self) -> t.Sequence[ast.stmt]:
        return (
            ast.ClassDef(
                name=self._context.name,
                bases=[self._resolver.expr(base) for base in self.__bases],
                keywords=[
                    ast.keyword(arg=key, value=self._resolver.expr(value)) for key, value in self.__keywords.items()
                ],
                body=self._resolver.stmts(*self._context.current_body, docs=self.__docs, pass_if_empty=True),
                decorator_list=self.__build_decorators(),
                type_params=[],
            ),
        )

    def _create_scope_builder(self) -> ClassBodyASTBuilder:
        return ClassBodyASTBuilder(self._context, self._resolver, self)

    def __build_decorators(self) -> list[ast.expr]:
        return [self._resolver.expr(dec) for dec in self.__decorators]


class _BaseFuncSignatureASTBuilder(_BaseHeaderASTBuilder[T_co]):
    def __init__(
        self,
        context: BuildContext,
        resolver: ASTResolver,
        name: str,
    ) -> None:
        super().__init__(context, resolver, name)
        self.__decorators = list[TypeRef]()
        self.__args = list[tuple[str, t.Optional[TypeRef]]]()
        self.__kwargs = dict[str, TypeRef]()
        self.__defaults = dict[str, Expr]()
        self.__returns: t.Optional[TypeRef] = None
        self.__is_async = False
        self.__is_abstract = False
        self.__is_override = False
        self.__iterator_cm = False
        self.__is_stub = False
        self.__is_not_implemented = False
        self.__docs = list[str]()

    def async_(self, *, is_async: bool = True) -> t.Self:
        self.__is_async = is_async
        return self

    def abstract(self) -> t.Self:
        self.__is_abstract = True
        return self

    def override(self) -> t.Self:
        self.__is_override = True
        return self

    def docstring(self, value: t.Optional[str]) -> t.Self:
        if value:
            self.__docs.append(value)
        return self

    def decorators(self, *items: t.Optional[TypeRef]) -> t.Self:
        self.__decorators.extend(item for item in items if item is not None)
        return self

    def arg(
        self,
        name: str,
        annotation: t.Optional[TypeRef] = None,
        default: t.Optional[Expr] = None,
    ) -> t.Self:
        self.__args.append((name, annotation))

        if default is not None:
            self.__defaults[name] = default

        return self

    def returns(self, ret: t.Optional[TypeRef]) -> t.Self:
        if ret is not None:
            self.__returns = ret
        return self

    def context_manager(self) -> t.Self:
        self.__iterator_cm = True
        return self

    def stub(self) -> t.Self:
        self.__is_stub = True
        return self

    def not_implemented(self) -> t.Self:
        self.__is_not_implemented = True
        return self

    @t.override
    def build(self) -> t.Sequence[ast.stmt]:
        node: ast.stmt

        if self.__is_async:
            node = ast.AsyncFunctionDef(  # type: ignore[call-overload,no-any-return,unused-ignore]
                # type_comment and type_params has default value each in 3.12 and not available in 3.9
                name=self._name,
                args=self.__build_args(),
                decorator_list=self.__build_decorators(),
                returns=self.__build_returns(),
                body=self.__build_body(),
                lineno=0,
            )

        else:
            node = ast.FunctionDef(  # type: ignore[call-overload,no-any-return,unused-ignore]
                # type_comment and type_params has default value each in 3.12 and not available in 3.9
                name=self._name,
                decorator_list=self.__build_decorators(),
                args=self.__build_args(),
                body=self.__build_body(),
                returns=self.__build_returns(),
                lineno=0,
            )

        return (node,)

    @t.override
    @abc.abstractmethod
    def _create_scope_builder(self) -> T_co:
        raise NotImplementedError

    def __build_decorators(self) -> list[ast.expr]:
        head_decorators: list[TypeRef] = []
        last_decorators: list[TypeRef] = []

        if self.__is_override:
            head_decorators.append(get_predefs().override_decorator_ref)

        if self.__is_abstract:
            last_decorators.append(get_predefs().abstractmethod_ref)

        if self.__iterator_cm:
            last_decorators.append(
                get_predefs().async_context_manager_decorator
                if self.__is_async
                else get_predefs().context_manager_decorator
            )

        return [self._resolver.expr(dec) for dec in chain(head_decorators, self.__decorators, last_decorators)]

    def __build_args(self) -> ast.arguments:
        return ast.arguments(
            posonlyargs=[],
            args=[
                ast.arg(
                    arg=arg,
                    annotation=self._resolver.expr(annotation) if annotation is not None else None,
                )
                for arg, annotation in self.__args
            ],
            defaults=[self._resolver.expr(self.__defaults[arg]) for arg, _ in self.__args if arg in self.__defaults],
            kwonlyargs=[
                ast.arg(
                    arg=arg,
                    annotation=self._resolver.expr(annotation) if annotation is not None else None,
                )
                for arg, annotation in self.__kwargs.items()
            ],
            kw_defaults=[self._resolver.expr(self.__defaults[arg]) for arg in self.__kwargs if arg in self.__defaults],
        )

    def __build_returns(self) -> t.Optional[ast.expr]:
        if self.__returns is None:
            return None

        ret = self._resolver.expr(self.__returns)
        if self.__iterator_cm:
            ret = _BaseASTBuilder(self._resolver).iterator_type(ret, is_async=self.__is_async)

        return ret

    def __build_body(self) -> list[ast.stmt]:
        body: t.Sequence[Stmt]

        if self.__is_stub:
            body = [ast.Expr(value=ast.Constant(value=...))]

        elif self.__is_not_implemented:
            body = [ast.Raise(exc=ast.Name(id="NotImplementedError"))]

        else:
            body = self._context.current_body

        return self._resolver.stmts(*body, docs=self.__docs, pass_if_empty=True)


class FuncBodyASTBuilder(_BaseScopeBodyASTBuilder):
    pass


class FuncHeaderASTBuilder(_BaseFuncSignatureASTBuilder[FuncBodyASTBuilder]):
    def _create_scope_builder(self) -> FuncBodyASTBuilder:
        return FuncBodyASTBuilder(self._context, self._resolver, self)


class MethodBodyASTBuilder(FuncBodyASTBuilder):
    def self_attr(self, head: str, *tail: str) -> AttrASTBuilder:
        return self.attr("self", f"__{head}", *tail)


class MethodHeaderASTBuilder(_BaseFuncSignatureASTBuilder[MethodBodyASTBuilder]):
    def __init__(self, context: BuildContext, resolver: ASTResolver, name: str) -> None:
        super().__init__(context, resolver, name)
        self.arg("self")

    def _create_scope_builder(self) -> MethodBodyASTBuilder:
        return MethodBodyASTBuilder(self._context, self._resolver, self)


class ModuleASTBuilder(ScopeASTBuilder):
    def __init__(self, context: BuildContext, resolver: ASTResolver, info: ModuleInfo, body: list[ast.stmt]) -> None:
        super().__init__(context, resolver)
        self.__info = info
        self.__body = body
        self.__docs = list[str]()

    def __enter__(self) -> t.Self:
        self._context.enter_module(self.__info, self.__body)
        return self

    def __exit__(
        self,
        exc_type: t.Optional[type[BaseException]],
        exc_value: t.Optional[BaseException],
        exc_traceback: t.Optional[TracebackType],
    ) -> None:
        if exc_type is None:
            scope = self._context.leave_module()
            assert scope.body is self.__body

    @property
    def info(self) -> ModuleInfo:
        return self.__info

    def docstring(self, value: t.Optional[str]) -> t.Self:
        if value:
            self.__docs.append(value)
        return self

    def import_stmt(self, info: ModuleInfo) -> ast.Import:
        return ast.Import(names=[ast.alias(name=info.qualname)])

    def build(self) -> ast.Module:
        return ast.Module(
            body=self._resolver.stmts(*self.__build_imports(), *self.__body, docs=self.__docs),
            type_ignores=[],
        )

    def __build_imports(self) -> t.Sequence[ast.stmt]:
        return [
            self.import_stmt(dep)
            for dep in sorted(self._context.get_dependencies(self.__info), key=self.__get_dep_sort_key)
        ]

    def __get_dep_sort_key(self, info: ModuleInfo) -> str:
        return info.qualname


class PackageASTBuilder:
    def __init__(
        self,
        context: BuildContext,
        resolver: ASTResolver,
        info: PackageInfo,
        modules: dict[ModuleInfo, ModuleASTBuilder],
    ) -> None:
        self.__context = context
        self.__resolver = resolver
        self.__info = info
        self.__modules = modules

    def __enter__(self) -> t.Self:
        self.__context.enter_package(self.__info)
        return self

    def __exit__(
        self,
        exc_type: t.Optional[type[BaseException]],
        exc_value: t.Optional[BaseException],
        exc_traceback: t.Optional[TracebackType],
    ) -> None:
        if exc_type is not None:
            return

        self.__context.leave_package()

    @property
    def info(self) -> PackageInfo:
        return self.__info

    def sub(self, name: str) -> t.Self:
        return self.__class__(self.__context, self.__resolver, PackageInfo(self.__info, name), self.__modules)

    def init(self) -> ModuleASTBuilder:
        return self.module("__init__")

    def module(self, name: str) -> ModuleASTBuilder:
        info = ModuleInfo(self.__info, name)

        builder = self.__modules.get(info)
        if builder is None:
            builder = self.__modules[info] = ModuleASTBuilder(self.__context, self.__resolver, info, [])

        return builder

    def build(self) -> t.Mapping[ModuleInfo, ast.Module]:
        return {
            info: builder.build()
            for info, builder in self.__modules.items()
            if info.qualname.startswith(self.__info.qualname)
        }


def package(info: t.Union[str, PackageInfo], parent: t.Optional[PackageInfo] = None) -> PackageASTBuilder:
    pkg_info = info if isinstance(info, PackageInfo) else PackageInfo(parent, info)
    context = BuildContext([], defaultdict(set), deque())
    resolver = ASTResolver(context)
    return PackageASTBuilder(context, resolver, pkg_info, {})


def module(info: t.Union[str, ModuleInfo], parent: t.Optional[PackageInfo] = None) -> ModuleASTBuilder:
    mod_info = info if isinstance(info, ModuleInfo) else ModuleInfo(parent, info)
    context = BuildContext([], defaultdict(set), deque())
    resolver = ASTResolver(context)
    return ModuleASTBuilder(context, resolver, mod_info, [])


def render(node: t.Union[ast.Module, ModuleASTBuilder]) -> str:
    if isinstance(node, ast.Module):
        clean_node = node

    elif isinstance(node, ModuleASTBuilder):
        clean_node = node.build()

    else:
        t.assert_never(node)

    return ast.unparse(clean_node)
