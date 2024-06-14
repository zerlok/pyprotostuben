import typing as t

from google.protobuf.descriptor_pb2 import (
    FieldDescriptorProto,
    DescriptorProto,
    EnumDescriptorProto,
    MethodDescriptorProto,
)

from pyprotostuben.logging import LoggerMixin
from pyprotostuben.protobuf.types.resolver.abc import TypeResolver
from pyprotostuben.python.info import TypeInfo, ModuleInfo, NamespaceInfo


class ModuleDependencyResolver(TypeResolver[NamespaceInfo], LoggerMixin):
    def __init__(
        self,
        inner: TypeResolver[TypeInfo],
        module: ModuleInfo,
        deps: t.Set[ModuleInfo],
    ) -> None:
        self.__inner = inner
        self.__module = module
        self.__deps = deps

    def resolve_final(self) -> NamespaceInfo:
        return self.__resolve(self.__inner.resolve_final())

    def resolve_no_return(self) -> NamespaceInfo:
        return self.__resolve(self.__inner.resolve_no_return())

    def resolve_overload(self) -> NamespaceInfo:
        return self.__resolve(self.__inner.resolve_overload())

    def resolve_literal(self) -> NamespaceInfo:
        return self.__resolve(self.__inner.resolve_literal())

    def resolve_property(self) -> NamespaceInfo:
        return self.__resolve(self.__inner.resolve_property())

    def resolve_abstract_meta(self) -> NamespaceInfo:
        return self.__resolve(self.__inner.resolve_abstract_meta())

    def resolve_abstract_method(self) -> NamespaceInfo:
        return self.__resolve(self.__inner.resolve_abstract_method())

    def resolve_optional(self) -> NamespaceInfo:
        return self.__resolve(self.__inner.resolve_optional())

    def resolve_sequence(self) -> NamespaceInfo:
        return self.__resolve(self.__inner.resolve_sequence())

    def resolve_mapping(self) -> NamespaceInfo:
        return self.__resolve(self.__inner.resolve_mapping())

    def resolve_protobuf_enum_base(self, proto: EnumDescriptorProto) -> NamespaceInfo:
        return self.__resolve(self.__inner.resolve_protobuf_enum_base(proto))

    def resolve_protobuf_message_base(self, proto: DescriptorProto) -> NamespaceInfo:
        return self.__resolve(self.__inner.resolve_protobuf_message_base(proto))

    def resolve_protobuf_field(self, proto: FieldDescriptorProto) -> NamespaceInfo:
        return self.__resolve(self.__inner.resolve_protobuf_field(proto))

    def resolve_grpc_servicer_context(self, proto: MethodDescriptorProto) -> NamespaceInfo:
        return self.__resolve(self.__inner.resolve_grpc_servicer_context(proto))

    def resolve_grpc_method_input(self, proto: MethodDescriptorProto) -> NamespaceInfo:
        return self.__resolve(self.__inner.resolve_grpc_method_input(proto))

    def resolve_grpc_method_output(self, proto: MethodDescriptorProto) -> NamespaceInfo:
        return self.__resolve(self.__inner.resolve_grpc_method_output(proto))

    def __resolve(self, type_: TypeInfo) -> NamespaceInfo:
        if type_.module == self.__module:
            ns = type_.namespace

        else:
            self.__deps.add(type_.module)
            ns = type_

        self._log.debug("resolved", type_=type_, ns=ns)

        return ns
