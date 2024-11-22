import typing as t
from dataclasses import dataclass

from google.protobuf.compiler.plugin_pb2 import CodeGeneratorRequest
from google.protobuf.descriptor_pb2 import (
    FieldDescriptorProto,
)

from pyprotostuben.logging import LoggerMixin
from pyprotostuben.protobuf.file import ProtoFile
from pyprotostuben.protobuf.parser import CodeGeneratorParameters, ParameterParser
from pyprotostuben.protobuf.registry import (
    EnumInfo,
    MapEntryPlaceholder,
    MessageInfo,
    TypeRegistry,
)
from pyprotostuben.protobuf.visitor.abc import ProtoVisitor
from pyprotostuben.protobuf.visitor.decorator import LeaveProtoVisitorDecorator
from pyprotostuben.protobuf.visitor.model import (
    BaseContext,
    DescriptorContext,
    EnumDescriptorContext,
    EnumValueDescriptorContext,
    FieldDescriptorContext,
    FileDescriptorContext,
    MethodDescriptorContext,
    OneofDescriptorContext,
    Proto,
    ServiceDescriptorContext,
)
from pyprotostuben.protobuf.visitor.walker import Walker
from pyprotostuben.python.info import ModuleInfo


@dataclass(frozen=True)
class CodeGeneratorContext:
    request: CodeGeneratorRequest
    params: CodeGeneratorParameters
    files: t.Sequence[ProtoFile]
    registry: TypeRegistry


class ContextBuilder(ProtoVisitor[object], LoggerMixin):
    @classmethod
    def build(cls, request: CodeGeneratorRequest) -> CodeGeneratorContext:
        parser = ParameterParser()
        files: t.Dict[str, ProtoFile] = {}
        infos: t.Dict[str, t.Union[EnumInfo, MessageInfo]] = {}
        map_entries: t.Dict[str, MapEntryPlaceholder] = {}

        Walker(LeaveProtoVisitorDecorator(cls(files, infos, map_entries))).walk(None, *request.proto_file)

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
        self.__files = files
        self.__infos = infos
        self.__map_entries = map_entries

    def visit_file_descriptor_proto(self, context: FileDescriptorContext[object]) -> None:
        self.__register_file(context)
        self._log.debug("visited", file=context.file)

    def visit_enum_descriptor_proto(self, context: EnumDescriptorContext[object]) -> None:
        self.__register_enum(context)

    def visit_enum_value_descriptor_proto(self, _: EnumValueDescriptorContext[object]) -> None:
        pass

    def visit_descriptor_proto(self, context: DescriptorContext[object]) -> None:
        proto = context.item

        if proto.options.map_entry:
            self.__register_map_entry(
                context,
                self.__find_field_by_name(proto.field, "key"),
                self.__find_field_by_name(proto.field, "value"),
            )

        else:
            self.__register_message(context)

    def visit_oneof_descriptor_proto(self, _: OneofDescriptorContext[object]) -> None:
        pass

    def visit_field_descriptor_proto(self, _: FieldDescriptorContext[object]) -> None:
        pass

    def visit_service_descriptor_proto(self, _: ServiceDescriptorContext[object]) -> None:
        pass

    def visit_method_descriptor_proto(self, _: MethodDescriptorContext[object]) -> None:
        pass

    def __register_file(self, context: FileDescriptorContext[object]) -> None:
        self.__files[context.item.name] = context.file

    def __register_enum(self, context: EnumDescriptorContext[object]) -> None:
        qualname, module, ns = self.__build_type(context.root_context, context)
        info = self.__infos[qualname] = EnumInfo(module, ns)

        self._log.info("registered", qualname=qualname, info=info)

    def __register_message(self, context: t.Union[FileDescriptorContext[object], DescriptorContext[object]]) -> None:
        qualname, module, ns = self.__build_type(
            root=context.root_context if isinstance(context, DescriptorContext) else context,
            context=context,
        )
        info = self.__infos[qualname] = MessageInfo(module, ns)

        self._log.info("registered", qualname=qualname, info=info)

    def __register_map_entry(
        self,
        context: DescriptorContext[object],
        key: FieldDescriptorProto,
        value: FieldDescriptorProto,
    ) -> None:
        qualname, module, _ = self.__build_type(context.root_context, context)
        placeholder = self.__map_entries[qualname] = MapEntryPlaceholder(module, key, value)

        self._log.info("registered", qualname=qualname, placeholder=placeholder)

    def __build_type(
        self,
        root: FileDescriptorContext[object],
        context: BaseContext[object, Proto],
    ) -> t.Tuple[str, ModuleInfo, t.Sequence[str]]:
        ns = [desc.name for desc in context.parts[1:]]
        proto_path = ".".join(ns)

        qualname = f".{root.item.package}.{proto_path}"
        module = root.file.pb2_message

        return qualname, module, ns

    def __find_field_by_name(self, fields: t.Sequence[FieldDescriptorProto], name: str) -> FieldDescriptorProto:
        for field in fields:
            if field.name == name:
                return field

        msg = "field not found"
        raise ValueError(msg, name, fields)
