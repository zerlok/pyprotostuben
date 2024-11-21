import ast
import typing as t
from dataclasses import dataclass, field
from functools import cached_property

from pyprotostuben.codegen.module_ast import ModuleASTContext
from pyprotostuben.logging import LoggerMixin
from pyprotostuben.protobuf.builder.grpc import MethodInfo
from pyprotostuben.protobuf.registry import TypeRegistry
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
from pyprotostuben.python.ast_builder import ASTBuilder
from pyprotostuben.python.info import ModuleInfo, PackageInfo, TypeInfo
from pyprotostuben.stack import MutableStack
from pyprotostuben.string_case import camel2snake


@dataclass()
class Scope:
    methods: t.MutableSequence[MethodInfo] = field(default_factory=list)
    body: t.MutableSequence[ast.stmt] = field(default_factory=list)


@dataclass()
class BrokRPCContext(ModuleASTContext):
    builder: ASTBuilder
    module: ModuleInfo
    deps: t.MutableSet[ModuleInfo]
    scopes: MutableStack[Scope]


class BrokRPCModuleGenerator(ProtoVisitorDecorator[BrokRPCContext], LoggerMixin):
    def __init__(self, registry: TypeRegistry) -> None:
        self.__registry = registry

    def enter_file_descriptor_proto(self, context: FileDescriptorContext[BrokRPCContext]) -> None:
        context.meta.scopes.put(Scope())

    def leave_file_descriptor_proto(self, context: FileDescriptorContext[BrokRPCContext]) -> None:
        scope = context.meta.scopes.pop()

        if scope.body:
            context.meta.modules.update(
                {
                    context.meta.module.file: context.meta.builder.build_module(
                        deps=context.meta.deps,
                        doc=f"Source: {context.file.proto_path}",
                        body=scope.body,
                    ),
                }
            )

    def enter_enum_descriptor_proto(self, context: EnumDescriptorContext[BrokRPCContext]) -> None:
        pass

    def leave_enum_descriptor_proto(self, context: EnumDescriptorContext[BrokRPCContext]) -> None:
        pass

    def enter_enum_value_descriptor_proto(self, context: EnumValueDescriptorContext[BrokRPCContext]) -> None:
        pass

    def leave_enum_value_descriptor_proto(self, context: EnumValueDescriptorContext[BrokRPCContext]) -> None:
        pass

    def enter_descriptor_proto(self, context: DescriptorContext[BrokRPCContext]) -> None:
        pass

    def leave_descriptor_proto(self, context: DescriptorContext[BrokRPCContext]) -> None:
        pass

    def enter_oneof_descriptor_proto(self, context: OneofDescriptorContext[BrokRPCContext]) -> None:
        pass

    def leave_oneof_descriptor_proto(self, context: OneofDescriptorContext[BrokRPCContext]) -> None:
        pass

    def enter_field_descriptor_proto(self, context: FieldDescriptorContext[BrokRPCContext]) -> None:
        pass

    def leave_field_descriptor_proto(self, context: FieldDescriptorContext[BrokRPCContext]) -> None:
        pass

    def enter_service_descriptor_proto(self, context: ServiceDescriptorContext[BrokRPCContext]) -> None:
        context.meta.scopes.put(Scope())

    def leave_service_descriptor_proto(self, context: ServiceDescriptorContext[BrokRPCContext]) -> None:
        scope = context.meta.scopes.pop()
        parent = context.meta.scopes.get_last()

        service_class_name = f"{context.item.name}Service"
        client_class_name = f"{context.item.name}Client"

        parent.body.extend(
            [
                self.__build_service_def(context, service_class_name, scope.methods),
                self.__build_service_registrator_def(context, service_class_name, scope.methods),
                self.__build_client_def(context, client_class_name, scope.methods),
                self.__build_client_factory_def(context, client_class_name, scope.methods),
            ]
        )

    def enter_method_descriptor_proto(self, context: MethodDescriptorContext[BrokRPCContext]) -> None:
        pass

    def leave_method_descriptor_proto(self, context: MethodDescriptorContext[BrokRPCContext]) -> None:
        scope = context.meta.scopes.get_last()

        builder = context.meta.builder

        scope.methods.append(
            MethodInfo(
                name=camel2snake(context.item.name),
                doc="\n\n".join(context.comments),
                client_input=builder.build_ref(self.__registry.resolve_proto_method_client_input(context.item)),
                client_streaming=False,
                server_output=builder.build_ref(self.__registry.resolve_proto_method_server_output(context.item)),
                server_streaming=False,
            )
        )

    def __build_service_def(
        self,
        context: ServiceDescriptorContext[BrokRPCContext],
        name: str,
        methods: t.Sequence[MethodInfo],
    ) -> ast.stmt:
        builder = context.meta.builder

        return builder.build_abstract_class_def(
            name=name,
            doc="\n\n".join(context.comments),
            body=[
                builder.build_abstract_method_def(
                    name=method.name,
                    args=[
                        builder.build_pos_arg(
                            name="request",
                            annotation=builder.build_generic_ref(self.__brokrpc_request, method.client_input),
                        )
                    ],
                    returns=method.server_output,
                    is_async=True,
                    doc=method.doc,
                )
                for method in methods
            ],
        )

    def __build_service_registrator_def(
        self,
        context: ServiceDescriptorContext[BrokRPCContext],
        name: str,
        methods: t.Sequence[MethodInfo],
    ) -> ast.stmt:
        builder = context.meta.builder

        return builder.build_func_def(
            name=f"add_{camel2snake(name)}_to_server",
            args=[
                builder.build_pos_arg(
                    name="service",
                    annotation=builder.build_name(name),
                ),
                builder.build_pos_arg(
                    name="server",
                    annotation=builder.build_ref(self.__brokrpc_server),
                ),
            ],
            returns=builder.build_none_ref(),
            body=[
                builder.build_call_stmt(
                    func=builder.build_name("server", "register_unary_unary_handler"),
                    kwargs={
                        "func": builder.build_name("service", method.name),
                        "routing_key": self.__build_routing_key(context, method),
                        "serializer": self.__build_serializer(builder, method),
                    },
                )
                for method in methods
            ],
        )

    def __build_client_def(
        self,
        context: ServiceDescriptorContext[BrokRPCContext],
        name: str,
        methods: t.Sequence[MethodInfo],
    ) -> ast.stmt:
        builder = context.meta.builder

        return builder.build_class_def(
            name=name,
            doc="\n\n".join(context.comments),
            body=(
                self.__build_client_init(builder, methods),
                *(self.__build_client_call(builder, method) for method in methods),
            ),
        )

    def __build_client_init(self, builder: ASTBuilder, methods: t.Sequence[MethodInfo]) -> ast.stmt:
        return builder.build_init_def(
            args=[
                builder.build_pos_arg(
                    name=method.name,
                    annotation=builder.build_generic_ref(
                        self.__brokrpc_caller,
                        method.client_input,
                        method.server_output,
                    ),
                )
                for method in methods
            ],
            body=[
                builder.build_attr_assign(
                    target=builder.build_name("self", f"__{method.name}"),
                    value=builder.build_name(method.name),
                )
                for method in methods
            ],
        )

    def __build_client_call(self, builder: ASTBuilder, method: MethodInfo) -> ast.stmt:
        return builder.build_method_def(
            name=method.name,
            args=[
                builder.build_pos_arg(
                    name="request",
                    annotation=method.client_input,
                ),
            ],
            returns=builder.build_generic_ref(self.__brokrpc_response, method.server_output),
            doc=method.doc,
            body=[
                builder.build_return_stmt(
                    builder.build_call(
                        func=builder.build_name("self", f"__{method.name}", "invoke"),
                        args=[builder.build_name("request")],
                        is_async=True,
                    )
                ),
            ],
            is_async=True,
        )

    def __build_client_factory_def(
        self,
        context: ServiceDescriptorContext[BrokRPCContext],
        name: str,
        methods: t.Sequence[MethodInfo],
    ) -> ast.stmt:
        builder = context.meta.builder

        return builder.build_func_def(
            name="create_client",
            args=[
                builder.build_pos_arg(
                    name="client",
                    annotation=builder.build_ref(self.__brokrpc_client),
                ),
            ],
            returns=builder.build_name(name),
            is_async=True,
            is_context_manager=True,
            body=[
                builder.build_with_stmt(
                    is_async=True,
                    items=[
                        (
                            method.name,
                            self.__build_client_caller_factory(context, method),
                        )
                        for method in methods
                    ],
                    body=[
                        builder.build_yield_stmt(
                            builder.build_call(
                                func=builder.build_name(name),
                                kwargs={method.name: builder.build_name(method.name) for method in methods},
                            )
                        )
                    ],
                ),
            ],
        )

    def __build_client_caller_factory(
        self,
        context: ServiceDescriptorContext[BrokRPCContext],
        method: MethodInfo,
    ) -> ast.expr:
        builder = context.meta.builder

        return builder.build_call(
            func=builder.build_name("client", "unary_unary_caller"),
            kwargs={
                "routing_key": self.__build_routing_key(context, method),
                "serializer": self.__build_serializer(builder, method),
            },
        )

    def __build_routing_key(self, context: ServiceDescriptorContext[BrokRPCContext], method: MethodInfo) -> ast.expr:
        return ast.Constant(value=f"/{context.root.package}/{context.item.name}/{method.name}")

    def __build_serializer(self, builder: ASTBuilder, method: MethodInfo) -> ast.expr:
        return builder.build_call(
            func=builder.build_ref(self.__brokrpc_serializer),
            args=[
                method.client_input,
                method.server_output,
            ],
        )

    @cached_property
    def __brokrpc(self) -> PackageInfo:
        return PackageInfo(None, "brokrpc")

    @cached_property
    def __brokrpc_rpc(self) -> PackageInfo:
        return PackageInfo(self.__brokrpc, "rpc")

    @cached_property
    def __brokrpc_server(self) -> TypeInfo:
        return TypeInfo.build(ModuleInfo(self.__brokrpc_rpc, "server"), "Server")

    @cached_property
    def __brokrpc_client(self) -> TypeInfo:
        return TypeInfo.build(ModuleInfo(self.__brokrpc_rpc, "client"), "Client")

    @cached_property
    def __brokrpc_caller(self) -> TypeInfo:
        return TypeInfo.build(ModuleInfo(self.__brokrpc_rpc, "abc"), "Caller")

    @cached_property
    def __brokrpc_request(self) -> TypeInfo:
        return TypeInfo.build(ModuleInfo(self.__brokrpc_rpc, "model"), "Request")

    @cached_property
    def __brokrpc_response(self) -> TypeInfo:
        return TypeInfo.build(ModuleInfo(self.__brokrpc_rpc, "model"), "Response")

    @cached_property
    def __brokrpc_serializer(self) -> TypeInfo:
        return TypeInfo.build(
            ModuleInfo(PackageInfo(self.__brokrpc, "serializer"), "protobuf"), "RPCProtobufSerializer"
        )
