import ast
import typing as t
from dataclasses import dataclass

from google.protobuf.descriptor_pb2 import FieldDescriptorProto, MethodDescriptorProto

from pyprotostuben.python.builder import build_attr, build_generic_ref


@dataclass(frozen=True)
class EnumInfo:
    ref: t.Sequence[str]


@dataclass(frozen=True)
class MessageInfo:
    ref: t.Sequence[str]


@dataclass(frozen=True)
class MapEntryInfo:
    key: FieldDescriptorProto
    value: FieldDescriptorProto


ProtoInfo = t.Union[EnumInfo, MessageInfo, MapEntryInfo]


class TypeRegistry:
    def __init__(self, infos: t.Mapping[str, ProtoInfo]) -> None:
        self.__bytes_ast = build_attr("builtins", "bytes")
        self.__bool_ast = build_attr("builtins", "bool")
        self.__int_ast = build_attr("builtins", "int")
        self.__float_ast = build_attr("builtins", "float")
        self.__str_ast = build_attr("builtins", "str")

        self.__builtin: t.Mapping[FieldDescriptorProto.Type.ValueType, ast.expr] = {
            FieldDescriptorProto.TYPE_BYTES: self.__bytes_ast,
            FieldDescriptorProto.TYPE_BOOL: self.__bool_ast,
            FieldDescriptorProto.TYPE_INT32: self.__int_ast,
            FieldDescriptorProto.TYPE_INT64: self.__int_ast,
            FieldDescriptorProto.TYPE_UINT32: self.__int_ast,
            FieldDescriptorProto.TYPE_UINT64: self.__int_ast,
            FieldDescriptorProto.TYPE_SINT32: self.__int_ast,
            FieldDescriptorProto.TYPE_SINT64: self.__int_ast,
            FieldDescriptorProto.TYPE_FIXED32: self.__int_ast,
            FieldDescriptorProto.TYPE_FIXED64: self.__int_ast,
            FieldDescriptorProto.TYPE_SFIXED32: self.__int_ast,
            FieldDescriptorProto.TYPE_SFIXED64: self.__int_ast,
            FieldDescriptorProto.TYPE_FLOAT: self.__float_ast,
            FieldDescriptorProto.TYPE_DOUBLE: self.__float_ast,
            FieldDescriptorProto.TYPE_STRING: self.__str_ast,
        }

        self.__message_types = {
            FieldDescriptorProto.Type.TYPE_MESSAGE,
            FieldDescriptorProto.Type.TYPE_ENUM,
        }
        self.__infos = infos

        assert (
            set(self.__iter_field_type_enum()) - (self.__builtin.keys() | self.__message_types)
        ) == set(), "not all possible field types are covered"
        assert self.__builtin.keys() & self.__message_types == set(), "field type should be either builtin or a message"

    def resolve_field_type(self, proto: FieldDescriptorProto) -> ast.expr:
        type_ = proto.type
        is_many = proto.label == FieldDescriptorProto.Label.LABEL_REPEATED

        if type_ in self.__message_types:
            info = self.__infos[proto.type_name]

            if isinstance(info, (EnumInfo, MessageInfo)):
                ref = build_attr(*info.ref)

            elif isinstance(info, MapEntryInfo):
                is_many = False
                ref = build_generic_ref(
                    build_attr("typing", "Mapping"),
                    self.resolve_field_type(info.key),
                    self.resolve_field_type(info.value),
                )

            else:
                t.assert_never(info)

        else:
            ref = self.__builtin[type_]

        if is_many:
            ref = build_generic_ref(build_attr("typing", "Sequence"), ref)

        return ref

    def resolve_type_ref(self, ref: str) -> ast.expr:
        info = self.__infos[ref]
        if not isinstance(info, MessageInfo):
            raise ValueError("invalid method input type", info, ref)

        return build_attr(*info.ref)

    @classmethod
    def __iter_field_type_enum(cls) -> t.Iterable[FieldDescriptorProto.Type.ValueType]:
        for name in dir(FieldDescriptorProto.Type):
            if name.startswith("TYPE_"):
                yield getattr(FieldDescriptorProto.Type, name)
