import abc
import ast
import typing as t
from collections import deque
from dataclasses import dataclass

from pyprotostuben.python.builder import ModuleASTBuilder, TypeRef
from pyprotostuben.python.info import ModuleInfo, TypeInfo
from pyprotostuben.python.visitor.abc import TypeVisitorDecorator
from pyprotostuben.python.visitor.model import (
    ContainerContext,
    EnumContext,
    EnumValueContext,
    ScalarContext,
    StructureContext,
    StructureFieldContext,
)
from pyprotostuben.python.visitor.walker import DefaultTypeWalkerTrait, TypeWalker, TypeWalkerTrait


class ModelFactory(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def create_enum_ref(self, elements: t.Sequence[str]) -> TypeRef:
        raise NotImplementedError

    @abc.abstractmethod
    def create_container_ref(self, container: type[object], inners: t.Sequence[TypeRef]) -> TypeRef:
        raise NotImplementedError

    @abc.abstractmethod
    def create_model_def(
        self,
        name: str,
        doc: t.Optional[str],
        fields: t.Mapping[str, TypeRef],
        defaults: t.Mapping[str, object],
        nested: t.Sequence[ast.stmt],
    ) -> ast.stmt:
        raise NotImplementedError

    @abc.abstractmethod
    def create_model_ref(self, name: str) -> TypeRef:
        raise NotImplementedError


class ModelDefBuilder:
    def __init__(
        self,
        factory: ModelFactory,
        trait: t.Optional[TypeWalkerTrait] = None,
    ) -> None:
        self.__factory = factory
        self.__trait = trait or DefaultTypeWalkerTrait()

        self.__hierarchy = list[object]()
        self.__registry = dict[object, tuple[t.Sequence[ast.stmt], TypeRef]]()
        self.__analyzer = TypeWalker(self.__trait, ModelASTGenerator(factory, self.__hierarchy, self.__registry))

    def create(
        self,
        name: str,
        fields: t.Mapping[str, TypeRef],
        defaults: t.Optional[t.Mapping[str, object]] = None,
        nested: t.Optional[t.Sequence[ast.stmt]] = None,
        doc: t.Optional[str] = None,
    ) -> ast.stmt:
        return self.__factory.create_model_def(
            name=name,
            doc=doc,
            fields=fields,
            defaults=defaults or {},
            nested=nested or [],
        )

    def update(self, types: t.Collection[type[object]]) -> None:
        todo = set(types) - self.__registry.keys()

        for type_ in todo:
            context = GenContext(deque([GenContext.Item(None, [], [], [])]))
            self.__analyzer.walk(type_, context)

            self.__registry[type_] = (context.last.nested, context.last.types[0])

    def resolve(self, type_: type[object]) -> TypeRef:
        _, ref = self.__registry[type_]
        return ref

    def assign_expr(
        self,
        source: ast.expr,
        type_: type[object],
        mode: t.Literal["original", "model"],
        builder: ModuleASTBuilder,
    ) -> ast.expr:
        context = InitExprContext(deque([InitExprContext.Item(source, [])]))

        resolve = TypeInfo.from_type if mode == "original" else self.resolve

        walker = TypeWalker(self.__trait, AssignExprGenerator(builder, resolve))
        walker.walk(type_, context)

        return context.last.exprs[0]

    def get_all_defs(self) -> t.Sequence[ast.stmt]:
        return [stmt for type_ in self.__hierarchy for stmt in self.__registry[type_][0]]


class DataclassModelFactory(ModelFactory):
    def __init__(self, builder: ModuleASTBuilder) -> None:
        self.__builder = builder

    def create_enum_ref(self, elements: t.Sequence[str]) -> TypeRef:
        return self.__builder.literal_ref(*(self.__builder.const(el) for el in elements))

    def create_container_ref(self, container: type[object], inners: t.Sequence[TypeRef]) -> TypeRef:
        return self.__builder.generic_ref(TypeInfo.from_type(container), *inners)

    def create_model_def(
        self,
        name: str,
        doc: t.Optional[str],
        fields: t.Mapping[str, TypeRef],
        defaults: t.Mapping[str, object],
        nested: t.Sequence[ast.stmt],
    ) -> ast.stmt:
        return self.__builder.dataclass_def(
            name=name,
            body=nested,
            frozen=True,
            kw_only=True,
            fields=fields,
            doc=doc,
        )

    def create_model_ref(self, name: str) -> TypeRef:
        return TypeInfo.build(self.__builder.info, name)


class PydanticModelFactory(ModelFactory):
    def __init__(self, builder: ModuleASTBuilder) -> None:
        self.__builder = builder
        self.__base_model = TypeInfo.build(ModuleInfo(None, "pydantic"), "BaseModel")

    def create_enum_ref(self, elements: t.Sequence[str]) -> TypeRef:
        return self.__builder.literal_ref(*(self.__builder.const(el) for el in elements))

    def create_container_ref(self, container: type[object], inners: t.Sequence[TypeRef]) -> TypeRef:
        return self.__builder.generic_ref(TypeInfo.from_type(container), *inners)

    def create_model_def(
        self,
        name: str,
        doc: t.Optional[str],
        fields: t.Mapping[str, TypeRef],
        defaults: t.Mapping[str, object],
        nested: t.Sequence[ast.stmt],
    ) -> ast.stmt:
        return self.__builder.class_def(
            name=name,
            body=[
                *nested,
                *(
                    self.__builder.attr_stub(
                        name=name,
                        annotation=annotation,
                    )
                    for name, annotation in fields.items()
                ),
            ],
            bases=[self.__base_model],
            doc=doc,
        )

    def create_model_ref(self, name: str) -> TypeRef:
        return TypeInfo.build(self.__builder.info, name)


@dataclass()
class GenContext:
    @dataclass()
    class Item:
        name: t.Optional[str]
        nested: t.MutableSequence[ast.stmt]
        types: t.MutableSequence[TypeRef]
        attrs: t.MutableSequence[ast.expr]

    stack: t.MutableSequence[Item]

    @property
    def last(self) -> Item:
        return self.stack[-1]

    def enter(self, name: t.Optional[str] = None) -> Item:
        context = self.Item(name=name, nested=list(), types=list(), attrs=list())
        self.stack.append(context)

        return context

    def leave(self) -> Item:
        return self.stack.pop()


class ModelASTGenerator(TypeVisitorDecorator[GenContext]):
    def __init__(
        self,
        factory: ModelFactory,
        hierarchy: t.MutableSequence[object],
        registry: t.MutableMapping[object, tuple[t.Sequence[ast.stmt], TypeRef]],
    ) -> None:
        self.__factory = factory
        self.__registry = registry
        self.__hierarchy = hierarchy

    def enter_scalar(self, context: ScalarContext, meta: GenContext) -> None:
        pass

    def leave_scalar(self, context: ScalarContext, meta: GenContext) -> None:
        self.__add_model(meta, context.type_, [], TypeInfo.from_type(context.type_))

    def enter_enum(self, context: EnumContext, meta: GenContext) -> None:
        meta.enter()

    def leave_enum(self, context: EnumContext, meta: GenContext) -> None:
        inner = meta.leave()
        ref = self.__factory.create_enum_ref([val.name for val in context.values])
        self.__add_model(meta, context.type_, inner.nested, ref)

    def enter_enum_value(self, context: EnumValueContext, meta: GenContext) -> None:
        pass

    def leave_enum_value(self, context: EnumValueContext, meta: GenContext) -> None:
        pass

    def enter_container(self, context: ContainerContext, meta: GenContext) -> None:
        meta.enter()

    def leave_container(self, context: ContainerContext, meta: GenContext) -> None:
        inner = meta.leave()
        ref = self.__factory.create_container_ref(context.origin, inner.types)

        for inner_type, inner_stmt in zip(context.inners, inner.nested):
            self.__add_model(meta, inner_type, [inner_stmt], ref)

    def enter_structure(self, context: StructureContext, meta: GenContext) -> None:
        meta.enter()

    def leave_structure(self, context: StructureContext, meta: GenContext) -> None:
        inner = meta.leave()
        ref = self.__factory.create_model_ref(context.name)
        model_def = self.__factory.create_model_def(
            name=context.name,
            fields={field.name: type_ref for field, type_ref in zip(context.fields, inner.types)},
            defaults={},
            nested=inner.nested,
            doc=context.description,
        )
        self.__add_model(meta, context.type_, [model_def], ref)

    def enter_structure_field(self, context: StructureFieldContext, meta: GenContext) -> None:
        pass

    def leave_structure_field(self, context: StructureFieldContext, meta: GenContext) -> None:
        pass

    def __add_model(self, meta: GenContext, type_: object, stmts: t.Sequence[ast.stmt], ref: TypeRef) -> None:
        if type_ not in self.__registry:
            self.__registry[type_] = (stmts, ref)
            self.__hierarchy.append(type_)

        meta.last.nested.extend(stmts)
        meta.last.types.append(ref)


@dataclass()
class InitExprContext:
    @dataclass()
    class Item:
        source: ast.expr
        exprs: t.MutableSequence[ast.expr]

    stack: t.MutableSequence[Item]

    @property
    def last(self) -> Item:
        return self.stack[-1]

    def enter(self, source: ast.expr) -> Item:
        context = self.Item(source=source, exprs=[])
        self.stack.append(context)

        return context

    def leave(self) -> Item:
        return self.stack.pop()


class AssignExprGenerator(TypeVisitorDecorator[InitExprContext]):
    def __init__(self, builder: ModuleASTBuilder, resolver: t.Callable[[type[object]], TypeInfo]) -> None:
        self.__builder = builder
        self.__resolver = resolver

    def enter_scalar(self, context: ScalarContext, meta: InitExprContext) -> None:
        pass

    def leave_scalar(self, context: ScalarContext, meta: InitExprContext) -> None:
        meta.last.exprs.append(meta.last.source)

    def enter_enum(self, context: EnumContext, meta: InitExprContext) -> None:
        meta.enter(meta.last.source)

    def leave_enum(self, context: EnumContext, meta: InitExprContext) -> None:
        scope = meta.leave()
        # TODO: support t.Literal
        meta.last.exprs.append(self.__builder.attr(scope.source, "name"))

    def enter_enum_value(self, context: EnumValueContext, meta: InitExprContext) -> None:
        pass

    def leave_enum_value(self, context: EnumValueContext, meta: InitExprContext) -> None:
        pass

    def enter_container(self, context: ContainerContext, meta: InitExprContext) -> None:
        queue = deque([meta.last.source])
        parts = ["item"]

        while queue:
            item = queue.pop()

            if isinstance(item, ast.Attribute):
                queue.append(item.value)
                parts.append(item.attr)

            elif isinstance(item, ast.Name):
                parts.append(item.id)

        meta.enter(self.__builder.attr("_".join(reversed(parts))))

    def leave_container(self, context: ContainerContext, meta: InitExprContext) -> None:
        # TODO: set / list / dict compr
        inner = meta.leave()
        meta.last.exprs.append(
            self.__builder.list_expr(
                items=meta.last.source,
                target=inner.source,
                item=inner.exprs[0],
            )
        )

    def enter_structure(self, context: StructureContext, meta: InitExprContext) -> None:
        meta.enter(meta.last.source)

    def leave_structure(self, context: StructureContext, meta: InitExprContext) -> None:
        nested = meta.leave()
        meta.last.exprs.append(
            self.__builder.call(
                func=self.__resolver(context.type_),
                kwargs={field.name: expr for field, expr in zip(context.fields, nested.exprs)},
            )
        )

    def enter_structure_field(self, context: StructureFieldContext, meta: InitExprContext) -> None:
        meta.enter(self.__builder.attr(meta.last.source, context.name))

    def leave_structure_field(self, context: StructureFieldContext, meta: InitExprContext) -> None:
        nested = meta.leave()
        meta.last.exprs.append(nested.exprs[0])
