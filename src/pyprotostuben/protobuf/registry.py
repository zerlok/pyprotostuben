import functools as ft
import typing as t

from google.protobuf.descriptor_pb2 import (
    FieldDescriptorProto,
    EnumDescriptorProto,
    DescriptorProto,
    MethodDescriptorProto,
    ServiceDescriptorProto,
)

from pyprotostuben.python.info import TypeInfo, ModuleInfo, PackageInfo
from pyprotostuben.python.types.resolver.abc import TypeResolver


def _iter_field_type_enum() -> t.Iterable[FieldDescriptorProto.Type.ValueType]:
    for name in dir(FieldDescriptorProto.Type):
        if name.startswith("TYPE_"):
            yield getattr(FieldDescriptorProto.Type, name)


class TypeRegistry(TypeResolver[TypeInfo]):
    def __init__(self, custom: t.Mapping[str, TypeInfo]) -> None:
        self.__bytes_info = TypeInfo(self.builtins_module, "bytes")
        self.__bool_info = TypeInfo(self.builtins_module, "bool")
        self.__int_info = TypeInfo(self.builtins_module, "int")
        self.__float_info = TypeInfo(self.builtins_module, "float")
        self.__str_info = TypeInfo(self.builtins_module, "str")

        self.__builtin: t.Dict[FieldDescriptorProto.Type.ValueType, TypeInfo] = {
            FieldDescriptorProto.TYPE_BYTES: self.__bytes_info,
            FieldDescriptorProto.TYPE_BOOL: self.__bool_info,
            FieldDescriptorProto.TYPE_INT32: self.__int_info,
            FieldDescriptorProto.TYPE_INT64: self.__int_info,
            FieldDescriptorProto.TYPE_UINT32: self.__int_info,
            FieldDescriptorProto.TYPE_UINT64: self.__int_info,
            FieldDescriptorProto.TYPE_SINT32: self.__int_info,
            FieldDescriptorProto.TYPE_SINT64: self.__int_info,
            FieldDescriptorProto.TYPE_FIXED32: self.__int_info,
            FieldDescriptorProto.TYPE_FIXED64: self.__int_info,
            FieldDescriptorProto.TYPE_SFIXED32: self.__int_info,
            FieldDescriptorProto.TYPE_SFIXED64: self.__int_info,
            FieldDescriptorProto.TYPE_FLOAT: self.__float_info,
            FieldDescriptorProto.TYPE_DOUBLE: self.__float_info,
            FieldDescriptorProto.TYPE_STRING: self.__str_info,
        }

        self.__custom_types = {
            FieldDescriptorProto.Type.TYPE_MESSAGE,
            FieldDescriptorProto.Type.TYPE_ENUM,
        }
        self.__custom = custom

        assert (
            set(_iter_field_type_enum()) - (self.__builtin.keys() | self.__custom_types)
        ) == set(), "not all possible field types are covered"
        assert self.__builtin.keys() & self.__custom_types == set(), "field type should be either builtin or a custom"

    def resolve_bytes(self) -> TypeInfo:
        return self.__bool_info

    def resolve_bool(self) -> TypeInfo:
        return self.__bool_info

    def resolve_int(self) -> TypeInfo:
        return self.__int_info

    def resolve_float(self) -> TypeInfo:
        return self.__float_info

    def resolve_str(self) -> TypeInfo:
        return self.__str_info

    @ft.lru_cache(1)
    def resolve_final(self) -> TypeInfo:
        return TypeInfo(self.typing_module, "final")

    @ft.lru_cache(1)
    def resolve_no_return(self) -> TypeInfo:
        return TypeInfo(self.typing_module, "NoReturn")

    @ft.lru_cache(1)
    def resolve_overload(self) -> TypeInfo:
        return TypeInfo(self.typing_module, "overload")

    @ft.lru_cache(1)
    def resolve_literal(self) -> TypeInfo:
        return TypeInfo(self.typing_module, "Literal")

    @ft.lru_cache(1)
    def resolve_property(self) -> TypeInfo:
        return TypeInfo(self.builtins_module, "property")

    @ft.lru_cache(1)
    def resolve_abstract_meta(self) -> TypeInfo:
        return TypeInfo(self.abc_module, "ABCMeta")

    @ft.lru_cache(1)
    def resolve_abstract_method(self) -> TypeInfo:
        return TypeInfo(self.abc_module, "abstractmethod")

    @ft.lru_cache(1)
    def resolve_optional(self) -> TypeInfo:
        return TypeInfo(self.typing_module, "Optional")

    @ft.lru_cache(1)
    def resolve_sequence(self) -> TypeInfo:
        return TypeInfo(self.typing_module, "Sequence")

    @ft.lru_cache(1)
    def resolve_mapping(self) -> TypeInfo:
        return TypeInfo(self.typing_module, "Mapping")

    @ft.lru_cache(1)
    def resolve_async_iterator(self) -> TypeInfo:
        return TypeInfo(self.typing_module, "AsyncIterator")

    def resolve_protobuf_enum_base(self, proto: EnumDescriptorProto) -> TypeInfo:
        return self.int_enum_cls

    def resolve_protobuf_message_base(self, proto: DescriptorProto) -> TypeInfo:
        return self.protobuf_message_cls

    def resolve_protobuf_field(self, proto: FieldDescriptorProto) -> TypeInfo:
        type_ = proto.type

        if type_ not in self.__custom_types:
            return self.__builtin[type_]

        return self.__custom[proto.type_name]

    def resolve_grpc_server(self, proto: ServiceDescriptorProto) -> TypeInfo:
        return TypeInfo.create(self.grpc_aio_module, "Server")

    def resolve_grpc_channel(self, proto: ServiceDescriptorProto) -> TypeInfo:
        return TypeInfo.create(self.grpc_aio_module, "Channel")

    def resolve_grpc_servicer_context(self, proto: MethodDescriptorProto) -> TypeInfo:
        return TypeInfo.create(self.grpc_aio_module, "ServicerContext")

    def resolve_grpc_stub_timeout(self, proto: MethodDescriptorProto) -> TypeInfo:
        return self.__float_info

    def resolve_grpc_stub_metadata_type(self, proto: MethodDescriptorProto) -> TypeInfo:
        return TypeInfo.create(self.grpc_aio_module, "MetadataType")

    def resolve_grpc_stub_credentials(self, proto: MethodDescriptorProto) -> TypeInfo:
        return TypeInfo.create(self.grpc_module, "CallCredentials")

    def resolve_grpc_stub_wait_for_ready(self, proto: MethodDescriptorProto) -> TypeInfo:
        return self.__bool_info

    def resolve_grpc_stub_compression(self, proto: MethodDescriptorProto) -> TypeInfo:
        return TypeInfo.create(self.grpc_module, "Compression")

    def resolve_grpc_stub_unary_unary_call(self, proto: MethodDescriptorProto) -> TypeInfo:
        return TypeInfo.create(self.grpc_aio_module, "UnaryUnaryCall")

    def resolve_grpc_stub_unary_stream_call(self, proto: MethodDescriptorProto) -> TypeInfo:
        return TypeInfo.create(self.grpc_aio_module, "UnaryStreamCall")

    def resolve_grpc_stub_stream_unary_call(self, proto: MethodDescriptorProto) -> TypeInfo:
        return TypeInfo.create(self.grpc_aio_module, "StreamUnaryCall")

    def resolve_grpc_stub_stream_stream_call(self, proto: MethodDescriptorProto) -> TypeInfo:
        return TypeInfo.create(self.grpc_aio_module, "StreamStreamCall")

    def resolve_grpc_method_input(self, proto: MethodDescriptorProto) -> TypeInfo:
        return self.__custom[proto.input_type]

    def resolve_grpc_method_output(self, proto: MethodDescriptorProto) -> TypeInfo:
        return self.__custom[proto.output_type]

    @ft.cached_property
    def builtins_module(self) -> ModuleInfo:
        return ModuleInfo.build("builtins")

    @ft.cached_property
    def abc_module(self) -> ModuleInfo:
        return ModuleInfo.build("abc")

    @ft.cached_property
    def typing_module(self) -> ModuleInfo:
        return ModuleInfo.build("typing")

    @ft.cached_property
    def protobuf_package(self) -> PackageInfo:
        return PackageInfo.build("google", "protobuf")

    @ft.cached_property
    def grpc_module(self) -> ModuleInfo:
        return ModuleInfo(None, "grpc")

    @ft.cached_property
    def grpc_aio_module(self) -> ModuleInfo:
        return ModuleInfo(PackageInfo(None, "grpc"), "aio")

    @ft.cached_property
    def int_enum_cls(self) -> TypeInfo:
        return TypeInfo(ModuleInfo.build("enum"), "IntEnum")

    @ft.cached_property
    def protobuf_message_cls(self) -> TypeInfo:
        return TypeInfo(ModuleInfo(self.protobuf_package, "message"), "Message")
