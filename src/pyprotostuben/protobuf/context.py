import typing as t
from dataclasses import dataclass, field

from google.protobuf.compiler.plugin_pb2 import CodeGeneratorRequest
from google.protobuf.descriptor_pb2 import FieldDescriptorProto

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
    DescriptorContext,
    EnumDescriptorContext,
    EnumValueDescriptorContext,
    FieldDescriptorContext,
    FileDescriptorContext,
    MethodDescriptorContext,
    OneofDescriptorContext,
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


@dataclass()
class BuildContext:
    files: t.Dict[str, ProtoFile] = field(default_factory=dict)
    types: t.Dict[str, t.Union[EnumInfo, MessageInfo]] = field(default_factory=dict)
    map_entries: t.Dict[str, MapEntryPlaceholder] = field(default_factory=dict)


class ContextBuilder(ProtoVisitor[BuildContext], LoggerMixin):
    def visit_file_descriptor_proto(self, context: FileDescriptorContext[BuildContext]) -> None:
        self.__register_file(context)
        self._log.debug("visited", file=context.file)

    def visit_enum_descriptor_proto(self, context: EnumDescriptorContext[BuildContext]) -> None:
        self.__register_enum(context)

    def visit_enum_value_descriptor_proto(self, _: EnumValueDescriptorContext[BuildContext]) -> None:
        pass

    def visit_descriptor_proto(self, context: DescriptorContext[BuildContext]) -> None:
        proto = context.proto

        if proto.options.map_entry:
            self.__register_map_entry(
                context,
                self.__find_field_by_name(proto.field, "key"),
                self.__find_field_by_name(proto.field, "value"),
            )

        else:
            self.__register_message(context)

    def visit_oneof_descriptor_proto(self, _: OneofDescriptorContext[BuildContext]) -> None:
        pass

    def visit_field_descriptor_proto(self, _: FieldDescriptorContext[BuildContext]) -> None:
        pass

    def visit_service_descriptor_proto(self, _: ServiceDescriptorContext[BuildContext]) -> None:
        pass

    def visit_method_descriptor_proto(self, _: MethodDescriptorContext[BuildContext]) -> None:
        pass

    # TODO: speed up with multiprocessing by files
    def build(self, request: CodeGeneratorRequest) -> CodeGeneratorContext:
        parser = ParameterParser()
        walker = Walker(LeaveProtoVisitorDecorator(self))

        context = BuildContext()

        # TODO: consider `request.source_file_descriptors` usage to keep options
        walker.walk(*request.proto_file, meta=context)

        return CodeGeneratorContext(
            request=request,
            params=parser.parse(request.parameter),
            files=[context.files[name] for name in request.file_to_generate],
            registry=TypeRegistry(context.types, context.map_entries),
        )

    def __register_file(self, context: FileDescriptorContext[BuildContext]) -> None:
        context.meta.files[context.proto.name] = context.file

    def __register_enum(self, context: EnumDescriptorContext[BuildContext]) -> None:
        qualname, module, ns = self.__build_type(context.root, context)
        type_ = context.meta.types[qualname] = EnumInfo(module, ns)

        self._log.info("registered", qualname=qualname, type_=type_)

    def __register_message(
        self,
        context: t.Union[FileDescriptorContext[BuildContext], DescriptorContext[BuildContext]],
    ) -> None:
        qualname, module, ns = self.__build_type(
            root=context.root if isinstance(context, DescriptorContext) else context,
            context=context,
        )
        type_ = context.meta.types[qualname] = MessageInfo(module, ns)

        self._log.info("registered", qualname=qualname, type_=type_)

    def __register_map_entry(
        self,
        context: DescriptorContext[BuildContext],
        key: FieldDescriptorProto,
        value: FieldDescriptorProto,
    ) -> None:
        qualname, module, _ = self.__build_type(context.root, context)
        placeholder = context.meta.map_entries[qualname] = MapEntryPlaceholder(module, key, value)

        self._log.info("registered", qualname=qualname, placeholder=placeholder)

    def __build_type(
        self,
        root: FileDescriptorContext[BuildContext],
        context: t.Union[
            FileDescriptorContext[BuildContext],
            EnumDescriptorContext[BuildContext],
            DescriptorContext[BuildContext],
        ],
    ) -> t.Tuple[str, ModuleInfo, t.Sequence[str]]:
        ns = [part.proto.name for part in context.parts[1:]]
        proto_path = ".".join(ns)

        qualname = f".{root.proto.package}.{proto_path}"
        module = root.file.pb2_module

        return qualname, module, ns

    def __find_field_by_name(self, fields: t.Sequence[FieldDescriptorProto], name: str) -> FieldDescriptorProto:
        for proto in fields:
            if proto.name == name:
                return proto

        msg = "field not found"
        raise ValueError(msg, name, fields)
