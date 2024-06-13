import ast
import typing as t
from dataclasses import dataclass, field

from google.protobuf.descriptor_pb2 import (
    MethodDescriptorProto,
    ServiceDescriptorProto,
    FieldDescriptorProto,
    OneofDescriptorProto,
    DescriptorProto,
    EnumValueDescriptorProto,
    EnumDescriptorProto,
    FileDescriptorProto,
)

from pyprotostuben.protobuf.visitor.abc import Proto
from pyprotostuben.protobuf.visitor.decorator import ProtoVisitorDecorator
from pyprotostuben.python.info import ModuleInfo
from pyprotostuben.stack import MutableStack


@dataclass()
class EnumInfo:
    name: str
    value: object


@dataclass()
class FieldInfo:
    name: str
    annotation: ast.expr
    multi: bool = False
    optional: bool = False


@dataclass()
class OneofInfo:
    name: str
    items: t.MutableSequence[str] = field(default_factory=list)


# @dataclass()
# class MapInfo:
#     key: FieldInfo
#     value: FieldInfo


@dataclass()
class MessageInfo:
    # dependencies: t.Set[ModuleInfo] = field(default_factory=set)
    enums: t.MutableSequence[EnumInfo] = field(default_factory=list)
    fields: t.MutableSequence[FieldInfo] = field(default_factory=list)
    oneofs: t.MutableSequence[OneofInfo] = field(default_factory=list)
    # maps: t.MutableMapping[MapInfo] = field(default_factory=dict)
    body: t.MutableSequence[ast.stmt] = field(default_factory=list)


@dataclass()
class ServiceInfo:
    # dependencies: t.Set[ModuleInfo] = field(default_factory=set)
    body: t.MutableSequence[ast.stmt] = field(default_factory=list)


@dataclass()
class ScopeInfo:
    name: str
    dependencies: t.Set[ModuleInfo] = field(default_factory=set)
    message: MessageInfo = field(default_factory=MessageInfo)
    service: ServiceInfo = field(default_factory=ServiceInfo)


class ScopeProtoVisitorDecorator(ProtoVisitorDecorator):
    def __init__(self, stack: MutableStack[ScopeInfo]) -> None:
        self.__stack = stack

    def enter_file_descriptor_proto(self, proto: FileDescriptorProto) -> None:
        self.__enter(proto)

    def leave_file_descriptor_proto(self, proto: FileDescriptorProto) -> None:
        self.__leave()

    def enter_enum_descriptor_proto(self, proto: EnumDescriptorProto) -> None:
        self.__enter(proto)

    def leave_enum_descriptor_proto(self, proto: EnumDescriptorProto) -> None:
        self.__leave()

    def enter_enum_value_descriptor_proto(self, proto: EnumValueDescriptorProto) -> None:
        self.__enter(proto)

    def leave_enum_value_descriptor_proto(self, proto: EnumValueDescriptorProto) -> None:
        self.__leave()

    def enter_descriptor_proto(self, proto: DescriptorProto) -> None:
        self.__enter(proto)

    def leave_descriptor_proto(self, proto: DescriptorProto) -> None:
        self.__leave()

    def enter_oneof_descriptor_proto(self, proto: OneofDescriptorProto) -> None:
        self.__enter(proto)

    def leave_oneof_descriptor_proto(self, proto: OneofDescriptorProto) -> None:
        self.__leave()

    def enter_field_descriptor_proto(self, proto: FieldDescriptorProto) -> None:
        self.__enter(proto)

    def leave_field_descriptor_proto(self, proto: FieldDescriptorProto) -> None:
        self.__leave()

    def enter_service_descriptor_proto(self, proto: ServiceDescriptorProto) -> None:
        self.__enter(proto)

    def leave_service_descriptor_proto(self, proto: ServiceDescriptorProto) -> None:
        self.__leave()

    def enter_method_descriptor_proto(self, proto: MethodDescriptorProto) -> None:
        self.__enter(proto)

    def leave_method_descriptor_proto(self, proto: MethodDescriptorProto) -> None:
        self.__leave()

    def __enter(self, proto: Proto) -> None:
        self.__stack.put(ScopeInfo(name=proto.name))

    def __leave(self) -> None:
        leaving = self.__stack.pop()

        if self.__stack:
            parent = self.__stack.get_last()
            parent.dependencies.update(leaving.dependencies)
