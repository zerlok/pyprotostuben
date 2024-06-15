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
from pyprotostuben.protobuf.registry import TypeRegistry
from pyprotostuben.protobuf.visitor.abc import Proto, visit, ProtoVisitor
from pyprotostuben.protobuf.visitor.decorator import EnterProtoVisitorDecorator
from pyprotostuben.protobuf.visitor.dfs import DFSWalkingProtoVisitor
from pyprotostuben.protobuf.visitor.stack import ProtoStackVisitorDecorator, ProtoFileStackVisitorDecorator
from pyprotostuben.python.info import TypeInfo, ModuleInfo
from pyprotostuben.stack import MutableStack, Stack


@dataclass(frozen=True)
class CodeGeneratorContext:
    request: CodeGeneratorRequest
    params: Parameters
    files: t.Sequence[ProtoFile]
    file_registry: t.Mapping[str, ProtoFile]
    type_registry: TypeRegistry


class ContextBuilder(ProtoVisitor, LoggerMixin):
    @classmethod
    def build(cls, request: CodeGeneratorRequest) -> CodeGeneratorContext:
        parser = ParameterParser()
        file_stack: MutableStack[ProtoFile] = MutableStack()
        proto_stack: MutableStack[Proto] = MutableStack()
        file_registry: t.Dict[str, ProtoFile] = {}
        type_registry: t.Dict[str, TypeInfo] = {}

        visit(
            DFSWalkingProtoVisitor(
                ProtoFileStackVisitorDecorator(file_stack),
                ProtoStackVisitorDecorator(proto_stack),
                EnterProtoVisitorDecorator(cls(file_stack, proto_stack, file_registry, type_registry)),
            ),
            *request.proto_file,
        )

        return CodeGeneratorContext(
            request=request,
            params=parser.parse(request.parameter),
            files=[file_registry[file.name] for file in request.proto_file],
            file_registry=file_registry,
            type_registry=TypeRegistry(type_registry),
        )

    def __init__(
        self,
        file_stack: Stack[ProtoFile],
        proto_stack: Stack[Proto],
        file_registry: t.Dict[str, ProtoFile],
        type_registry: t.Dict[str, TypeInfo],
    ) -> None:
        self.__file_stack = file_stack
        self.__proto_stack = proto_stack
        self.__file_registry = file_registry
        self.__type_registry = type_registry

    @property
    def file(self) -> ProtoFile:
        return self.__file_stack.get_last()

    def visit_file_descriptor_proto(self, proto: FileDescriptorProto) -> None:
        file = ProtoFile(proto)
        self.__file_registry[proto.name] = file

        self._log.debug("visited", file=file)

    def visit_enum_descriptor_proto(self, proto: EnumDescriptorProto) -> None:
        self.__register_type(self.file.pb2_message, proto.name)

    def visit_enum_value_descriptor_proto(self, proto: EnumValueDescriptorProto) -> None:
        pass

    def visit_descriptor_proto(self, proto: DescriptorProto) -> None:
        self.__register_type(self.file.pb2_message, proto.name)

    def visit_oneof_descriptor_proto(self, proto: OneofDescriptorProto) -> None:
        pass

    def visit_field_descriptor_proto(self, proto: FieldDescriptorProto) -> None:
        pass

    def visit_service_descriptor_proto(self, proto: ServiceDescriptorProto) -> None:
        self.__register_type(self.file.pb2_grpc, proto.name)

    def visit_method_descriptor_proto(self, proto: MethodDescriptorProto) -> None:
        pass

    def __register_type(self, module: ModuleInfo, name: str) -> TypeInfo:
        parts = [desc.name for desc in self.__proto_stack[1:]]
        proto_path = ".".join(parts)
        qualname = f".{self.file.descriptor.package}.{proto_path}"
        type_info = self.__type_registry[qualname] = TypeInfo.create(module, *parts)

        self._log.debug("registered", qualname=qualname, type_info=type_info)

        return type_info
