import ast
import typing as t
from collections import deque
from functools import cache, cached_property

from pyprotostuben.python.info import ModuleInfo, TypeInfo

TypeRef = t.Union[ast.expr, type[object], TypeInfo, "TypeRefBuilder"]


def main() -> None:
    with ModBuilder.create(ModuleInfo(None, "simple")) as _:
        with _.class_def("Foo") as foo:
            with _.dataclass_def("Bar") as bar:
                _.field_def("spam", int)

            _.field_def("bars", bar.ref().list().optional())

            foo.init_attrs_def({"my_bar": bar.ref()})

            with foo.method_def("do_stuff").pos_arg("x", int).returns(str):
                _.assign_stmt("y", _.call(str, [_.attr("x")]))
                _.return_stmt(_.attr("y"))

            foo.abstract_method_def("do_buzz").returns(object).stub()

        print(ast.unparse(_.build()))


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


class ScopeStack:
    def __init__(self, info: ModuleInfo) -> None:
        self.__info = info
        self.__names = list[t.Optional[str]]()
        self.__scopes = deque[list[ast.stmt]]([])

    @property
    def module(self) -> ModuleInfo:
        return self.__info

    def enter(self, name: t.Optional[str], body: list[ast.stmt]) -> list[ast.stmt]:
        self.__names.append(name)
        self.__scopes.append(body)
        return body

    def leave(self) -> list[ast.stmt]:
        self.__names.pop()
        body = self.__scopes.pop()
        return body

    @property
    def namespace(self) -> t.Sequence[str]:
        return tuple(name for name in self.__names if name is not None)

    @property
    def current(self) -> t.MutableSequence[ast.stmt]:
        return self.__scopes[-1]

    def append(self, stmt: t.Optional[ast.stmt]) -> None:
        if stmt is not None:
            self.current.append(stmt)

    def extend(self, *stmts: t.Optional[ast.stmt]) -> None:
        self.current.extend(stmt for stmt in stmts if stmt is not None)


class TypeRefResolver:
    def __init__(self, scopes: ScopeStack) -> None:
        self.__scopes = scopes
        self.__deps = set[ModuleInfo]()

    def resolve(self, ref: TypeRef) -> ast.expr:
        if isinstance(ref, ast.expr):
            return ref

        if isinstance(ref, TypeRefBuilder):
            return ref.build()

        if isinstance(ref, type):
            ref = TypeInfo.from_type(ref)

        if ref.module != self.__scopes.module and ref.module is not None:
            self.__deps.add(ref.module)

        else:
            ref = TypeInfo(None, ref.ns)

        return _build_attr_expr(*(ref.module.parts if ref.module is not None else ()), *ref.ns)

    @property
    def dependencies(self) -> t.Sequence[ModuleInfo]:
        return sorted(self.__deps, key=self.__get_dep_sort_key)

    def __get_dep_sort_key(self, module: ModuleInfo) -> str:
        return module.qualname


class BaseASTBuilder:
    def __init__(self, resolver: TypeRefResolver) -> None:
        self.__resolver = resolver

    @property
    def predefs(self) -> Predefs:
        return get_predefs()

    def resolve(self, ref: TypeRef) -> ast.expr:
        return self.__resolver.resolve(ref)

    def attr(self, head: t.Union[str, ast.expr], *tail: str) -> ast.expr:
        return _build_attr_expr(head, *tail)

    def const(self, value: object) -> ast.expr:
        return ast.Constant(value=value)

    def call(
        self,
        func: TypeRef,
        args: t.Optional[t.Sequence[ast.expr]] = None,
        kwargs: t.Optional[t.Mapping[str, ast.expr]] = None,
    ) -> ast.expr:
        return ast.Call(
            func=self.resolve(func),
            args=list(args or ()),
            keywords=[ast.keyword(arg=key, value=value) for key, value in (kwargs or {}).items()],
            lineno=0,
        )

    def generic_type(self, generic: TypeRef, *args: TypeRef) -> ast.expr:
        if len(args) == 0:
            return self.resolve(generic)

        if len(args) == 1:
            return ast.Subscript(value=self.resolve(generic), slice=self.resolve(args[0]))

        return ast.Subscript(value=self.resolve(generic), slice=ast.Tuple(elts=[self.resolve(arg) for arg in args]))

    def optional_type(self, of_type: TypeRef) -> ast.expr:
        return self.generic_type(self.predefs.optional_ref, of_type)

    def sequence_type(self, of_type: TypeRef, *, mutable: bool = False) -> ast.expr:
        return self.generic_type(self.predefs.mutable_sequence_ref if mutable else self.predefs.sequence_ref, of_type)

    def ellipsis_stmt(self) -> ast.stmt:
        return ast.Expr(value=ast.Constant(value=...))

    def pass_stmt(self) -> ast.stmt:
        return ast.Pass()


class TypeRefBuilder:
    def __init__(self, resolver: TypeRefResolver, info: TypeInfo) -> None:
        self.__impl = BaseASTBuilder(resolver)
        self.__info = info
        self.__wraps: t.Callable[[TypeInfo], ast.expr] = self.__impl.resolve

    def optional(self) -> "TypeRefBuilder":
        inner = self.__wraps

        def wrap(info: TypeInfo) -> ast.expr:
            return self.__impl.optional_type(inner(info))

        self.__wraps = wrap

        return self

    def list(self) -> "TypeRefBuilder":
        inner = self.__wraps

        def wrap(info: TypeInfo) -> ast.expr:
            return self.__impl.generic_type(list, inner(info))

        self.__wraps = wrap

        return self

    def build(self) -> ast.expr:
        return self.__wraps(self.__info)


class BodyASTBuilder(BaseASTBuilder):
    def __init__(
        self,
        scopes: ScopeStack,
        resolver: TypeRefResolver,
        name: t.Optional[str],
        body: list[ast.stmt],
    ) -> None:
        super().__init__(resolver)
        self.__scopes = scopes
        self.__resolver = resolver
        self.__name = name
        self.__body = body

    def ref(self) -> TypeRefBuilder:
        return TypeRefBuilder(self.__resolver, TypeInfo.build(self.__scopes.module, self.__name))

    def docstring(self, value: str) -> t.Self:
        self.__doc = value
        self.__body.insert(0, ast.Expr(value=ast.Constant(value=value)))
        return self

    def class_def(
        self,
        name: str,
        bases: t.Optional[t.Sequence[TypeRef]] = None,
    ) -> "ClassHeadASTBuilder":
        node = ast.ClassDef(
            name=name,
            bases=[self.resolve(base) for base in (bases or ())],
            keywords=[],
            body=[],
            decorator_list=[],
            type_params=[],
        )
        self.__scopes.append(node)

        return ClassHeadASTBuilder(self.__scopes, self.__resolver, node)

    def dataclass_def(self, name: str, frozen: bool = False, kw_only: bool = False) -> "ClassHeadASTBuilder":
        return self.class_def(name).decorators(
            self.call(
                func=self.predefs.dataclass_decorator_ref,
                kwargs={
                    "frozen": self.const(value=frozen),
                    "kw_only": self.const(value=kw_only),
                },
            )
        )

    def func_def(self, name: str) -> "FuncASTBuilder":
        node = ast.FunctionDef(
            name=name,
            args=ast.arguments(
                posonlyargs=[],
                args=[],
                defaults=[],
                kwonlyargs=[],
                kw_defaults=[],
            ),
            returns=None,
            decorator_list=[],
            body=[],
            type_params=[],
            lineno=0,
        )
        self.__scopes.append(node)

        return FuncASTBuilder(self.__scopes, self.__resolver, node)

    def async_func_def(self, name: str) -> "FuncASTBuilder":
        node = ast.AsyncFunctionDef(
            name=name,
            args=ast.arguments(
                posonlyargs=[],
                args=[],
                defaults=[],
                kwonlyargs=[],
                kw_defaults=[],
            ),
            returns=None,
            decorator_list=[],
            body=[],
            type_params=[],
            lineno=0,
        )
        self.__scopes.append(node)

        return FuncASTBuilder(self.__scopes, self.__resolver, node)

    def field_def(self, name: str, annotation: TypeRef) -> ast.stmt:
        node = ast.AnnAssign(
            target=ast.Name(id=name),
            annotation=self.resolve(annotation),
            value=None,
            simple=1,
        )
        self.__scopes.append(node)

        return node

    def assign_stmt(self, target: t.Union[str, ast.expr], value: ast.expr) -> ast.stmt:
        node = ast.Assign(
            targets=[ast.Name(id=target) if isinstance(target, str) else target],
            value=value,
            type_comment=None,
            lineno=0,
        )
        self.__scopes.append(node)

        return node

    def return_stmt(self, value: ast.expr) -> ast.stmt:
        node = ast.Return(
            value=value,
            lineno=0,
        )
        self.__scopes.append(node)

        return node

    def yield_stmt(self, value: ast.expr) -> ast.stmt:
        node = ast.Expr(
            value=ast.Yield(
                value=value,
                lineno=0,
            ),
        )
        self.__scopes.append(node)

        return node


class ClassHeadASTBuilder:
    def __init__(self, scopes: ScopeStack, resolver: TypeRefResolver, node: ast.ClassDef) -> None:
        self.__scopes = scopes
        self.__resolver = resolver
        self.__node = node

    def inherits(self, *bases: t.Optional[TypeRef]) -> t.Self:
        self.__node.bases.extend(self.__resolver.resolve(base) for base in bases if base is not None)
        return self

    def decorators(self, *items: t.Optional[TypeRef]) -> t.Self:
        self.__node.decorator_list.extend(self.__resolver.resolve(item) for item in items if item is not None)
        return self

    def __enter__(self) -> "ClassBodyASTBuilder":
        self.__scopes.enter(self.__node.name, self.__node.body)
        return ClassBodyASTBuilder(self.__scopes, self.__resolver, self.__node)

    def __exit__(self, *_: object) -> None:
        body = self.__scopes.leave()
        assert body is self.__node.body


class ClassBodyASTBuilder(BodyASTBuilder):
    def __init__(self, scopes: ScopeStack, resolver: TypeRefResolver, node: ast.ClassDef) -> None:
        super().__init__(scopes, resolver, node.name, node.body)
        self.__node = node

    def inherits(self, *bases: t.Optional[TypeRef]) -> t.Self:
        self.__node.bases.extend(self.resolve(base) for base in bases if base is not None)
        return self

    def decorators(self, *items: t.Optional[TypeRef]) -> t.Self:
        self.__node.decorator_list.extend(self.resolve(item) for item in items if item is not None)
        return self

    def init_def(self) -> "FuncASTBuilder":
        return self.func_def("__init__").pos_arg("self").returns(self.const(None))

    def init_attrs_def(self, attrs: t.Mapping[str, TypeRef]) -> "FuncASTBuilder":
        init = self.init_def()

        for name, value in attrs.items():
            init.pos_arg(name=name, annotation=value)

        with init as init_body:
            for name, value in attrs.items():
                init_body.assign_stmt(init_body.attr("self", f"__{name}"), value=init_body.attr(name))

        return init

    def method_def(self, name: str) -> "FuncASTBuilder":
        return self.func_def(name).pos_arg("self")

    def async_method_def(self, name: str) -> "FuncASTBuilder":
        return self.async_func_def(name).pos_arg("self")

    def abstract_method_def(self, name: str) -> "FuncASTBuilder":
        return self.func_def(name).pos_arg("self").decorators(self.predefs.abstractmethod_ref)

    def async_abstract_method_def(self, name: str) -> "FuncASTBuilder":
        return self.async_func_def(name).pos_arg("self").decorators(self.predefs.abstractmethod_ref)

    def class_method_def(self, name: str) -> "FuncASTBuilder":
        return self.func_def(name).pos_arg("cls").decorators(self.predefs.classmethod_ref)

    def async_class_method_def(self, name: str) -> "FuncASTBuilder":
        return self.async_func_def(name).pos_arg("cls").decorators(self.predefs.classmethod_ref)

    def property_getter_def(self, name: str) -> "FuncASTBuilder":
        return self.func_def(name).pos_arg("self").decorators(self.predefs.property_ref)

    def property_setter_def(self, name: str) -> "FuncASTBuilder":
        return self.func_def(name).pos_arg("self").decorators(self.attr(name, "setter"))


class FuncASTBuilder:
    def __init__(
        self,
        scopes: ScopeStack,
        resolver: TypeRefResolver,
        node: t.Union[ast.FunctionDef, ast.AsyncFunctionDef],
    ) -> None:
        self.__scopes = scopes
        self.__resolver = resolver
        self.__node = node

    def decorators(self, *items: t.Optional[TypeRef]) -> t.Self:
        self.__node.decorator_list.extend(self.__resolver.resolve(item) for item in items if item is not None)
        return self

    def pos_arg(
        self,
        name: str,
        annotation: t.Optional[TypeRef] = None,
        default: t.Optional[ast.expr] = None,
    ) -> t.Self:
        self.__node.args.args.append(
            ast.arg(
                arg=name,
                annotation=self.__resolver.resolve(annotation) if annotation is not None else None,
            )
        )

        if default is not None:
            self.__node.args.defaults.append(default)

        return self

    def returns(self, ref: TypeRef) -> t.Self:
        self.__node.returns = self.__resolver.resolve(ref)

        return self

    def stub(self) -> None:
        self.__node.body = [ast.Expr(value=ast.Constant(value=...))]

    def __enter__(self) -> BodyASTBuilder:
        self.__scopes.enter(self.__node.name, self.__node.body)
        return BodyASTBuilder(self.__scopes, self.__resolver, self.__node.name, self.__node.body)

    def __exit__(self, *_: object) -> None:
        body = self.__scopes.leave()
        assert body is self.__node.body


class ModBuilder(BodyASTBuilder):
    @classmethod
    def create(cls, info: ModuleInfo) -> "ModBuilder":
        node = ast.Module(body=[], type_ignores=[])
        scopes = ScopeStack(info)
        resolver = TypeRefResolver(scopes)

        return cls(scopes, resolver, node)

    def __init__(self, scopes: ScopeStack, resolver: TypeRefResolver, node: ast.Module) -> None:
        super().__init__(scopes, resolver, None, scopes.enter(None, node.body))
        self.__scopes = scopes
        self.__resolver = resolver
        self.__node = node

    def __enter__(self) -> t.Self:
        return self

    def __exit__(self, *_: object) -> None:
        pass

    def import_stmt(self, module: ModuleInfo) -> ast.Import:
        return ast.Import(names=[ast.alias(name=module.qualname)])

    def build(self) -> ast.Module:
        self.__node.body = [
            *(self.import_stmt(dep) for dep in self.__resolver.dependencies),
            *self.__node.body,
        ]

        return self.__node


def _build_attr_expr(head: t.Union[str, ast.expr], *tail: str) -> ast.expr:
    expr: ast.expr = ast.Name(id=head) if isinstance(head, str) else head
    for attr in tail:
        expr = ast.Attribute(attr=attr, value=expr)

    return expr


if __name__ == "__main__":
    main()
