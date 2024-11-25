import abc
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

M = t.TypeVar("M")


@dataclass(frozen=True)
class _BaseContext(t.Generic[M_co, T_co]):
    meta: M_co
    proto: T_co
    child_meta_factory: "ChildMetaFactory[M_co]"
    path: t.Sequence[int]

    @property
    def parts(self) -> t.Sequence[Proto]:
        return (self.proto,)


@dataclass(frozen=True)
class FileDescriptorContext(_BaseContext[M_co, FileDescriptorProto]):
    @cached_property
    def file(self) -> ProtoFile:
        return ProtoFile(self.proto)

    @cached_property
    def locations(self) -> t.Mapping[t.Sequence[int], SourceCodeInfo.Location]:
        return {tuple(loc.path): loc for loc in self.proto.source_code_info.location}


@dataclass(frozen=True)
class _ChildContext(_BaseContext[M_co, T_co], t.Generic[M_co, T_co, P_co]):
    parent: _BaseContext[M_co, P_co]

    @cached_property
    def root(self) -> FileDescriptorContext[M_co]:
        ctx = self.parent

        while isinstance(ctx, _ChildContext):
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
class EnumDescriptorContext(_ChildContext[M_co, EnumDescriptorProto, t.Union[FileDescriptorProto, DescriptorProto]]):
    pass


@dataclass(frozen=True)
class EnumValueDescriptorContext(_ChildContext[M_co, EnumValueDescriptorProto, EnumDescriptorProto]):
    pass


@dataclass(frozen=True)
class DescriptorContext(_ChildContext[M_co, DescriptorProto, t.Union[FileDescriptorProto, DescriptorProto]]):
    pass


@dataclass(frozen=True)
class OneofDescriptorContext(_ChildContext[M_co, OneofDescriptorProto, DescriptorProto]):
    pass


@dataclass(frozen=True)
class FieldDescriptorContext(_ChildContext[M_co, FieldDescriptorProto, t.Union[FileDescriptorProto, DescriptorProto]]):
    pass


@dataclass(frozen=True)
class ServiceDescriptorContext(_ChildContext[M_co, ServiceDescriptorProto, FileDescriptorProto]):
    pass


@dataclass(frozen=True)
class MethodDescriptorContext(_ChildContext[M_co, MethodDescriptorProto, ServiceDescriptorProto]):
    pass


class ChildMetaFactory(t.Protocol[M]):
    @abc.abstractmethod
    def __call__(
        self,
        parent: t.Union[
            FileDescriptorContext[M],
            EnumDescriptorContext[M],
            EnumValueDescriptorContext[M],
            DescriptorContext[M],
            OneofDescriptorContext[M],
            FieldDescriptorContext[M],
            ServiceDescriptorContext[M],
            MethodDescriptorContext[M],
        ],
    ) -> M:
        raise NotImplementedError


def forward_meta(
    parent: t.Union[
        FileDescriptorContext[M_co],
        EnumDescriptorContext[M_co],
        EnumValueDescriptorContext[M_co],
        DescriptorContext[M_co],
        OneofDescriptorContext[M_co],
        FieldDescriptorContext[M_co],
        ServiceDescriptorContext[M_co],
        MethodDescriptorContext[M_co],
    ],
) -> M_co:
    return parent.meta
