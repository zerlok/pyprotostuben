import typing as t
from dataclasses import dataclass

from google.protobuf.compiler.plugin_pb2 import CodeGeneratorRequest
from google.protobuf.descriptor_pb2 import (
    FileDescriptorProto,
    EnumDescriptorProto,
    EnumValueDescriptorProto,
    DescriptorProto,
    OneofDescriptorProto,
    MethodDescriptorProto,
    ServiceDescriptorProto,
    FieldDescriptorProto,
)

from pyprotostuben.logging import LoggerMixin
from pyprotostuben.protobuf.file import ProtoFile
from pyprotostuben.protobuf.parser import Parameters, ParameterParser
from pyprotostuben.protobuf.registry import ProtoInfo, MapEntryInfo, MessageInfo, EnumInfo, TypeRegistry
from pyprotostuben.protobuf.visitor.abc import Proto, visit
from pyprotostuben.protobuf.visitor.decorator import ProtoVisitorDecorator
from pyprotostuben.protobuf.visitor.dfs import DFSWalkingProtoVisitor
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
        infos: t.Dict[str, ProtoInfo] = {}

        visit(
            DFSWalkingProtoVisitor(
                # ProtoFileStackVisitorDecorator(file_stack),
                # ProtoStackVisitorDecorator(proto_stack),
                cls(files, infos),
            ),
            *request.proto_file,
        )

        return CodeGeneratorContext(
            request=request,
            params=parser.parse(request.parameter),
            files=[files[file.name] for file in request.proto_file],
            registry=TypeRegistry(infos),
        )

    def __init__(
        self,
        files: t.Dict[str, ProtoFile],
        infos: t.Dict[str, ProtoInfo],
    ) -> None:
        self.__file_stack: MutableStack[ProtoFile] = MutableStack()
        self.__proto_stack: MutableStack[Proto] = MutableStack()
        self.__files = files
        self.__infos = infos

    @property
    def file(self) -> ProtoFile:
        return self.__file_stack.get_last()

    def enter_file_descriptor_proto(self, proto: FileDescriptorProto) -> None:
        file = ProtoFile(proto)
        self.__files[proto.name] = file
        self.__file_stack.put(file)

    def leave_file_descriptor_proto(self, proto: FileDescriptorProto) -> None:
        file = self.__file_stack.pop()
        self._log.debug("visited", file=file)

    def enter_enum_descriptor_proto(self, proto: EnumDescriptorProto) -> None:
        self.__proto_stack.put(proto)

    def leave_enum_descriptor_proto(self, proto: EnumDescriptorProto) -> None:
        self.__register_enum()
        self.__proto_stack.pop()

    def enter_enum_value_descriptor_proto(self, proto: EnumValueDescriptorProto) -> None:
        self.__proto_stack.put(proto)

    def leave_enum_value_descriptor_proto(self, proto: EnumValueDescriptorProto) -> None:
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

    def leave_oneof_descriptor_proto(self, proto: OneofDescriptorProto) -> None:
        self.__proto_stack.pop()

    def enter_field_descriptor_proto(self, proto: FieldDescriptorProto) -> None:
        self.__proto_stack.put(proto)

    def leave_field_descriptor_proto(self, proto: FieldDescriptorProto) -> None:
        self.__proto_stack.pop()

    def enter_service_descriptor_proto(self, proto: ServiceDescriptorProto) -> None:
        self.__proto_stack.put(proto)

    def leave_service_descriptor_proto(self, proto: ServiceDescriptorProto) -> None:
        self.__proto_stack.pop()

    def enter_method_descriptor_proto(self, proto: MethodDescriptorProto) -> None:
        self.__proto_stack.put(proto)

    def leave_method_descriptor_proto(self, proto: MethodDescriptorProto) -> None:
        self.__proto_stack.pop()

    def __register_enum(self) -> None:
        qualname, parts = self.__build_type_ref()
        info = self.__infos[qualname] = EnumInfo(parts)

        self._log.info("registered", qualname=qualname, info=info)

    def __register_message(self) -> None:
        qualname, parts = self.__build_type_ref()
        info = self.__infos[qualname] = MessageInfo(parts)

        self._log.info("registered", qualname=qualname, info=info)

    def __register_map_entry(self, key: FieldDescriptorProto, value: FieldDescriptorProto) -> None:
        qualname, parts = self.__build_type_ref()
        info = self.__infos[qualname] = MapEntryInfo(key=key, value=value)

        self._log.info("registered", qualname=qualname, info=info)

    def __build_type_ref(self) -> t.Tuple[str, t.Sequence[str]]:
        ns = [desc.name for desc in self.__proto_stack]
        proto_path = ".".join(ns)

        return f".{self.file.descriptor.package}.{proto_path}", [*self.file.pb2_message.parts, *ns]

    def __find_field_by_name(self, fields: t.Sequence[FieldDescriptorProto], name: str) -> FieldDescriptorProto:
        for field in fields:
            if field.name == name:
                return field

        raise ValueError("field not found", name, fields)
