import typing as t
from dataclasses import dataclass
from functools import cached_property

from google.protobuf.descriptor_pb2 import (
    DescriptorProto,
    EnumDescriptorProto,
    EnumValueDescriptorProto,
    FieldDescriptorProto,
    FileDescriptorProto,
    MethodDescriptorProto,
    OneofDescriptorProto,
    ServiceDescriptorProto,
    SourceCodeInfo,
)

from pyprotostuben.protobuf.file import ProtoFile

Proto = t.Union[
    FileDescriptorProto,
    EnumDescriptorProto,
    EnumValueDescriptorProto,
    DescriptorProto,
    OneofDescriptorProto,
    FieldDescriptorProto,
    ServiceDescriptorProto,
    MethodDescriptorProto,
]

M = t.TypeVar("M")
P_co = t.TypeVar("P_co", covariant=True, bound=Proto)
T_co = t.TypeVar("T_co", covariant=True, bound=Proto)


@dataclass(frozen=True)
class BaseContext(t.Generic[M, T_co]):
    meta: M
    item: T_co
    path: t.Sequence[int]

    @property
    def parts(self) -> t.Sequence[Proto]:
        return (self.item,)


@dataclass(frozen=True)
class FileDescriptorContext(BaseContext[M, FileDescriptorProto]):
    @cached_property
    def file(self) -> ProtoFile:
        return ProtoFile(self.item)

    @cached_property
    def locations(self) -> t.Mapping[t.Sequence[int], SourceCodeInfo.Location]:
        return {tuple(loc.path): loc for loc in self.item.source_code_info.location}


@dataclass(frozen=True)
class ChildContext(BaseContext[M, T_co], t.Generic[M, T_co, P_co]):
    parent_context: BaseContext[M, P_co]

    @cached_property
    def root_context(self) -> FileDescriptorContext[M]:
        ctx = self.parent_context

        while isinstance(ctx, ChildContext):
            ctx = ctx.parent_context

        assert isinstance(ctx, FileDescriptorContext)

        return ctx

    @property
    def root(self) -> FileDescriptorProto:
        return self.root_context.item

    @cached_property
    def file(self) -> ProtoFile:
        return self.root_context.file

    @property
    def parent(self) -> P_co:
        return self.parent_context.item

    @cached_property
    def parts(self) -> t.Sequence[Proto]:
        return *self.parent_context.parts, self.item

    @cached_property
    def location(self) -> t.Optional[SourceCodeInfo.Location]:
        return self.root_context.locations.get(self.path)


@dataclass(frozen=True)
class EnumDescriptorContext(ChildContext[M, EnumDescriptorProto, t.Union[FileDescriptorProto, DescriptorProto]]):
    pass


@dataclass(frozen=True)
class EnumValueDescriptorContext(ChildContext[M, EnumValueDescriptorProto, EnumDescriptorProto]):
    pass


@dataclass(frozen=True)
class DescriptorContext(ChildContext[M, DescriptorProto, t.Union[FileDescriptorProto, DescriptorProto]]):
    pass


@dataclass(frozen=True)
class OneofDescriptorContext(ChildContext[M, OneofDescriptorProto, DescriptorProto]):
    pass


@dataclass(frozen=True)
class FieldDescriptorContext(ChildContext[M, FieldDescriptorProto, t.Union[FileDescriptorProto, DescriptorProto]]):
    pass


@dataclass(frozen=True)
class ServiceDescriptorContext(ChildContext[M, ServiceDescriptorProto, FileDescriptorProto]):
    pass


@dataclass(frozen=True)
class MethodDescriptorContext(ChildContext[M, MethodDescriptorProto, ServiceDescriptorProto]):
    pass
