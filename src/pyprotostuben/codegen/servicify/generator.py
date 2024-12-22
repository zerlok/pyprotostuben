import ast
import enum
import itertools
import typing as t
from dataclasses import dataclass

from pyprotostuben.codegen.servicify.abc import ServicifyCodeGenerator
from pyprotostuben.codegen.servicify.model import EntrypointInfo, GeneratedFile, GeneratorContext, MethodInfo
from pyprotostuben.python.ast_builder import ASTBuilder, PackageBuilder
from pyprotostuben.python.info import ModuleInfo, PackageInfo, TypeInfo
from pyprotostuben.string_case import camel2snake, snake2camel


class EntrypointTrait:
    def __init__(self, context: GeneratorContext, entrypoint: EntrypointInfo) -> None:
        self.__context = context
        self.__entrypoint = entrypoint

    def get_root_pkg(self) -> PackageInfo:
        return PackageInfo.build(self.__context.package or "api")

    def get_abc_mod(self) -> ModuleInfo:
        return ModuleInfo(self.get_root_pkg(), "abc")

    def get_interface_type(self) -> TypeInfo:
        return TypeInfo.build(self.get_abc_mod(), snake2camel(self.__entrypoint.name.title()))

    def get_type(self, package: str, module: str, name: str) -> TypeInfo:
        return TypeInfo.build(
            ModuleInfo(PackageInfo.build(*self.get_root_pkg().parts, package, self.__entrypoint.name), module),
            name,
        )

    # def get_server_model_type(self, method: MethodInfo, suffix: str) -> TypeInfo:
    #     return self._get_type_info("server", "model", f"{method.name}{suffix}")
    #
    # def get_server_serializer_type(self, method: MethodInfo, suffix: str) -> TypeInfo:
    #     return self._get_type_info("server", "serializer", f"{method.name}{suffix}")
    #
    # def get_server_impl_type(self) -> TypeInfo:
    #     return self._get_type_info("server", "entrypoint", f"{self.__entrypoint.name}Impl")
    #
    # def get_client_model_type(self, method: MethodInfo, suffix: str) -> TypeInfo:
    #     return self._get_type_info("client", "model", f"{method.name}{suffix}")
    #
    # def get_client_serializer_type(self, method: MethodInfo, suffix: str) -> TypeInfo:
    #     return self._get_type_info("client", "serializer", f"{method.name}{suffix}")
    #
    # def get_client_impl_type(self) -> TypeInfo:
    #     return self._get_type_info("client", "entrypoint", f"{self.__entrypoint.name}Impl")


@dataclass(frozen=True, kw_only=True)
class _BaseBrokRPCMethodSpec:
    entrypoint: EntrypointInfo
    method: MethodInfo
    trait: EntrypointTrait

    @property
    def parts(self) -> t.Sequence[str]:
        return *self.entrypoint.type_.module.parts, *self.entrypoint.type_.ns, self.method.name


@dataclass(frozen=True, kw_only=True)
class BrokRPCConsumerMethodSpec(_BaseBrokRPCMethodSpec):
    pass


@dataclass(frozen=True, kw_only=True)
class BrokRPCRequestResponseMethodSpec(_BaseBrokRPCMethodSpec):
    class Kind(enum.Enum):
        UNARY_UNARY = enum.auto()
        STREAM_UNARY = enum.auto()
        UNARY_STREAM = enum.auto()
        STREAM_STREAM = enum.auto()

    kind: Kind


BrokRPCMethodSpec = t.Union[BrokRPCConsumerMethodSpec, BrokRPCRequestResponseMethodSpec]


@dataclass(frozen=True, kw_only=True)
class BrokRPCEntrypointSpec:
    entrypoint: EntrypointInfo
    methods: t.Sequence[BrokRPCMethodSpec]


# TODO: try to reuse this code in protobuf brokrpc generator. Use some kind of factory to inject custom module naming
#  (protobuf message types & serializer_module).
class BrokRPCServicifyCodeGenerator(ServicifyCodeGenerator):
    def generate(self, context: GeneratorContext) -> t.Sequence[GeneratedFile]:
        builder = PackageBuilder(context.package or "api")
        specs: t.Sequence[BrokRPCEntrypointSpec] = list(self.__build_entrypoint_specs(context))

        print(specs)

        # TODO: repeat domain project root_pkg structure
        return [
            # *(
            #     self.__gen_package(context, pkg)
            #     for pkg in (
            #         # mod_manager.get_root_pkg(),
            #         # mod_manager.get_server_pkg(),
            #         # mod_manager.get_client_pkg(),
            #     )
            # ),
            # *self.__build_serializer_modules(context, specs),
            self.__build_abc_module(context, specs),
            # *self.__build_server_modules(context, specs),
            # *self.__build_client_modules(context, specs),
        ]

    def __build_entrypoint_specs(self, context: GeneratorContext) -> t.Iterable[BrokRPCEntrypointSpec]:
        for entrypoint in context.entrypoints:
            if not entrypoint.methods:
                continue

            yield BrokRPCEntrypointSpec(
                entrypoint=entrypoint,
                methods=tuple(self.__build_method_spec(context, entrypoint, method) for method in entrypoint.methods),
            )

    def __build_method_spec(
        self,
        context: GeneratorContext,
        entrypoint: EntrypointInfo,
        method: MethodInfo,
    ) -> BrokRPCMethodSpec:
        trait = EntrypointTrait(context, entrypoint)

        if method.returns is None:
            return BrokRPCConsumerMethodSpec(
                entrypoint=entrypoint,
                method=method,
                trait=trait,
            )

        else:
            return BrokRPCRequestResponseMethodSpec(
                entrypoint=entrypoint,
                method=method,
                # TODO: support all kinds
                kind=BrokRPCRequestResponseMethodSpec.Kind.UNARY_UNARY,
                trait=trait,
            )

    def __build_abc_module(
        self,
        context: GeneratorContext,
        specs: t.Sequence[BrokRPCEntrypointSpec],
    ) -> GeneratedFile:
        builder = self.__get_builder(info)

        body = builder.build_module(
            body=[
                builder.build_abstract_class_def(
                    name=spec.name,
                    body=[
                        builder.build_abstract_method_def(
                            name=method.name,
                            args=[
                                builder.build_pos_arg(
                                    name="input_",
                                    annotation=builder.build_int_ref(),
                                )
                            ],
                            returns=builder.build_none_ref(),
                            is_async=True,
                        )
                        for group, methods in spec.groups.items()
                        for method in methods
                    ],
                )
                for spec in specs
            ],
        )

        return self.__gen_module(context, info, body)

    # TODO: separate server & client serializer_module
    def __build_serializer_module(
        self,
        context: GeneratorContext,
        info: ModuleInfo,
        specs: t.Sequence[BrokRPCMethodSpec],
    ) -> GeneratedFile:
        builder = self.__get_builder(info)

        body = builder.build_module(
            body=list(itertools.chain.from_iterable(self.__build_method_serializers(spec, builder) for spec in specs))
        )

        return self.__gen_module(context, info, body)

    def __build_server_module(
        self,
        context: GeneratorContext,
        info: ModuleInfo,
        specs: t.Sequence[BrokRPCEntrypointSpec],
    ) -> GeneratedFile:
        builder = self.__get_builder(info)

        body = builder.build_module(
            body=list(
                itertools.chain.from_iterable(
                    (
                        builder.build_func_def(
                            name=f"register_{camel2snake(spec.name.title())}",
                            args=[
                                builder.build_pos_arg(
                                    name="entrypoint",
                                    annotation=builder.build_attr(spec.name),
                                ),
                                builder.build_pos_arg(
                                    name="server",
                                    annotation=builder.build_ref(TypeInfo.from_str("brokrpc.rpc.server:Server")),
                                ),
                            ],
                            returns=builder.build_none_ref(),
                            body=[
                                self.__build_server_method_register_stmt(method, builder)
                                for group, methods in spec.groups.items()
                                for method in methods
                            ],
                        ),
                    )
                    for spec in specs
                )
            ),
        )

        return self.__gen_module(context, info, body)

    def __build_client_module(
        self,
        context: GeneratorContext,
        info: ModuleInfo,
        specs: t.Sequence[BrokRPCEntrypointSpec],
    ) -> GeneratedFile:
        builder = self.__get_builder(info)

        body = builder.build_module(
            body=[self.__build_client_class(spec, builder) for spec in specs],
        )

        return self.__gen_module(context, info, body)

    def __build_method_serializers(self, spec: BrokRPCMethodSpec, builder: ASTBuilder) -> t.Iterable[ast.stmt]:
        return (
            builder.build_class_def(
                name=spec.request_name,
                bases=[TypeInfo.from_str("brokrpc.rpc.abc:RPCSerializer")],
                body=[
                    builder.build_attr_stub(
                        name=param.name,
                        annotation=TypeInfo.from_type(param.annotation),
                    )
                    for param in spec.request_params
                ],
            ),
            builder.build_class_def(
                name=spec.response_name,
                bases=[TypeInfo.from_str("brokrpc.rpc.abc:RPCSerializer")],
                body=[builder.build_pass_stmt()],
            ),
        )

    def __build_server_method_register_stmt(self, spec: BrokRPCMethodSpec, builder: ASTBuilder) -> ast.stmt:
        registrator: str

        if isinstance(spec, BrokRPCConsumerMethodSpec):
            registrator = "register_consumer"

        elif isinstance(spec, BrokRPCRequestResponseMethodSpec):
            if spec.kind is BrokRPCRequestResponseMethodSpec.Kind.UNARY_UNARY:
                registrator = "register_unary_unary_handler"

            elif spec.kind is BrokRPCRequestResponseMethodSpec.Kind.STREAM_UNARY:
                registrator = "register_stream_unary_handler"

            elif spec.kind is BrokRPCRequestResponseMethodSpec.Kind.UNARY_STREAM:
                registrator = "register_unary_stream_handler"

            elif spec.kind is BrokRPCRequestResponseMethodSpec.Kind.STREAM_STREAM:
                registrator = "register_stream_stream_handler"

            else:
                t.assert_never(spec.kind)

        else:
            t.assert_never(spec.kind)

        return builder.build_call_stmt(
            func=builder.build_attr("server", registrator),
            kwargs={
                "func": builder.build_attr("entrypoint", spec.method.name),
                "routing_key": builder.build_const("/".join(spec.parts)),
                "serializer": builder.build_ref(spec.server_serializer),
            },
        )

    def __build_client_class(self, spec: BrokRPCEntrypointSpec, builder: ASTBuilder) -> ast.stmt:
        name = f"{snake2camel(spec.name.title())}Client"

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
                                    spec.name,
                                    self.__build_client_method_caller_register_stmt(method, builder),
                                )
                                for group, methods in spec.groups.items()
                                for method in methods
                            ],
                            body=[
                                builder.build_yield_stmt(
                                    value=builder.build_call(
                                        func=builder.build_attr("cls"),
                                        kwargs={
                                            method.name: builder.build_attr(method.name)
                                            for group, methods in spec.groups.items()
                                            for method in methods
                                        },
                                    )
                                ),
                            ],
                            is_async=True,
                        ),
                    ],
                ),
                builder.build_init_attrs_def(
                    args=[
                        builder.build_pos_arg(
                            name=spec.name,
                            annotation=self.__build_client_method_caller_type(method, builder),
                        )
                        for group, methods in spec.groups.items()
                        for method in methods
                    ],
                ),
                *(
                    self.__build_client_method_caller_def(method, builder)
                    for group, methods in spec.groups.items()
                    for method in methods
                ),
            ],
        )

    def __build_client_method_caller_register_stmt(self, spec: BrokRPCMethodSpec, builder: ASTBuilder) -> ast.expr:
        registrator: str

        if isinstance(spec, BrokRPCConsumerMethodSpec):
            registrator = "publisher"

        elif isinstance(spec, BrokRPCRequestResponseMethodSpec):
            if spec.kind is BrokRPCRequestResponseMethodSpec.Kind.UNARY_UNARY:
                registrator = "unary_unary_caller"

            elif spec.kind is BrokRPCRequestResponseMethodSpec.Kind.STREAM_UNARY:
                registrator = "stream_unary_caller"

            elif spec.kind is BrokRPCRequestResponseMethodSpec.Kind.UNARY_STREAM:
                registrator = "unary_stream_caller"

            elif spec.kind is BrokRPCRequestResponseMethodSpec.Kind.STREAM_STREAM:
                registrator = "stream_stream_caller"

            else:
                t.assert_never(spec.kind)

        else:
            t.assert_never(spec.kind)

        return builder.build_call(
            func=builder.build_attr("client", registrator),
            kwargs={
                "routing_key": builder.build_const("/".join(spec.parts)),
                "serializer": builder.build_ref(spec.client_serializer),
            },
        )

    def __build_client_method_caller_type(self, spec: BrokRPCMethodSpec, builder: ASTBuilder) -> ast.expr:
        if isinstance(spec, BrokRPCConsumerMethodSpec):
            return builder.build_generic_ref(
                TypeInfo.from_str("brokrpc.abc:Publisher"), builder.build_attr(spec.name), builder.build_none_ref()
            )

        elif isinstance(spec, BrokRPCRequestResponseMethodSpec):
            return builder.build_generic_ref(
                TypeInfo.from_str("brokrpc.rpc.abc:Caller"),
                builder.build_attr(spec.request_name),
                builder.build_attr(spec.response_name),
            )

        else:
            t.assert_never(spec.kind)

    def __build_client_method_caller_def(self, spec: BrokRPCMethodSpec, builder: ASTBuilder) -> ast.stmt:
        if isinstance(spec, BrokRPCConsumerMethodSpec):
            return builder.build_method_def(
                name=spec.name,
                args=[builder.build_pos_arg(name="event", annotation=spec.input_info)],
                body=[
                    builder.build_call_stmt(
                        func=builder.build_attr("self", f"__{spec.name}", "publish"),
                        args=[builder.build_attr("event")],
                        is_async=True,
                    ),
                ],
                returns=builder.build_none_ref(),
                is_async=True,
            )

        elif isinstance(spec, BrokRPCRequestResponseMethodSpec):
            return builder.build_method_def(
                name=spec.name,
                args=[builder.build_pos_arg(name="request", annotation=spec.request_info)],
                body=[
                    builder.build_return_stmt(
                        value=builder.build_call(
                            func=builder.build_attr("self", f"__{spec.name}", "invoke"),
                            args=[builder.build_attr("request")],
                            is_async=True,
                        ),
                    )
                ],
                returns=spec.response_info,
                is_async=True,
            )

        else:
            t.assert_never(spec.kind)

    def __gen_module(self, context: GeneratorContext, info: ModuleInfo, body: ast.Module) -> GeneratedFile:
        return GeneratedFile(path=context.output.joinpath(info.file), content=ast.unparse(body))
