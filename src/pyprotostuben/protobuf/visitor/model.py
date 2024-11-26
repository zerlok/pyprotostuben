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


@dataclass()
class _BaseContext(t.Generic[M, T_co]):
    _meta: t.Optional[M]
    proto: T_co
    path: t.Sequence[int]

    @property
    def meta(self) -> M:
        if self._meta is None:
            raise ValueError(self)

        return self._meta

    @meta.setter
    def meta(self, value: M) -> None:
        self._meta = value

    @property
    def parts(self) -> t.Sequence["_BaseContext[M, Proto]"]:
        return (self,)


@dataclass()
class FileContext(_BaseContext[M, FileDescriptorProto]):
    @cached_property
    def file(self) -> ProtoFile:
        return ProtoFile(self.proto)

    @cached_property
    def locations(self) -> t.Mapping[t.Sequence[int], SourceCodeInfo.Location]:
        return {tuple(loc.path): loc for loc in self.proto.source_code_info.location}


@dataclass()
class _ChildContext(_BaseContext[M, T_co], t.Generic[M, T_co, P_co]):
    parent: _BaseContext[M, P_co]

    @cached_property
    def root(self) -> FileContext[M]:
        ctx = self.parent

        while isinstance(ctx, _ChildContext):
            ctx = ctx.parent

        assert isinstance(ctx, FileContext)

        return ctx

    @cached_property
    def file(self) -> ProtoFile:
        return self.root.file

    @cached_property
    def parts(self) -> t.Sequence["_BaseContext[M, Proto]"]:
        return *self.parent.parts, self

    @cached_property
    def location(self) -> t.Optional[SourceCodeInfo.Location]:
        return self.root.locations.get(self.path)


@dataclass()
class EnumContext(_ChildContext[M, EnumDescriptorProto, t.Union[FileDescriptorProto, DescriptorProto]]):
    pass


@dataclass()
class EnumValueContext(_ChildContext[M, EnumValueDescriptorProto, EnumDescriptorProto]):
    pass


@dataclass()
class DescriptorContext(_ChildContext[M, DescriptorProto, t.Union[FileDescriptorProto, DescriptorProto]]):
    pass


@dataclass()
class OneofContext(_ChildContext[M, OneofDescriptorProto, DescriptorProto]):
    pass


@dataclass()
class FieldContext(_ChildContext[M, FieldDescriptorProto, t.Union[FileDescriptorProto, DescriptorProto]]):
    pass


@dataclass()
class ServiceContext(_ChildContext[M, ServiceDescriptorProto, FileDescriptorProto]):
    pass


@dataclass()
class MethodContext(_ChildContext[M, MethodDescriptorProto, ServiceDescriptorProto]):
    pass


@dataclass()
class ExtensionContext(_ChildContext[M, FieldDescriptorProto, t.Union[FileDescriptorProto, DescriptorProto]]):
    pass
