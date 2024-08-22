import typing as t
from dataclasses import dataclass

from google.protobuf.descriptor_pb2 import FieldDescriptorProto, MethodDescriptorProto

from pyprotostuben.python.info import ModuleInfo, TypeInfo


@dataclass(frozen=True)
class ScalarInfo(TypeInfo):
    pass


@dataclass(frozen=True)
class EnumInfo(TypeInfo):
    pass


@dataclass(frozen=True)
class MessageInfo(TypeInfo):
    pass


@dataclass(frozen=True)
class MapEntryInfo:
    module: ModuleInfo
    key: t.Union[ScalarInfo, EnumInfo, MessageInfo]
    value: t.Union[ScalarInfo, EnumInfo, MessageInfo]


ProtoInfo = t.Union[ScalarInfo, EnumInfo, MessageInfo, MapEntryInfo]


@dataclass(frozen=True)
class MapEntryPlaceholder:
    module: ModuleInfo
    key: FieldDescriptorProto
    value: FieldDescriptorProto


class RegistryError(Exception):
    pass


class InvalidMessageInfoError(RegistryError):
    pass


class InvalidMapEntryKeyError(RegistryError):
    pass


class InvalidMapEntryValueError(RegistryError):
    pass


class TypeRegistry:
    def __init__(
        self,
        user_types: t.Mapping[str, t.Union[EnumInfo, MessageInfo]],
        map_entries: t.Mapping[str, MapEntryPlaceholder],
    ) -> None:
        self.__scalars: t.Mapping[FieldDescriptorProto.Type.ValueType, ScalarInfo] = self.__build_scalars()
        self.__message_types = {
            FieldDescriptorProto.Type.TYPE_MESSAGE,
            FieldDescriptorProto.Type.TYPE_ENUM,
        }

        self.__user_types = user_types
        self.__map_entries = map_entries

        assert not (
            set(self.__iter_field_type_enum()) - (self.__scalars.keys() | self.__message_types)
        ), "not all possible field types are covered"
        assert not (self.__scalars.keys() & self.__message_types), "field type should be either scalar or message"

    def resolve_proto_field(self, field: FieldDescriptorProto) -> ProtoInfo:
        if field.type not in self.__message_types:
            return self.__scalars[field.type]

        if field.type_name in self.__user_types:
            return self.__user_types[field.type_name]

        return self.resolve_proto_map_entry(field.type_name)

    def resolve_proto_method_client_input(self, method: MethodDescriptorProto) -> MessageInfo:
        return self.resolve_proto_message(method.input_type)

    def resolve_proto_method_server_output(self, method: MethodDescriptorProto) -> MessageInfo:
        return self.resolve_proto_message(method.output_type)

    def resolve_proto_message(self, ref: str) -> MessageInfo:
        info = self.__user_types[ref]
        if not isinstance(info, MessageInfo):
            raise InvalidMessageInfoError(info, ref)

        return info

    def resolve_proto_map_entry(self, ref: str) -> MapEntryInfo:
        map_entry = self.__map_entries[ref]

        key = self.resolve_proto_field(map_entry.key)
        if not isinstance(key, (ScalarInfo, EnumInfo, MessageInfo)):
            raise InvalidMapEntryKeyError(key, ref)

        value = self.resolve_proto_field(map_entry.value)
        if not isinstance(value, (ScalarInfo, EnumInfo, MessageInfo)):
            raise InvalidMapEntryValueError(value, ref)

        return MapEntryInfo(map_entry.module, key, value)

    @classmethod
    def __build_scalars(cls) -> t.Mapping[FieldDescriptorProto.Type.ValueType, ScalarInfo]:
        builtins_module = ModuleInfo(None, "builtins")

        bytes_info = ScalarInfo(builtins_module, ("bytes",))
        bool_info = ScalarInfo(builtins_module, ("bool",))
        int_info = ScalarInfo(builtins_module, ("int",))
        float_info = ScalarInfo(builtins_module, ("float",))
        str_info = ScalarInfo(builtins_module, ("str",))

        return {
            FieldDescriptorProto.TYPE_BYTES: bytes_info,
            FieldDescriptorProto.TYPE_BOOL: bool_info,
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
            FieldDescriptorProto.TYPE_STRING: str_info,
        }

    @classmethod
    def __iter_field_type_enum(cls) -> t.Iterable[FieldDescriptorProto.Type.ValueType]:
        for name in dir(FieldDescriptorProto.Type):
            if name.startswith("TYPE_"):
                yield getattr(FieldDescriptorProto.Type, name)
