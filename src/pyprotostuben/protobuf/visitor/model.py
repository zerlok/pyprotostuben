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

M_co = t.TypeVar("M_co", covariant=True)
P_co = t.TypeVar("P_co", covariant=True, bound=Proto)
T_co = t.TypeVar("T_co", covariant=True, bound=Proto)


@dataclass(frozen=True)
class BaseContext(t.Generic[M_co, T_co]):
    meta: M_co
    proto: T_co
    path: t.Sequence[int]

    @property
    def parts(self) -> t.Sequence[Proto]:
        return (self.proto,)


@dataclass(frozen=True)
class FileDescriptorContext(BaseContext[M_co, FileDescriptorProto]):
    @cached_property
    def file(self) -> ProtoFile:
        return ProtoFile(self.proto)

    @cached_property
    def locations(self) -> t.Mapping[t.Sequence[int], SourceCodeInfo.Location]:
        return {tuple(loc.path): loc for loc in self.proto.source_code_info.location}


@dataclass(frozen=True)
class ChildContext(BaseContext[M_co, T_co], t.Generic[M_co, T_co, P_co]):
    parent: BaseContext[M_co, P_co]

    @cached_property
    def root(self) -> FileDescriptorContext[M_co]:
        ctx = self.parent

        while isinstance(ctx, ChildContext):
            ctx = ctx.parent

        assert isinstance(ctx, FileDescriptorContext)

        return ctx

    @cached_property
    def file(self) -> ProtoFile:
        return self.root.file

    @cached_property
    def parts(self) -> t.Sequence[Proto]:
        return *self.parent.parts, self.proto

    @cached_property
    def location(self) -> t.Optional[SourceCodeInfo.Location]:
        return self.root.locations.get(self.path)


@dataclass(frozen=True)
class EnumDescriptorContext(ChildContext[M_co, EnumDescriptorProto, t.Union[FileDescriptorProto, DescriptorProto]]):
    pass


@dataclass(frozen=True)
class EnumValueDescriptorContext(ChildContext[M_co, EnumValueDescriptorProto, EnumDescriptorProto]):
    pass


@dataclass(frozen=True)
class DescriptorContext(ChildContext[M_co, DescriptorProto, t.Union[FileDescriptorProto, DescriptorProto]]):
    pass


@dataclass(frozen=True)
class OneofDescriptorContext(ChildContext[M_co, OneofDescriptorProto, DescriptorProto]):
    pass


@dataclass(frozen=True)
class FieldDescriptorContext(ChildContext[M_co, FieldDescriptorProto, t.Union[FileDescriptorProto, DescriptorProto]]):
    pass


@dataclass(frozen=True)
class ServiceDescriptorContext(ChildContext[M_co, ServiceDescriptorProto, FileDescriptorProto]):
    pass


@dataclass(frozen=True)
class MethodDescriptorContext(ChildContext[M_co, MethodDescriptorProto, ServiceDescriptorProto]):
    pass
