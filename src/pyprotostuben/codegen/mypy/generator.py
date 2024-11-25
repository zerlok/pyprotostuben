import ast
import typing as t
from dataclasses import dataclass

from google.protobuf.descriptor import (
    FileDescriptor,
    MethodDescriptor,
    ServiceDescriptor,
)

from pyprotostuben.codegen.module_ast import ModuleASTContext
from pyprotostuben.codegen.mypy.context import GRPCContext, MessageContext
from pyprotostuben.logging import LoggerMixin
from pyprotostuben.protobuf.builder.grpc import MethodInfo
from pyprotostuben.protobuf.builder.message import FieldInfo
from pyprotostuben.protobuf.location import build_docstring
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
from pyprotostuben.python.info import TypeInfo
from pyprotostuben.stack import MutableStack


@dataclass()
class MypyStubContext(ModuleASTContext):
    descriptors: MutableStack[MessageContext]
    grpcs: MutableStack[GRPCContext]


# TODO: consider use of inline type dicts, see: https://mypy.readthedocs.io/en/stable/typed_dict.html#inline-typeddict-types
class MypyStubASTGenerator(ProtoVisitorDecorator[MypyStubContext], LoggerMixin):
    def __init__(self, registry: TypeRegistry) -> None:
        self.__registry = registry

    def enter_file_descriptor_proto(self, context: FileDescriptorContext[MypyStubContext]) -> None:
        pass

    def leave_file_descriptor_proto(self, context: FileDescriptorContext[MypyStubContext]) -> None:
        message = context.meta.descriptors.get_last()
        grpc = context.meta.grpcs.get_last()

        context.meta.modules.update(
            {
                message.module.stub_file: message.builder.build_protobuf_message_module(
                    body=[
                        *message.nested,
                        # *message.builder.build_protobuf_message_field_stubs(message.fields),
                        # *self.__build_service_descriptors(context, grpc),
                        # *(self.__build_extension_field(message.builder.inner, field) for field in message.fields),
                        # *self.__build_file_descriptor(context, message),
                    ],
                ),
                grpc.module.stub_file: grpc.builder.build_grpc_module(
                    body=grpc.nested,
                ),
            }
        )

    def enter_enum_descriptor_proto(self, context: EnumDescriptorContext[MypyStubContext]) -> None:
        parent = context.meta.descriptors.get_last()

        context.meta.descriptors.put(parent.sub())

    def leave_enum_descriptor_proto(self, context: EnumDescriptorContext[MypyStubContext]) -> None:
        message = context.meta.descriptors.pop()
        parent = context.meta.descriptors.get_last()
        builder = message.builder

        parent.nested.append(
            builder.build_protobuf_enum_def(
                name=context.proto.name,
                doc=build_docstring(context.location),
                nested=message.nested,
            )
        )

    def enter_enum_value_descriptor_proto(self, _: EnumValueDescriptorContext[MypyStubContext]) -> None:
        pass

    def leave_enum_value_descriptor_proto(self, context: EnumValueDescriptorContext[MypyStubContext]) -> None:
        parent = context.meta.descriptors.get_last()
        builder = parent.builder

        parent.nested.extend(
            builder.build_protobuf_enum_value_def(
                name=context.proto.name,
                doc=build_docstring(context.location),
                value=context.proto.number,
            )
        )

    def enter_descriptor_proto(self, context: DescriptorContext[MypyStubContext]) -> None:
        parent = context.meta.descriptors.get_last()

        context.meta.descriptors.put(parent.sub())

    def leave_descriptor_proto(self, context: DescriptorContext[MypyStubContext]) -> None:
        message = context.meta.descriptors.pop()

        if context.proto.options.map_entry:
            return

        parent = context.meta.descriptors.get_last()
        builder = message.builder

        parent.nested.append(
            builder.build_protobuf_message_def(
                name=context.proto.name,
                doc=build_docstring(context.location),
                nested=message.nested,
                fields=message.fields,
            ),
        )

    def enter_oneof_descriptor_proto(self, _: OneofDescriptorContext[MypyStubContext]) -> None:
        pass

    def leave_oneof_descriptor_proto(self, context: OneofDescriptorContext[MypyStubContext]) -> None:
        info = context.meta.descriptors.get_last()
        info.oneof_groups.append(context.proto.name)

    def enter_field_descriptor_proto(self, _: FieldDescriptorContext[MypyStubContext]) -> None:
        pass

    def leave_field_descriptor_proto(self, context: FieldDescriptorContext[MypyStubContext]) -> None:
        is_optional = context.proto.proto3_optional
        message = context.meta.descriptors.get_last()
        builder = message.builder

        info = self.__registry.resolve_proto_field(context.proto)

        annotation = builder.build_protobuf_type_ref(info)
        if not isinstance(info, MapEntryInfo) and context.proto.label == context.proto.Label.LABEL_REPEATED:
            annotation = builder.build_protobuf_repeated_ref(annotation)

        message.fields.append(
            FieldInfo(
                name=context.proto.name,
                annotation=annotation,
                # descriptor=builder.inner.build_class_def(
                #     name="_Descriptor",
                #     bases=[builder.inner.build_ref(TypeInfo.from_type(FieldDescriptor))],
                #     body=[
                #         builder.inner.build_attr_stub(
                #             name="name",
                #             annotation=builder.inner.build_str_ref(),
                #         ),
                #     ],
                # ),
                doc=build_docstring(context.location),
                optional=is_optional,
                default=None,
                # TODO: support proto.default_value
                oneof_group=message.oneof_groups[context.proto.oneof_index]
                if not is_optional and context.proto.HasField("oneof_index")
                else None,
            ),
        )

        # if context.proto.HasField("extendee"):
        #     (context.proto)

    def enter_service_descriptor_proto(self, context: ServiceDescriptorContext[MypyStubContext]) -> None:
        parent = context.meta.grpcs.get_last()

        context.meta.grpcs.put(parent.sub())

    def leave_service_descriptor_proto(self, context: ServiceDescriptorContext[MypyStubContext]) -> None:
        grpc = context.meta.grpcs.pop()
        parent = context.meta.grpcs.get_last()
        builder = grpc.builder

        doc = build_docstring(context.location)
        parent.nested.extend(builder.build_grpc_servicer_defs(f"{context.proto.name}Servicer", doc, grpc.methods))
        parent.nested.extend(builder.build_grpc_stub_defs(f"{context.proto.name}Stub", doc, grpc.methods))

    def enter_method_descriptor_proto(self, context: MethodDescriptorContext[MypyStubContext]) -> None:
        pass

    def leave_method_descriptor_proto(self, context: MethodDescriptorContext[MypyStubContext]) -> None:
        grpc = context.meta.grpcs.get_last()
        builder = grpc.builder

        grpc.methods.append(
            MethodInfo(
                name=context.proto.name,
                doc=build_docstring(context.location),
                client_input=builder.build_grpc_message_ref(
                    self.__registry.resolve_proto_method_client_input(context.proto)
                ),
                client_streaming=context.proto.client_streaming,
                server_output=builder.build_grpc_message_ref(
                    self.__registry.resolve_proto_method_server_output(context.proto)
                ),
                server_streaming=context.proto.server_streaming,
            ),
        )

    # def __build_extension_field(
    #     self,
    #     builder: ASTBuilder,
    #     field: FieldInfo,
    # ) -> ast.stmt:
    #     return builder.build_attr_stub(
    #         name=field.name,
    #         annotation=builder.build_generic_ref(
    #             TypeInfo.build(ModuleInfo.from_obj(extension), "ExtensionDescriptor"),
    #             field.annotation,
    #         ),
    #     )

    def __build_service_descriptors(
        self,
        context: FileDescriptorContext[MypyStubContext],
        grpc: GRPCContext,
    ) -> t.Sequence[ast.stmt]:
        builder = grpc.builder.inner

        return [
            builder.build_class_def(
                name=service.name,
                bases=[builder.build_ref(TypeInfo.from_type(ServiceDescriptor))],
                body=[
                    *(
                        builder.build_class_def(
                            name=method.name,
                            bases=[builder.build_ref(TypeInfo.from_type(MethodDescriptor))],
                            body=[
                                builder.build_attr_stub(
                                    name="name",
                                    annotation=builder.build_str_ref(),
                                ),
                                builder.build_attr_stub(
                                    name="full_name",
                                    annotation=builder.build_str_ref(),
                                ),
                                builder.build_attr_stub(
                                    name="index",
                                    annotation=builder.build_int_ref(),
                                ),
                                builder.build_attr_stub(
                                    name="containing_service",
                                    annotation=builder.build_int_ref(),
                                ),
                                builder.build_attr_stub(
                                    name="input_type",
                                    annotation=builder.build_int_ref(),
                                ),
                                builder.build_attr_stub(
                                    name="output_type",
                                    annotation=builder.build_int_ref(),
                                ),
                                builder.build_attr_stub(
                                    name="client_streaming",
                                    annotation=builder.build_int_ref(),
                                ),
                                builder.build_attr_stub(
                                    name="server_streaming",
                                    annotation=builder.build_int_ref(),
                                ),
                            ],
                            is_final=True,
                        )
                        for method in service.method
                    ),
                    builder.build_typed_dict_def(
                        name="_MethodsByName",
                        items={method.name: builder.build_name(method.name) for method in service.method},
                        is_final=True,
                    ),
                ],
                is_final=True,
            )
            for service in context.proto.service
        ]

    def __build_file_descriptor(
        self,
        context: FileDescriptorContext[MypyStubContext],
        message: MessageContext,
        # grpc: GRPCContext,
    ) -> t.Sequence[ast.stmt]:
        builder = message.builder.inner

        return [
            builder.build_class_def(
                name="_FileDescriptor",
                bases=[
                    builder.build_ref(TypeInfo.from_type(FileDescriptor)),
                ],
                body=[
                    *(
                        builder.build_typed_dict_def(
                            name="_EnumTypesByName",
                            items={
                                enum_type.name: builder.build_type_ref(builder.build_name(enum_type.name))
                                for enum_type in context.proto.enum_type
                            },
                            is_final=True,
                        ),
                        builder.build_typed_dict_def(
                            name="_MessageTypesByName",
                            items={
                                message_type.name: builder.build_type_ref(builder.build_name(message_type.name))
                                for message_type in context.proto.message_type
                            },
                            is_final=True,
                        ),
                        builder.build_typed_dict_def(
                            name="_ServicesByName",
                            items={
                                service.name: builder.build_type_ref(builder.build_name(service.name))
                                for service in context.proto.service
                            },
                            is_final=True,
                        ),
                        # builder.build_typed_dict_def(
                        #     name="_ExtensionsByName",
                        #     items={field.name: ... for field in message.fields},
                        #     is_final=True,
                        # ),
                    ),
                    builder.build_attr_stub(
                        name="name",
                        annotation=builder.build_str_ref(),
                    ),
                    builder.build_attr_stub(
                        name="package",
                        annotation=builder.build_str_ref(),
                    ),
                    builder.build_attr_stub(
                        name="enum_types_by_name",
                        annotation=builder.build_name("_EnumTypesByName"),
                    ),
                    builder.build_attr_stub(
                        name="message_types_by_name",
                        annotation=builder.build_name("_MessageTypesByName"),
                    ),
                    builder.build_attr_stub(
                        name="services_by_name",
                        annotation=builder.build_name("_ServicesByName"),
                    ),
                    builder.build_attr_stub(
                        name="extensions_by_name",
                        annotation=builder.build_name("_ExtensionsByName"),
                    ),
                ],
                is_final=True,
            ),
            builder.build_attr_stub(
                name="DESCRIPTOR",
                annotation=builder.build_name("_FileDescriptor"),
                is_final=True,
            ),
        ]
