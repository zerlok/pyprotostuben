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
        int_info = TypeInfo(self.builtins_module, "int")
        float_info = TypeInfo(self.builtins_module, "float")

        self.__builtin: t.Dict[FieldDescriptorProto.Type.ValueType, TypeInfo] = {
            FieldDescriptorProto.TYPE_BYTES: TypeInfo(self.builtins_module, "bytes"),
            FieldDescriptorProto.TYPE_BOOL: TypeInfo(self.builtins_module, "bool"),
            FieldDescriptorProto.TYPE_INT32: int_info,
            FieldDescriptorProto.TYPE_INT64: int_info,
            FieldDescriptorProto.TYPE_UINT32: int_info,
            FieldDescriptorProto.TYPE_UINT64: int_info,
            FieldDescriptorProto.TYPE_SINT32: int_info,
            FieldDescriptorProto.TYPE_SINT64: int_info,
            FieldDescriptorProto.TYPE_FIXED32: int_info,
            FieldDescriptorProto.TYPE_FIXED64: int_info,
            FieldDescriptorProto.TYPE_SFIXED32: int_info,
            FieldDescriptorProto.TYPE_SFIXED64: int_info,
            FieldDescriptorProto.TYPE_FLOAT: float_info,
            FieldDescriptorProto.TYPE_DOUBLE: float_info,
            FieldDescriptorProto.TYPE_STRING: TypeInfo(self.builtins_module, "str"),
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
        return TypeInfo.create(self.grpc_module, "Server")

    def resolve_grpc_channel(self, proto: ServiceDescriptorProto) -> TypeInfo:
        return TypeInfo.create(self.grpc_module, "Channel")

    def resolve_grpc_servicer_context(self, proto: MethodDescriptorProto) -> TypeInfo:
        return TypeInfo.create(self.grpc_module, "ServicerContext")

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
        return ModuleInfo(PackageInfo(None, "grpc"), "aio")

    @ft.cached_property
    def int_enum_cls(self) -> TypeInfo:
        return TypeInfo(ModuleInfo.build("enum"), "IntEnum")

    @ft.cached_property
    def protobuf_message_cls(self) -> TypeInfo:
        return TypeInfo(ModuleInfo(self.protobuf_package, "message"), "Message")
