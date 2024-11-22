import typing as t
from dataclasses import dataclass

from google.protobuf.descriptor_pb2 import SourceCodeInfo

from pyprotostuben.codegen.module_ast import ModuleASTContext
from pyprotostuben.codegen.mypy.context import GRPCContext, MessageContext
from pyprotostuben.logging import LoggerMixin
from pyprotostuben.protobuf.builder.grpc import MethodInfo
from pyprotostuben.protobuf.builder.message import FieldInfo
from pyprotostuben.protobuf.file import ProtoFile
from pyprotostuben.protobuf.registry import MapEntryInfo, TypeRegistry
from pyprotostuben.protobuf.visitor.decorator import ProtoVisitorDecorator
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
from pyprotostuben.stack import MutableStack


@dataclass()
class MypyStubContext(ModuleASTContext):
    messages: MutableStack[MessageContext]
    grpcs: MutableStack[GRPCContext]


class MypyStubASTGenerator(ProtoVisitorDecorator[MypyStubContext], LoggerMixin):
    def __init__(
        self,
        registry: TypeRegistry,
        message_context_factory: t.Callable[[ProtoFile], MessageContext],
        grpc_context_factory: t.Callable[[ProtoFile], GRPCContext],
    ) -> None:
        self.__registry = registry
        self.__message_context_factory = message_context_factory
        self.__grpc_context_factory = grpc_context_factory

    def enter_file_descriptor_proto(self, context: FileDescriptorContext[MypyStubContext]) -> None:
        context.meta.messages.put(self.__message_context_factory(context.file))
        context.meta.grpcs.put(self.__grpc_context_factory(context.file))

    def leave_file_descriptor_proto(self, context: FileDescriptorContext[MypyStubContext]) -> None:
        message = context.meta.messages.pop()
        grpc = context.meta.grpcs.pop()

        context.meta.modules.update(
            {
                message.module.stub_file: message.builder.build_protobuf_message_module(
                    deps=message.external_modules,
                    body=message.nested,
                ),
                grpc.module.stub_file: grpc.builder.build_grpc_module(
                    deps=grpc.external_modules,
                    body=grpc.nested,
                ),
            }
        )

    def enter_enum_descriptor_proto(self, context: EnumDescriptorContext[MypyStubContext]) -> None:
        parent = context.meta.messages.get_last()

        context.meta.messages.put(parent.sub())

    def leave_enum_descriptor_proto(self, context: EnumDescriptorContext[MypyStubContext]) -> None:
        message = context.meta.messages.pop()
        parent = context.meta.messages.get_last()
        builder = message.builder

        parent.nested.append(
            builder.build_protobuf_enum_def(
                name=context.item.name,
                doc=self.__get_doc(context.location),
                nested=message.nested,
            )
        )

    def enter_enum_value_descriptor_proto(self, _: EnumValueDescriptorContext[MypyStubContext]) -> None:
        pass

    def leave_enum_value_descriptor_proto(self, context: EnumValueDescriptorContext[MypyStubContext]) -> None:
        parent = context.meta.messages.get_last()
        builder = parent.builder

        parent.nested.extend(
            builder.build_protobuf_enum_value_def(
                name=context.item.name,
                doc=self.__get_doc(context.location),
                value=context.item.number,
            )
        )

    def enter_descriptor_proto(self, context: DescriptorContext[MypyStubContext]) -> None:
        parent = context.meta.messages.get_last()

        context.meta.messages.put(parent.sub())

    def leave_descriptor_proto(self, context: DescriptorContext[MypyStubContext]) -> None:
        message = context.meta.messages.pop()

        if context.item.options.map_entry:
            return

        parent = context.meta.messages.get_last()
        builder = message.builder

        parent.nested.append(
            builder.build_protobuf_message_def(
                name=context.item.name,
                doc=self.__get_doc(context.location),
                nested=message.nested,
                fields=message.fields,
            ),
        )

    def enter_oneof_descriptor_proto(self, _: OneofDescriptorContext[MypyStubContext]) -> None:
        pass

    def leave_oneof_descriptor_proto(self, context: OneofDescriptorContext[MypyStubContext]) -> None:
        info = context.meta.messages.get_last()
        info.oneof_groups.append(context.item.name)

    def enter_field_descriptor_proto(self, _: FieldDescriptorContext[MypyStubContext]) -> None:
        pass

    def leave_field_descriptor_proto(self, context: FieldDescriptorContext[MypyStubContext]) -> None:
        is_optional = context.item.proto3_optional
        message = context.meta.messages.get_last()
        builder = message.builder

        info = self.__registry.resolve_proto_field(context.item)

        annotation = builder.build_protobuf_type_ref(info)
        if not isinstance(info, MapEntryInfo) and context.item.label == context.item.Label.LABEL_REPEATED:
            annotation = builder.build_protobuf_repeated_ref(annotation)

        message.fields.append(
            FieldInfo(
                name=context.item.name,
                annotation=annotation,
                doc=self.__get_doc(context.location),
                optional=is_optional,
                default=None,
                # TODO: support proto.default_value
                oneof_group=message.oneof_groups[context.item.oneof_index]
                if not is_optional and context.item.HasField("oneof_index")
                else None,
            ),
        )

    def enter_service_descriptor_proto(self, context: ServiceDescriptorContext[MypyStubContext]) -> None:
        parent = context.meta.grpcs.get_last()

        context.meta.grpcs.put(parent.sub())

    def leave_service_descriptor_proto(self, context: ServiceDescriptorContext[MypyStubContext]) -> None:
        grpc = context.meta.grpcs.pop()
        parent = context.meta.grpcs.get_last()
        builder = grpc.builder

        doc = self.__get_doc(context.location)
        parent.nested.extend(builder.build_grpc_servicer_defs(f"{context.item.name}Servicer", doc, grpc.methods))
        parent.nested.extend(builder.build_grpc_stub_defs(f"{context.item.name}Stub", doc, grpc.methods))

    def enter_method_descriptor_proto(self, context: MethodDescriptorContext[MypyStubContext]) -> None:
        pass

    def leave_method_descriptor_proto(self, context: MethodDescriptorContext[MypyStubContext]) -> None:
        grpc = context.meta.grpcs.get_last()
        builder = grpc.builder

        grpc.methods.append(
            MethodInfo(
                name=context.item.name,
                doc=self.__get_doc(context.location),
                client_input=builder.build_grpc_message_ref(
                    self.__registry.resolve_proto_method_client_input(context.item)
                ),
                client_streaming=context.item.client_streaming,
                server_output=builder.build_grpc_message_ref(
                    self.__registry.resolve_proto_method_server_output(context.item)
                ),
                server_streaming=context.item.server_streaming,
            ),
        )

    def __get_doc(self, location: t.Optional[SourceCodeInfo.Location]) -> t.Optional[str]:
        if location is None:
            return None

        blocks: t.List[str] = []
        blocks.extend(comment.strip() for comment in location.leading_detached_comments)

        if location.HasField("leading_comments"):
            blocks.append(location.leading_comments.strip())

        if location.HasField("trailing_comments"):
            blocks.append(location.trailing_comments.strip())

        return "\n\n".join(blocks)
