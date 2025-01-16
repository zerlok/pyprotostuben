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


@dataclass()
class _BaseContext(t.Generic[M]):
    _meta: t.Optional[M]
    path: t.Sequence[int]

    @property
    def name(self) -> str:
        raise NotImplementedError

    @property
    def meta(self) -> M:
        if self._meta is None:
            raise ValueError(self)

        return self._meta

    @meta.setter
    def meta(self, value: M) -> None:
        self._meta = value

    @property
    def parts(self) -> t.Sequence["_BaseContext[M]"]:
        return (self,)


@dataclass()
class FileContext(_BaseContext[M]):
    proto: FileDescriptorProto

    @property
    def name(self) -> str:
        return self.proto.name

    @cached_property
    def file(self) -> ProtoFile:
        return ProtoFile(self.proto)

    @cached_property
    def locations(self) -> t.Mapping[t.Sequence[int], SourceCodeInfo.Location]:
        return {tuple(loc.path): loc for loc in self.proto.source_code_info.location}


@dataclass()
class _ChildContext(_BaseContext[M]):
    parent: _BaseContext[M]

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
    def parts(self) -> t.Sequence[_BaseContext[M]]:
        return *self.parent.parts, self

    @cached_property
    def location(self) -> t.Optional[SourceCodeInfo.Location]:
        return self.root.locations.get(self.path)


@dataclass()
class EnumContext(_ChildContext[M]):
    proto: EnumDescriptorProto

    @property
    def name(self) -> str:
        return self.proto.name


@dataclass()
class EnumValueContext(_ChildContext[M]):
    proto: EnumValueDescriptorProto

    @property
    def name(self) -> str:
        return self.proto.name


@dataclass()
class DescriptorContext(_ChildContext[M]):
    proto: DescriptorProto

    @property
    def name(self) -> str:
        return self.proto.name


@dataclass()
class OneofContext(_ChildContext[M]):
    proto: OneofDescriptorProto

    @property
    def name(self) -> str:
        return self.proto.name


@dataclass()
class FieldContext(_ChildContext[M]):
    proto: FieldDescriptorProto

    @property
    def name(self) -> str:
        return self.proto.name


@dataclass()
class ServiceContext(_ChildContext[M]):
    proto: ServiceDescriptorProto

    @property
    def name(self) -> str:
        return self.proto.name


@dataclass()
class MethodContext(_ChildContext[M]):
    proto: MethodDescriptorProto

    @property
    def name(self) -> str:
        return self.proto.name


@dataclass()
class ExtensionContext(_ChildContext[M]):
    proto: FieldDescriptorProto

    @property
    def name(self) -> str:
        return self.proto.name
