import ast
import enum
import inspect
import itertools
import typing as t
from collections import defaultdict
from dataclasses import dataclass

from pyprotostuben.codegen.servicify.abc import ServicifyCodeGenerator
from pyprotostuben.codegen.servicify.model import EntrypointInfo, GeneratedFile, GeneratorContext, GroupInfo, MethodInfo
from pyprotostuben.python.ast_builder import ASTBuilder, ModuleDependencyResolver
from pyprotostuben.python.info import ModuleInfo, PackageInfo, TypeInfo
from pyprotostuben.string_case import camel2snake, snake2camel


class RPCMethodKind(enum.Enum):
    SUBSCRIBER = enum.auto()
    UNARY_UNARY = enum.auto()
    STREAM_UNARY = enum.auto()
    UNARY_STREAM = enum.auto()
    STREAM_STREAM = enum.auto()


@dataclass(frozen=True, kw_only=True)
class RPCMethodSpec:
    package: PackageInfo
    entrypoint: EntrypointInfo
    group: GroupInfo
    method: MethodInfo
    request: TypeInfo
    response: TypeInfo

    @property
    def parts(self) -> t.Sequence[str]:
        return self.entrypoint.name, self.group.name, self.method.name

    @property
    def kind(self) -> RPCMethodKind:
        # TODO: support all kinds
        if self.method.signature.return_annotation is None:
            return RPCMethodKind.SUBSCRIBER

        else:
            return RPCMethodKind.UNARY_UNARY

    @property
    def request_name(self) -> str:
        return self.request.ns[0]

    @property
    def request_params(self) -> t.Sequence[inspect.Parameter]:
        return list(self.method.signature.parameters.values())

    @property
    def response_name(self) -> str:
        return self.response.ns[0]

    @property
    def response_param(self) -> inspect.Parameter:
        return inspect.Parameter(
            name=self.response_name,
            kind=inspect.Parameter.POSITIONAL_ONLY,
            annotation=self.method.signature.return_annotation,
        )


def group_by_entrypoint_groups(
    specs: t.Sequence[RPCMethodSpec],
) -> t.Mapping[tuple[EntrypointInfo, GroupInfo], t.Sequence[RPCMethodSpec]]:
    result: dict[tuple[EntrypointInfo, GroupInfo], t.List[RPCMethodSpec]] = defaultdict(list)

    for spec in specs:
        result[(spec.entrypoint, spec.group)].append(spec)

    return result


# TODO: try to reuse this code in protobuf brokrpc generator. Use some kind of factory to inject custom module naming
#  (protobuf message types & serializers).
class BrokRPCServicifyCodeGenerator(ServicifyCodeGenerator):
    def generate(self, context: GeneratorContext) -> t.Sequence[GeneratedFile]:
        package = PackageInfo(None, context.package or "brokrpcx")
        serializer_module = ModuleInfo(package, "serializer")
        server_module = ModuleInfo(package, "server")
        client_module = ModuleInfo(package, "client")

        specs = [
            RPCMethodSpec(
                package=package,
                entrypoint=entrypoint,
                group=group,
                method=method,
                request=TypeInfo(
                    module=serializer_module,
                    ns=(self.__build_method_type_name(entrypoint, group, method, "Request"),),
                ),
                response=TypeInfo(
                    module=serializer_module,
                    ns=(self.__build_method_type_name(entrypoint, group, method, "Response"),),
                ),
            )
            for entrypoint, group, method in context.iter_methods()
        ]

        # TODO: repeat domain project package structure
        return [
            self.__gen_package(context, package),
            self.__build_serializer_module(context, serializer_module, specs),
            self.__build_server_module(context, server_module, specs),
            self.__build_client_module(context, client_module, specs),
        ]

    def __build_serializer_module(
        self,
        context: GeneratorContext,
        info: ModuleInfo,
        specs: t.Sequence[RPCMethodSpec],
    ) -> GeneratedFile:
        builder = self.__get_builder(info)

        body = builder.build_module(
            body=list(
                itertools.chain.from_iterable(
                    (
                        builder.build_class_def(
                            name=spec.request_name,
                            bases=[TypeInfo.from_str("brokrpc.rpc.abc:RPCSerializer")],
                            body=[
                                builder.build_attr_stub(
                                    name=param.name,
                                    annotation=TypeInfo.from_type(param.annotation),
                                )
                                for param in spec.request_params
                                if param.annotation is not inspect.Parameter.empty
                            ],
                        ),
                        builder.build_class_def(
                            name=spec.response_name,
                            bases=[TypeInfo.from_str("brokrpc.rpc.abc:RPCSerializer")],
                            body=[builder.build_pass_stmt()],
                        ),
                    )
                    for spec in specs
                )
            )
        )

        return self.__gen_module(context, info, body)

    def __build_server_module(
        self,
        context: GeneratorContext,
        info: ModuleInfo,
        specs: t.Sequence[RPCMethodSpec],
    ) -> GeneratedFile:
        builder = self.__get_builder(info)

        body = builder.build_module(
            body=list(
                itertools.chain.from_iterable(
                    (
                        builder.build_func_def(
                            name=f"register_{camel2snake(entrypoint.name.title())}_{camel2snake(group.name.title())}",
                            args=[
                                builder.build_pos_arg(
                                    name="entrypoint",
                                    annotation=builder.build_ref(group.info),
                                ),
                                builder.build_pos_arg(
                                    name="server",
                                    annotation=builder.build_ref(TypeInfo.from_str("brokrpc.rpc.server:Server")),
                                ),
                            ],
                            returns=builder.build_none_ref(),
                            body=[self.__build_server_method_register_stmt(spec, builder) for spec in grouped_specs],
                        ),
                    )
                    for (entrypoint, group), grouped_specs in group_by_entrypoint_groups(specs).items()
                )
            ),
        )

        return self.__gen_module(context, info, body)

    def __build_client_module(
        self,
        context: GeneratorContext,
        info: ModuleInfo,
        specs: t.Sequence[RPCMethodSpec],
    ) -> GeneratedFile:
        builder = self.__get_builder(info)

        body = builder.build_module(
            body=[
                self.__build_client_class_def(entrypoint, group, grouped_specs, builder)
                for (entrypoint, group), grouped_specs in group_by_entrypoint_groups(specs).items()
            ],
        )

        return self.__gen_module(context, info, body)

    def __build_client_class_def(
        self,
        entrypoint: EntrypointInfo,
        group: GroupInfo,
        specs: t.Sequence[RPCMethodSpec],
        builder: ASTBuilder,
    ) -> ast.stmt:
        name = f"{snake2camel(entrypoint.name.title())}{snake2camel(group.name.title())}Client"

        return builder.build_class_def(
            name=name,
            body=[
                builder.build_class_method_def(
                    name="create",
                    args=[
                        builder.build_pos_arg(
                            name="client",
                            annotation=builder.build_ref(TypeInfo.from_str("brokrpc.rpc.client:Client")),
                        ),
                    ],
                    returns=builder.build_const(name),
                    is_async=True,
                    is_context_manager=True,
                    body=[
                        builder.build_with_stmt(
                            items=[
                                (
                                    self.__build_client_method_caller_name(spec),
                                    self.__build_client_method_caller(spec, builder),
                                )
                                for spec in specs
                            ],
                            body=[
                                builder.build_yield_stmt(
                                    value=builder.build_call(
                                        func=builder.build_attr("cls"),
                                        kwargs={
                                            self.__build_client_method_caller_name(spec): builder.build_attr(
                                                self.__build_client_method_caller_name(spec)
                                            )
                                            for spec in specs
                                        },
                                    )
                                ),
                            ],
                            is_async=True,
                        )
                    ],
                ),
                builder.build_init_attrs_def(
                    args=[
                        builder.build_pos_arg(
                            name=self.__build_client_method_caller_name(spec),
                            annotation=self.__build_client_method_caller_type(spec, builder),
                        )
                        for spec in specs
                    ],
                ),
                *(self.__build_client_method_caller_def(spec, builder) for spec in specs),
            ],
        )

    def __build_server_method_register_stmt(self, spec: RPCMethodSpec, builder: ASTBuilder) -> ast.stmt:
        registrator: str

        if spec.kind is RPCMethodKind.SUBSCRIBER:
            registrator = "register_consumer"

        elif spec.kind is RPCMethodKind.UNARY_UNARY:
            registrator = "register_unary_unary_handler"

        elif spec.kind is RPCMethodKind.STREAM_UNARY:
            registrator = "register_stream_unary_handler"

        elif spec.kind is RPCMethodKind.UNARY_STREAM:
            registrator = "register_unary_stream_handler"

        elif spec.kind is RPCMethodKind.STREAM_STREAM:
            registrator = "register_stream_stream_handler"

        else:
            t.assert_never(spec.kind)

        return builder.build_call_stmt(
            func=builder.build_attr("server", registrator),
            kwargs={
                "func": builder.build_attr("entrypoint", spec.method.name),
                "routing_key": builder.build_const("/".join(spec.parts)),
                "serializer": builder.build_call(
                    func=builder.build_ref(TypeInfo.from_str("brokrpc.serializer.json:JSONSerializer")),
                ),
            },
        )

    def __build_client_method_caller(self, spec: RPCMethodSpec, builder: ASTBuilder) -> ast.expr:
        registrator: str

        if spec.kind is RPCMethodKind.SUBSCRIBER:
            registrator = "publisher"

        elif spec.kind is RPCMethodKind.UNARY_UNARY:
            registrator = "unary_unary_caller"

        elif spec.kind is RPCMethodKind.STREAM_UNARY:
            registrator = "stream_unary_caller"

        elif spec.kind is RPCMethodKind.UNARY_STREAM:
            registrator = "unary_stream_caller"

        elif spec.kind is RPCMethodKind.STREAM_STREAM:
            registrator = "stream_stream_caller"

        else:
            t.assert_never(spec.kind)

        return builder.build_call(
            func=builder.build_attr(
                "client",
                registrator,
            ),
            kwargs={
                "routing_key": builder.build_const("/".join(spec.parts)),
                "serializer": builder.build_call(
                    func=builder.build_ref(TypeInfo.from_str("brokrpc.serializer.json:JSONSerializer")),
                ),
            },
        )

    def __build_client_method_caller_type(self, spec: RPCMethodSpec, builder: ASTBuilder) -> ast.expr:
        if spec.kind is RPCMethodKind.SUBSCRIBER:
            return builder.build_generic_ref(
                TypeInfo.from_str("brokrpc.abc:Publisher"), spec.request, builder.build_none_ref()
            )

        elif (
            spec.kind is RPCMethodKind.UNARY_UNARY
            or spec.kind is RPCMethodKind.STREAM_UNARY
            or spec.kind is RPCMethodKind.UNARY_STREAM
            or spec.kind is RPCMethodKind.STREAM_STREAM
        ):
            return builder.build_generic_ref(TypeInfo.from_str("brokrpc.rpc.abc:Caller"), spec.request, spec.response)

        else:
            t.assert_never(spec.kind)

    def __build_client_method_caller_def(self, spec: RPCMethodSpec, builder: ASTBuilder) -> ast.stmt:
        if spec.kind is RPCMethodKind.SUBSCRIBER:
            return builder.build_method_def(
                name=self.__build_client_method_caller_name(spec),
                args=[builder.build_pos_arg(name="event", annotation=spec.request)],
                body=[
                    builder.build_call_stmt(
                        func=builder.build_attr("self", f"__{self.__build_client_method_caller_name(spec)}", "publish"),
                        args=[builder.build_attr("event")],
                        is_async=True,
                    ),
                ],
                returns=builder.build_none_ref(),
                is_async=True,
            )

        elif (
            spec.kind is RPCMethodKind.UNARY_UNARY
            or spec.kind is RPCMethodKind.STREAM_UNARY
            or spec.kind is RPCMethodKind.UNARY_STREAM
            or spec.kind is RPCMethodKind.STREAM_STREAM
        ):
            return builder.build_method_def(
                name=self.__build_client_method_caller_name(spec),
                args=[builder.build_pos_arg(name="request", annotation=spec.request)],
                body=[
                    builder.build_return_stmt(
                        value=builder.build_call(
                            func=builder.build_attr(
                                "self", f"__{self.__build_client_method_caller_name(spec)}", "invoke"
                            ),
                            args=[builder.build_attr("request")],
                            is_async=True,
                        ),
                    )
                ],
                returns=spec.response,
                is_async=True,
            )

        else:
            t.assert_never(spec.kind)

    def __build_client_method_caller_name(self, spec: RPCMethodSpec) -> str:
        return "_".join(camel2snake(part) for part in reversed(spec.parts))

    def __build_method_type_name(
        self,
        entrypoint: EntrypointInfo,
        group: GroupInfo,
        method: MethodInfo,
        name: str,
    ) -> str:
        return "".join(snake2camel(part.title()) for part in (entrypoint.name, group.name, method.name, name))

    def __gen_package(self, context: GeneratorContext, package: PackageInfo) -> GeneratedFile:
        info = ModuleInfo(package, "__init__")
        return self.__gen_module(context, info, self.__get_builder(info).build_module())

    def __gen_module(self, context: GeneratorContext, info: ModuleInfo, body: ast.Module) -> GeneratedFile:
        return GeneratedFile(path=context.output.joinpath(info.file), content=ast.unparse(body))

    def __get_builder(self, info: ModuleInfo) -> ASTBuilder:
        return ASTBuilder(ModuleDependencyResolver(info))
