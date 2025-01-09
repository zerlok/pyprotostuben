import ast
import typing as t
from collections import deque
from dataclasses import dataclass

from pyprotostuben.python.builder import ModuleASTBuilder, TypeRef
from pyprotostuben.python.info import TypeInfo
from pyprotostuben.python.visitor.abc import TypeVisitorDecorator
from pyprotostuben.python.visitor.model import ContainerContext, EnumContext, ScalarContext, StructureContext
from pyprotostuben.python.visitor.walker import DefaultTypeWalkerTrait, TypeWalker, TypeWalkerTrait


class DataclassASTBuilder:
    def __init__(self, builder: ModuleASTBuilder, trait: t.Optional[TypeWalkerTrait] = None) -> None:
        self.__hierarchy = list[object]()
        self.__registry = dict[object, tuple[t.Sequence[ast.stmt], TypeRef]]()
        self.__walker = TypeWalker(
            trait or DefaultTypeWalkerTrait(),
            TypeHierarchyAnalyzer(self.__registry, self.__hierarchy),
            NestedTypesDataclassASTGenerator(builder),
        )

    def update(self, types: t.Collection[type[object]]) -> None:
        todo = set(types) - self.__registry.keys()

        for type_ in todo:
            context = GenContext(deque([TypeContext(None, [], [])]))
            self.__walker.walk(type_, context)

            self.__registry[type_] = (context.last.nested, context.last.types[0])

    def resolve(self, type_: type[object]) -> TypeRef:
        _, ref = self.__registry[type_]
        return ref

    def get_all_defs(self) -> t.Sequence[ast.stmt]:
        return [stmt for type_ in self.__hierarchy for stmt in self.__registry[type_][0]]


@dataclass()
class TypeContext:
    name: t.Optional[str]
    nested: t.MutableSequence[ast.stmt]
    types: t.MutableSequence[TypeRef]


@dataclass()
class GenContext:
    stack: t.MutableSequence[TypeContext]

    @property
    def namespace(self) -> t.Sequence[str]:
        return [context.name for context in self.stack if context.name]

    @property
    def last(self) -> TypeContext:
        return self.stack[-1]

    def enter(self, name: t.Optional[str] = None) -> TypeContext:
        context = TypeContext(name=name, nested=list(), types=list())
        self.stack.append(context)

        return context

    def leave(self) -> TypeContext:
        return self.stack.pop()


class TypeHierarchyAnalyzer(TypeVisitorDecorator[GenContext]):
    def __init__(
        self,
        registry: t.MutableMapping[object, tuple[t.Sequence[ast.stmt], TypeRef]],
        hierarchy: t.MutableSequence[object],
    ) -> None:
        self.__registry = registry
        self.__hierarchy = hierarchy

    def enter_scalar(self, context: ScalarContext, meta: GenContext) -> None:
        pass

    def leave_scalar(self, context: ScalarContext, meta: GenContext) -> None:
        self.__add_type(context.type_)

    def enter_enum(self, context: EnumContext, meta: GenContext) -> None:
        pass

    def leave_enum(self, context: EnumContext, meta: GenContext) -> None:
        self.__add_type(context.type_)

    def enter_container(self, context: ContainerContext, meta: GenContext) -> None:
        pass

    def leave_container(self, context: ContainerContext, meta: GenContext) -> None:
        self.__add_type(context.type_)

    def enter_structure(self, context: StructureContext, meta: GenContext) -> None:
        pass

    def leave_structure(self, context: StructureContext, meta: GenContext) -> None:
        self.__add_type(context.type_)

    def __add_type(self, type_: object) -> None:
        if type_ not in self.__registry:
            self.__registry[type_] = ([], TypeInfo.from_type(type_))
            self.__hierarchy.append(type_)


class NestedTypesDataclassASTGenerator(TypeVisitorDecorator[GenContext]):
    def __init__(self, builder: ModuleASTBuilder) -> None:
        self.__builder = builder

    def enter_scalar(self, context: ScalarContext, meta: GenContext) -> None:
        pass

    def leave_scalar(self, context: ScalarContext, meta: GenContext) -> None:
        meta.last.types.append(TypeInfo.from_type(context.type_))

    def enter_enum(self, context: EnumContext, meta: GenContext) -> None:
        meta.enter(context.name)

    def leave_enum(self, context: EnumContext, meta: GenContext) -> None:
        meta.leave()
        meta.last.types.append(self.__builder.literal_ref(*(self.__builder.const(val.name) for val in context.values)))

    def enter_container(self, context: ContainerContext, meta: GenContext) -> None:
        meta.enter()

    def leave_container(self, context: ContainerContext, meta: GenContext) -> None:
        inner_types = meta.leave()
        meta.last.types.append(self.__builder.generic_ref(TypeInfo.from_type(context.origin), *inner_types.types))

    def enter_structure(self, context: StructureContext, meta: GenContext) -> None:
        meta.enter(context.name)

    def leave_structure(self, context: StructureContext, meta: GenContext) -> None:
        inner = meta.leave()
        meta.last.nested.append(
            self.__builder.dataclass_def(
                name=context.name,
                body=inner.nested,
                frozen=True,
                kw_only=True,
                fields={field.name: type_ref for field, type_ref in zip(context.fields, inner.types)},
            )
        )
        meta.last.types.append(TypeInfo.build(None, *meta.namespace, context.name))
