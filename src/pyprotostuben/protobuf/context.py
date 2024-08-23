import typing as t
from dataclasses import dataclass

from google.protobuf.compiler.plugin_pb2 import CodeGeneratorRequest
from google.protobuf.descriptor_pb2 import (
    DescriptorProto,
    EnumDescriptorProto,
    EnumValueDescriptorProto,
    FieldDescriptorProto,
    FileDescriptorProto,
    MethodDescriptorProto,
    OneofDescriptorProto,
    ServiceDescriptorProto,
)

from pyprotostuben.logging import LoggerMixin
from pyprotostuben.protobuf.file import ProtoFile
from pyprotostuben.protobuf.parser import ParameterParser, Parameters
from pyprotostuben.protobuf.registry import (
    EnumInfo,
    MapEntryPlaceholder,
    MessageInfo,
    TypeRegistry,
)
from pyprotostuben.protobuf.visitor.abc import Proto, visit
from pyprotostuben.protobuf.visitor.decorator import ProtoVisitorDecorator
from pyprotostuben.protobuf.visitor.dfs import DFSWalkingProtoVisitor
from pyprotostuben.python.info import ModuleInfo
from pyprotostuben.stack import MutableStack


@dataclass(frozen=True)
class CodeGeneratorContext:
    request: CodeGeneratorRequest
    params: Parameters
    files: t.Sequence[ProtoFile]
    registry: TypeRegistry


class ContextBuilder(ProtoVisitorDecorator, LoggerMixin):
    @classmethod
    def build(cls, request: CodeGeneratorRequest) -> CodeGeneratorContext:
        parser = ParameterParser()
        files: t.Dict[str, ProtoFile] = {}
        infos: t.Dict[str, t.Union[EnumInfo, MessageInfo]] = {}
        map_entries: t.Dict[str, MapEntryPlaceholder] = {}

        visit(DFSWalkingProtoVisitor(cls(files, infos, map_entries)), *request.proto_file)

        return CodeGeneratorContext(
            request=request,
            params=parser.parse(request.parameter),
            files=[files[name] for name in request.file_to_generate],
            registry=TypeRegistry(infos, map_entries),
        )

    def __init__(
        self,
        files: t.MutableMapping[str, ProtoFile],
        infos: t.MutableMapping[str, t.Union[EnumInfo, MessageInfo]],
        map_entries: t.MutableMapping[str, MapEntryPlaceholder],
    ) -> None:
        self.__file_stack: MutableStack[ProtoFile] = MutableStack()
        self.__proto_stack: MutableStack[Proto] = MutableStack()
        self.__files = files
        self.__infos = infos
        self.__map_entries = map_entries

    def enter_file_descriptor_proto(self, proto: FileDescriptorProto) -> None:
        file = ProtoFile(proto)
        self.__files[proto.name] = file
        self.__file_stack.put(file)

    def leave_file_descriptor_proto(self, _: FileDescriptorProto) -> None:
        file = self.__file_stack.pop()
        self._log.debug("visited", file=file)

    def enter_enum_descriptor_proto(self, proto: EnumDescriptorProto) -> None:
        self.__proto_stack.put(proto)

    def leave_enum_descriptor_proto(self, _: EnumDescriptorProto) -> None:
        self.__register_enum()
        self.__proto_stack.pop()

    def enter_enum_value_descriptor_proto(self, proto: EnumValueDescriptorProto) -> None:
        self.__proto_stack.put(proto)

    def leave_enum_value_descriptor_proto(self, _: EnumValueDescriptorProto) -> None:
        self.__proto_stack.pop()

    def enter_descriptor_proto(self, proto: DescriptorProto) -> None:
        self.__proto_stack.put(proto)

    def leave_descriptor_proto(self, proto: DescriptorProto) -> None:
        if proto.options.map_entry:
            self.__register_map_entry(
                self.__find_field_by_name(proto.field, "key"),
                self.__find_field_by_name(proto.field, "value"),
            )

        else:
            self.__register_message()

        self.__proto_stack.pop()

    def enter_oneof_descriptor_proto(self, proto: OneofDescriptorProto) -> None:
        self.__proto_stack.put(proto)

    def leave_oneof_descriptor_proto(self, _: OneofDescriptorProto) -> None:
        self.__proto_stack.pop()

    def enter_field_descriptor_proto(self, proto: FieldDescriptorProto) -> None:
        self.__proto_stack.put(proto)

    def leave_field_descriptor_proto(self, _: FieldDescriptorProto) -> None:
        self.__proto_stack.pop()

    def enter_service_descriptor_proto(self, proto: ServiceDescriptorProto) -> None:
        self.__proto_stack.put(proto)

    def leave_service_descriptor_proto(self, _: ServiceDescriptorProto) -> None:
        self.__proto_stack.pop()

    def enter_method_descriptor_proto(self, proto: MethodDescriptorProto) -> None:
        self.__proto_stack.put(proto)

    def leave_method_descriptor_proto(self, _: MethodDescriptorProto) -> None:
        self.__proto_stack.pop()

    def __register_enum(self) -> None:
        qualname, module, ns = self.__build_type()
        info = self.__infos[qualname] = EnumInfo(module, ns)

        self._log.info("registered", qualname=qualname, info=info)

    def __register_message(self) -> None:
        qualname, module, ns = self.__build_type()
        info = self.__infos[qualname] = MessageInfo(module, ns)

        self._log.info("registered", qualname=qualname, info=info)

    def __register_map_entry(self, key: FieldDescriptorProto, value: FieldDescriptorProto) -> None:
        qualname, module, _ = self.__build_type()
        placeholder = self.__map_entries[qualname] = MapEntryPlaceholder(module, key, value)

        self._log.info("registered", qualname=qualname, placeholder=placeholder)

    def __build_type(self) -> t.Tuple[str, ModuleInfo, t.Sequence[str]]:
        file = self.__file_stack.get_last()
        ns = [desc.name for desc in self.__proto_stack]
        proto_path = ".".join(ns)

        return f".{file.descriptor.package}.{proto_path}", file.pb2_message, ns

    def __find_field_by_name(self, fields: t.Sequence[FieldDescriptorProto], name: str) -> FieldDescriptorProto:
        for field in fields:
            if field.name == name:
                return field

        msg = "field not found"
        raise ValueError(msg, name, fields)
