import abc
import ast
import typing as t
from collections import deque
from contextlib import contextmanager
from dataclasses import dataclass
from functools import cache, cached_property
from itertools import chain

from pyprotostuben.python.info import ModuleInfo, PackageInfo, TypeInfo


class ASTBuilder(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def build(self) -> ast.AST:
        raise NotImplementedError


class ExpressionASTBuilder(ASTBuilder, metaclass=abc.ABCMeta):
    @t.override
    @abc.abstractmethod
    def build(self) -> ast.expr:
        raise NotImplementedError


class StatementASTBuilder(ASTBuilder, metaclass=abc.ABCMeta):
    @t.override
    @abc.abstractmethod
    def build(self) -> ast.stmt:
        raise NotImplementedError


class Referencable(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def ref(self) -> ExpressionASTBuilder:
        raise NotImplementedError


Expr = t.Union[ast.expr, ExpressionASTBuilder]
Stmt = t.Union[ast.stmt, StatementASTBuilder, Expr]


TypeRef = t.Union[Expr, type[object], TypeInfo, Referencable]


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


@dataclass()
class BuildContext:
    packages: t.MutableSequence[PackageInfo]
    dependencies: t.MutableSet[ModuleInfo]
    scopes: t.MutableSequence[Scope]
    _module: t.Optional[ModuleInfo] = None

    @property
    def module(self) -> ModuleInfo:
        assert self._module is not None
        return self._module

    def enter_package(self, info: PackageInfo) -> t.Self:
        assert self._module is None
        self.packages.append(info)
        return self

    def leave_package(self) -> t.Self:
        assert self._module is None
        self.packages.pop()
        return self

    def enter_module(self, info: ModuleInfo, body: t.MutableSequence[ast.stmt]) -> Scope:
        assert self._module is None
        assert len(self.scopes) == 0
        self._module = info
        return self.enter_scope(None, body)

    def leave_module(self) -> Scope:
        assert len(self.scopes) == 1
        scope = self.leave_scope()
        self._module = None
        self.dependencies.clear()
        return scope

    def enter_scope(self, name: t.Optional[str], body: t.MutableSequence[ast.stmt]) -> Scope:
        scope = Scope(name, body)
        self.scopes.append(scope)
        return scope

    def leave_scope(self) -> Scope:
        scope = self.scopes.pop()
        return scope

    @property
    def namespace(self) -> t.Sequence[str]:
        return tuple(scope.name for scope in self.scopes if scope.name is not None)

    @property
    def current_scope(self) -> Scope:
        return self.scopes[-1]

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

    def expr(self, ref: TypeRef) -> ast.expr:
        if isinstance(ref, Referencable):
            ref = ref.ref()

        if isinstance(ref, ExpressionASTBuilder):
            ref = ref.build()

        if isinstance(ref, ast.expr):
            return ref

        if isinstance(ref, type):
            ref = TypeInfo.from_type(ref)

        if ref.module is not None and ref.module != self.__context.module:
            self.__context.dependencies.add(ref.module)

        else:
            ref = TypeInfo(None, ref.ns)

        head, *tail = (*(ref.module.parts if ref.module is not None else ()), *ref.ns)

        expr: ast.expr = ast.Name(id=head)
        for attr in tail:
            expr = ast.Attribute(attr=attr, value=expr)

        return expr

    def stmts(self, *stmts: Stmt, docs: t.Optional[t.Sequence[str]] = None) -> list[ast.stmt]:
        body = [
            stmt
            if isinstance(stmt, ast.stmt)
            else stmt.build()
            if isinstance(stmt, StatementASTBuilder)
            else ast.Expr(value=self.expr(stmt))
            for stmt in stmts
        ]

        if docs:
            body.insert(0, ast.Expr(value=ast.Constant(value="\n".join(docs))))

        if not body:
            body.append(ast.Pass())

        return body


class TypeRefBuilder(ExpressionASTBuilder):
    def __init__(self, resolver: ASTResolver, info: TypeInfo) -> None:
        self.__resolver = resolver
        self.__info = info
        self.__wraps: t.Callable[[TypeInfo], ast.expr] = self.__resolver.expr
        self.__base = BaseASTBuilder(resolver)

    def optional(self) -> "TypeRefBuilder":
        inner = self.__wraps

        def wrap(info: TypeInfo) -> ast.expr:
            return self.__base.optional_type(inner(info))

        self.__wraps = wrap

        return self

    def list(self) -> "TypeRefBuilder":
        inner = self.__wraps

        def wrap(info: TypeInfo) -> ast.expr:
            return self.__base.generic_type(list, inner(info))

        self.__wraps = wrap

        return self

    def context_manager(self, is_async: bool = False) -> "TypeRefBuilder":
        inner = self.__wraps

        def wrap(info: TypeInfo) -> ast.expr:
            return self.__base.context_manager_type(inner(info), is_async=is_async)

        self.__wraps = wrap

        return self

    def attr(self, *tail: str) -> "AttrASTBuilder":
        return AttrASTBuilder(self.__resolver, self).attr(*tail)

    def init(
        self,
        args: t.Optional[t.Sequence[Expr]] = None,
        kwargs: t.Optional[t.Mapping[str, Expr]] = None,
    ) -> "CallASTBuilder":
        return self.attr().call(args, kwargs)

    @t.override
    def build(self) -> ast.expr:
        return self.__wraps(self.__info)


class AttrASTBuilder(ExpressionASTBuilder):
    def __init__(self, resolver: ASTResolver, node: t.Union[str, TypeRef]) -> None:
        self.__resolver = resolver
        self.__head = node
        self.__parts = list[str]()

    @property
    def parts(self) -> t.Sequence[str]:
        if isinstance(self.__head, str):
            return self.__head, *self.__parts

        queue = deque([self.__head])
        parts = list[str]()

        while queue:
            item = queue.pop()

            if isinstance(item, ast.Attribute):
                queue.append(item.value)
                parts.append(item.attr)

            elif isinstance(item, ast.Name):
                parts.append(item.id)

        return *reversed(parts), *self.__parts

    def attr(self, *tail: str) -> t.Self:
        self.__parts.extend(tail)
        return self

    def call(
        self,
        args: t.Optional[t.Sequence[Expr]] = None,
        kwargs: t.Optional[t.Mapping[str, Expr]] = None,
    ) -> "CallASTBuilder":
        builder = CallASTBuilder(
            resolver=self.__resolver,
            func=self,
        )

        for arg in args or ():
            builder.arg(arg)

        for name, kwarg in (kwargs or {}).items():
            builder.kwarg(name, kwarg)

        return builder

    @t.override
    def build(self) -> ast.expr:
        expr: ast.expr = ast.Name(id=self.__head) if isinstance(self.__head, str) else self.__resolver.expr(self.__head)

        for part in self.__parts:
            expr = ast.Attribute(attr=part, value=expr)

        return expr


class CallASTBuilder(ExpressionASTBuilder):
    def __init__(self, resolver: ASTResolver, func: TypeRef) -> None:
        self.__resolver = resolver
        self.__func = func
        self.__args = list[Expr]()
        self.__kwargs = dict[str, Expr]()

    def arg(self, expr: Expr) -> t.Self:
        self.__args.append(self.__resolver.expr(expr))
        return self

    def kwarg(self, name: str, expr: Expr) -> t.Self:
        self.__kwargs[name] = expr
        return self

    def build(self) -> ast.expr:
        return ast.Call(
            func=self.__resolver.expr(self.__func),
            args=[self.__resolver.expr(arg) for arg in self.__args],
            keywords=[ast.keyword(arg=key, value=self.__resolver.expr(kwarg)) for key, kwarg in self.__kwargs.items()],
            lineno=0,
        )


class BaseASTBuilder:
    def __init__(self, resolver: ASTResolver) -> None:
        self._resolver = resolver

    def const(self, value: object) -> ast.expr:
        assert not isinstance(value, ast.AST)
        return ast.Constant(value=value)

    def attr(self, head: t.Union[str, TypeRef], *tail: str) -> AttrASTBuilder:
        return AttrASTBuilder(self._resolver, head).attr(*tail)

    def call(
        self,
        func: TypeRef,
        args: t.Optional[t.Sequence[Expr]] = None,
        kwargs: t.Optional[t.Mapping[str, Expr]] = None,
    ) -> CallASTBuilder:
        return self.attr(func).call(args, kwargs)

    def generic_type(self, generic: TypeRef, *args: TypeRef) -> ast.expr:
        if len(args) == 0:
            return self._expr(generic)

        if len(args) == 1:
            return ast.Subscript(
                value=self._expr(generic),
                slice=self._expr(args[0]),
            )

        return ast.Subscript(
            value=self._expr(generic),
            slice=ast.Tuple(
                elts=[self._expr(arg) for arg in args],
            ),
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

    def _stmt(self, stmt: Stmt) -> t.Sequence[ast.stmt]:
        return self._resolver.stmts(stmt)


class ScopeASTBuilder(BaseASTBuilder):
    def __init__(self, context: BuildContext, resolver: ASTResolver) -> None:
        super().__init__(resolver)
        self.__context = context
        self.__docs = list[str]()

    def class_def(self, name: str) -> "ClassHeadASTBuilder":
        return ClassHeadASTBuilder(self.__context, self._resolver, name)

    def dataclass_def(self, name: str, frozen: bool = False, kw_only: bool = False) -> "ClassHeadASTBuilder":
        return self.class_def(name).decorators(
            self.call(
                func=get_predefs().dataclass_decorator_ref,
                kwargs={
                    "frozen": self.const(value=frozen),
                    "kw_only": self.const(value=kw_only),
                },
            )
        )

    def func_def(self, name: str) -> "FuncHeadASTBuilder":
        return FuncHeadASTBuilder(self.__context, self._resolver, name)

    def field_def(self, name: str, annotation: TypeRef) -> ast.stmt:
        node = ast.AnnAssign(
            target=ast.Name(id=name),
            annotation=self._expr(annotation),
            value=None,
            simple=1,
        )
        self.__context.append_body(node)

        return node

    def type_ref(self, base: t.Union[type[object], TypeInfo]) -> TypeRefBuilder:
        return TypeRefBuilder(self._resolver, base if isinstance(base, TypeInfo) else TypeInfo.from_type(base))

    def assign_stmt(self, target: t.Union[str, Expr], value: Expr) -> ast.stmt:
        node = ast.Assign(
            targets=[self._expr(self.attr(target))],
            value=self._expr(value),
            type_comment=None,
            lineno=0,
        )
        self.__context.append_body(node)

        return node

    def return_stmt(self, value: Expr) -> ast.stmt:
        node = ast.Return(
            value=self._expr(value),
            lineno=0,
        )
        self.__context.append_body(node)

        return node

    def yield_stmt(self, value: Expr) -> ast.stmt:
        node = ast.Expr(
            value=ast.Yield(
                value=self._expr(value),
                lineno=0,
            ),
        )
        self.__context.append_body(node)

        return node


class ClassHeadASTBuilder(StatementASTBuilder):
    def __init__(self, context: BuildContext, resolver: ASTResolver, name: str) -> None:
        self.__context = context
        self.__resolver = resolver
        self.__name = name
        self.__bases = list[TypeRef]()
        self.__decorators = list[TypeRef]()
        self.__keywords = dict[str, TypeRef]()
        self.__docs = list[str]()

    def __enter__(self) -> "ClassScopeASTBuilder":
        self.__context.enter_scope(self.__name, [])
        return ClassScopeASTBuilder(self.__context, self.__resolver)

    def __exit__(self, *_: object) -> None:
        stmts = self.__resolver.stmts(self)

        self.__context.leave_scope()
        self.__context.extend_body(stmts)

    def docstring(self, value: str) -> t.Self:
        self.__docs.append(value)
        return self

    def abstract(self) -> t.Self:
        return self.keywords(metaclass=get_predefs().abc_meta_ref)

    def dataclass(self, frozen: bool = False, kw_only: bool = False) -> t.Self:
        return self.decorators(
            CallASTBuilder(self.__resolver, get_predefs().dataclass_decorator_ref)
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
    def build(self) -> ast.stmt:
        return ast.ClassDef(
            name=self.__name,
            bases=[self.__resolver.expr(base) for base in self.__bases],
            keywords=[
                ast.keyword(arg=key, value=self.__resolver.expr(value)) for key, value in self.__keywords.items()
            ],
            body=self.__resolver.stmts(*self.__context.current_body, docs=self.__docs),
            decorator_list=self.__build_decorators(),
            type_params=[],
        )

    def __build_decorators(self) -> list[ast.expr]:
        return [self.__resolver.expr(dec) for dec in self.__decorators]


class ClassScopeASTBuilder(ScopeASTBuilder, Referencable):
    def __init__(self, context: BuildContext, resolver: ASTResolver) -> None:
        super().__init__(context, resolver)
        self.__info = TypeInfo(context.module, context.namespace)

    @t.override
    def ref(self) -> TypeRefBuilder:
        return TypeRefBuilder(self._resolver, self.__info)

    def method_def(self, name: str) -> "FuncHeadASTBuilder":
        return self.func_def(name).pos_arg("self")

    def init_def(self) -> "FuncHeadASTBuilder":
        return self.method_def("__init__").returns(self.const(None))

    @contextmanager
    def init_self_attrs_def(self, attrs: t.Mapping[str, TypeRef]) -> t.Iterator[ScopeASTBuilder]:
        init = self.init_def()

        for name, value in attrs.items():
            init.pos_arg(name=name, annotation=value)

        with init as init_body:
            for name, value in attrs.items():
                init_body.assign_stmt(init_body.attr("self", f"__{name}"), value=init_body.attr(name))

            yield init_body

    def self_attr(self, head: str, *tail: str) -> AttrASTBuilder:
        return self.attr("self", f"__{head}", *tail)

    def property_getter_def(self, name: str) -> "FuncHeadASTBuilder":
        return self.func_def(name).pos_arg("self").decorators(get_predefs().property_ref)

    def property_setter_def(self, name: str) -> "FuncHeadASTBuilder":
        return self.func_def(name).pos_arg("self").decorators(self.attr(name, "setter"))


class FuncHeadASTBuilder(StatementASTBuilder):
    def __init__(
        self,
        context: BuildContext,
        resolver: ASTResolver,
        name: str,
    ) -> None:
        self.__context = context
        self.__resolver = resolver
        self.__name = name
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

    def __enter__(self) -> ScopeASTBuilder:
        self.__context.enter_scope(self.__name, [])
        return ScopeASTBuilder(self.__context, self.__resolver)

    def __exit__(self, *_: object) -> None:
        stmts = self.__resolver.stmts(self)

        self.__context.leave_scope()
        self.__context.extend_body(stmts)

    def async_(self) -> t.Self:
        self.__is_async = True
        return self

    def abstract(self) -> t.Self:
        self.__is_abstract = True
        return self

    def override(self) -> t.Self:
        self.__is_override = True
        return self

    def docstring(self, value: str) -> t.Self:
        self.__docs.append(value)
        return self

    def decorators(self, *items: t.Optional[TypeRef]) -> t.Self:
        self.__decorators.extend(item for item in items if item is not None)
        return self

    def pos_arg(
        self,
        name: str,
        annotation: t.Optional[TypeRef] = None,
        default: t.Optional[Expr] = None,
    ) -> t.Self:
        self.__args.append((name, annotation))

        if default is not None:
            self.__defaults[name] = default

        return self

    def returns(self, ret: TypeRef) -> t.Self:
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

    def build(self) -> ast.stmt:
        if self.__is_async:
            return ast.AsyncFunctionDef(  # type: ignore[call-overload,no-any-return,unused-ignore]
                # type_comment and type_params has default value each in 3.12 and not available in 3.9
                name=self.__name,
                args=self.__build_args(),
                decorator_list=self.__build_decorators(),
                returns=self.__build_returns(),
                body=self.__build_body(),
                lineno=0,
            )

        return ast.FunctionDef(  # type: ignore[call-overload,no-any-return,unused-ignore]
            # type_comment and type_params has default value each in 3.12 and not available in 3.9
            name=self.__name,
            decorator_list=self.__build_decorators(),
            args=self.__build_args(),
            body=self.__build_body(),
            returns=self.__build_returns(),
            lineno=0,
        )

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

        return [self.__resolver.expr(dec) for dec in chain(head_decorators, self.__decorators, last_decorators)]

    def __build_args(self) -> ast.arguments:
        return ast.arguments(
            posonlyargs=[],
            args=[
                ast.arg(
                    arg=arg,
                    annotation=self.__resolver.expr(annotation) if annotation is not None else None,
                )
                for arg, annotation in self.__args
            ],
            defaults=[self.__resolver.expr(self.__defaults[arg]) for arg, _ in self.__args if arg in self.__defaults],
            kwonlyargs=[
                ast.arg(
                    arg=arg,
                    annotation=self.__resolver.expr(annotation) if annotation is not None else None,
                )
                for arg, annotation in self.__kwargs.items()
            ],
            kw_defaults=[self.__resolver.expr(self.__defaults[arg]) for arg in self.__kwargs if arg in self.__defaults],
        )

    def __build_returns(self) -> t.Optional[ast.expr]:
        if self.__returns is None:
            return None

        ret = self.__resolver.expr(self.__returns)
        if self.__iterator_cm:
            ret = BaseASTBuilder(self.__resolver).iterator_type(ret, is_async=self.__is_async)

        return ret

    def __build_body(self) -> list[ast.stmt]:
        body: t.Sequence[Stmt]

        if self.__is_stub:
            body = [ast.Expr(value=ast.Constant(value=...))]

        elif self.__is_not_implemented:
            body = [ast.Raise(exc=ast.Name(id="NotImplementedError"))]

        else:
            body = self.__context.current_body

        return self.__resolver.stmts(*body, docs=self.__docs)


class ModuleASTBuilder(ScopeASTBuilder, ASTBuilder):
    def __init__(self, context: BuildContext, resolver: ASTResolver, info: ModuleInfo, body: list[ast.stmt]) -> None:
        super().__init__(context, resolver)
        self.__context = context
        self.__resolver = resolver
        self.__info = info
        self.__body = body
        self.__docs = list[str]()

    def __enter__(self) -> t.Self:
        self.__context.enter_module(self.__info, self.__body)
        return self

    def __exit__(self, *_: object) -> None:
        scope = self.__context.leave_module()
        assert scope.body is self.__body

    @property
    def info(self) -> ModuleInfo:
        return self.__info

    def docstring(self, value: str) -> t.Self:
        self.__docs.append(value)
        return self

    def import_stmt(self, info: ModuleInfo) -> ast.Import:
        return ast.Import(names=[ast.alias(name=info.qualname)])

    @t.override
    def build(self) -> ast.AST:
        return ast.Module(
            body=[
                *(self.import_stmt(dep) for dep in sorted(self.__context.dependencies, key=self.__get_dep_sort_key)),
                *self.__resolver.stmts(*self.__body, docs=self.__docs),
            ],
            type_ignores=[],
        )

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

    def __exit__(self, *_: object) -> None:
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
            builder = ModuleASTBuilder(self.__context, self.__resolver, info, [])

        return builder

    def build(self) -> t.Mapping[ModuleInfo, ast.AST]:
        return {
            info: builder.build()
            for info, builder in self.__modules.items()
            if info.qualname.startswith(self.__info.qualname)
        }


def package(info: t.Union[str, PackageInfo], parent: t.Optional[PackageInfo] = None) -> PackageASTBuilder:
    pkg_info = info if isinstance(info, PackageInfo) else PackageInfo(parent, info)
    context = BuildContext([pkg_info], set(), deque())
    resolver = ASTResolver(context)
    return PackageASTBuilder(context, resolver, pkg_info, {})


def module(info: t.Union[str, ModuleInfo], parent: t.Optional[PackageInfo] = None) -> ModuleASTBuilder:
    mod_info = info if isinstance(info, ModuleInfo) else ModuleInfo(parent, info)
    context = BuildContext([], set(), deque())
    resolver = ASTResolver(context)
    return ModuleASTBuilder(context, resolver, mod_info, [])


def render(node: t.Union[ast.AST, ASTBuilder]) -> str:
    if isinstance(node, ast.AST):
        clean_node = node

    elif isinstance(node, ASTBuilder):
        clean_node = node.build()

    else:
        t.assert_never(node)

    return ast.unparse(clean_node)


def main1() -> None:
    with package("simple") as pkg:
        with pkg.module("foo") as foo:
            with foo.class_def("Foo") as foo_class:
                with (
                    foo_class.method_def("do_stuff")
                    .pos_arg("spam", str)
                    .returns(foo.type_ref(str).context_manager())
                    .abstract()
                    .not_implemented()
                ):
                    pass

            print(foo.info)
            print(render(foo))

        with pkg.module("bar") as bar:
            with bar.class_def("Bar").inherits(foo_class) as _:
                with _.method_def("do_stuff").pos_arg("spam", str).returns(str).context_manager().override().stub():
                    pass

            print(bar.info)
            print(render(bar))


def main() -> None:
    with module("simple") as _:
        with _.class_def("Foo") as foo:
            with _.dataclass_def("Bar") as bar:
                _.field_def("spam", int)

            _.field_def("bars", bar.ref().list().optional())

            with foo.init_self_attrs_def({"my_bar": bar}):
                pass

            with foo.method_def("do_stuff").pos_arg("x", int).returns(str):
                _.assign_stmt("y", _.call(str, [_.attr("x")]))
                _.assign_stmt(_.attr("self", "__some"), bar.ref().init().kwarg("x", _.attr("x")))
                _.return_stmt(_.attr("y").attr("__str__").call())

            with foo.method_def("do_buzz").abstract().returns(object).stub():
                pass

        print(ast.unparse(_.build()))


if __name__ == "__main__":
    main()
