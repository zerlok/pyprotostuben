import ast
import inspect
import itertools
import typing as t
from dataclasses import dataclass

from pyprotostuben.codegen.servicify.abc import ServicifyCodeGenerator
from pyprotostuben.codegen.servicify.model import EntrypointInfo, GeneratedFile, GeneratorContext, GroupInfo, MethodInfo
from pyprotostuben.python.ast_builder import ASTBuilder, ModuleDependencyResolver
from pyprotostuben.python.info import ModuleInfo, PackageInfo, TypeInfo
from pyprotostuben.string_case import snake2camel


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


class BrokRPCServicifyCodeGenerator(ServicifyCodeGenerator):
    def generate(self, context: GeneratorContext) -> t.Sequence[GeneratedFile]:
        package = PackageInfo(None, context.package or "brokrpcx")
        model_module = ModuleInfo(package, "model")
        app_module = ModuleInfo(package, "app")

        specs = [
            RPCMethodSpec(
                package=package,
                entrypoint=entrypoint,
                group=group,
                method=method,
                request=self.__build_method_type_info(model_module, entrypoint, group, method, "Request"),
                response=self.__build_method_type_info(model_module, entrypoint, group, method, "Response"),
            )
            for entrypoint, group, method in context.iter_methods()
        ]

        return [
            self.__gen_package(context, package),
            # self.__build_models(context, model_module, specs),
            self.__build_app(context, app_module, specs),
        ]

    def __build_models(
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
                            bases=[TypeInfo.from_str("pydantic:BaseModel")],
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
                            bases=[
                                builder.build_generic_ref(
                                    TypeInfo.from_str("pydantic:RootModel"),
                                    TypeInfo.from_type(spec.response_param.annotation),
                                ),
                            ],
                            body=[builder.build_pass_stmt()],
                        ),
                    )
                    for spec in specs
                )
            )
        )

        return self.__gen_module(context, info, body)

    def __build_app(
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
                            name="".join(
                                (
                                    snake2camel(spec.entrypoint.name.title()),
                                    snake2camel(spec.group.name.title()),
                                    "Entrypoint",
                                )
                            ),
                            body=[
                                builder.build_init_def(
                                    args=[
                                        builder.build_pos_arg(
                                            name="impl",
                                            annotation=spec.group.info,
                                        )
                                    ],
                                    body=[
                                        builder.build_attr_assign("self", "__impl", value=builder.build_name("impl")),
                                    ],
                                ),
                                builder.build_method_def(
                                    name="add_to_server",
                                    args=[
                                        builder.build_pos_arg(
                                            name="server",
                                            annotation=builder.build_ref(
                                                TypeInfo.from_str("brokrpc.rpc.server:Server")
                                            ),
                                        ),
                                    ],
                                    returns=builder.build_none_ref(),
                                    body=[builder.build_pass_stmt()],
                                ),
                            ],
                        ),
                        # builder.build_func_def(
                        #     name="_".join(camel2snake(part) for part in reversed(spec.parts)),
                        #     decorators=[
                        #         builder.build_call(
                        #             func=builder.build_name("app", "post"),
                        #             args=[builder.build_const("/" + "/".join(spec.parts))],
                        #         ),
                        #     ],
                        #     args=[
                        #         builder.build_pos_arg(
                        #             name="request",
                        #             annotation=TypeInfo.from_str("fastapi:Request"),
                        #         ),
                        #     ],
                        #     body=[
                        #         builder.build_attr_assign(
                        #             "request_payload",
                        #             value=builder.build_call(
                        #                 func=ast.Attribute(
                        #                     value=builder.build_ref(spec.request),
                        #                     attr="model_validate_json",
                        #                 ),
                        #                 args=[
                        #                     builder.build_call(func=builder.build_name("request", "read"), is_async=True)
                        #                 ],
                        #                 kwargs={"by_alias": builder.build_const(True)},
                        #             ),
                        #         ),
                        #         builder.build_attr_assign(
                        #             "response_payload",
                        #             value=builder.build_call(
                        #                 func=builder.build_name("request", "state", *spec.parts),
                        #                 kwargs={
                        #                     param.name: builder.build_name("request_payload", param.name)
                        #                     for param in spec.request_params
                        #                     if param.annotation is not inspect.Parameter.empty
                        #                 },
                        #             ),
                        #         ),
                        #         builder.build_return_stmt(
                        #             value=builder.build_call(
                        #                 func=ast.Attribute(
                        #                     value=builder.build_ref(spec.response),
                        #                     attr="model_dump",
                        #                 ),
                        #                 args=[builder.build_name("response_payload")],
                        #                 kwargs={"by_alias": builder.build_const(True)},
                        #             ),
                        #         ),
                        #     ],
                        #     returns=spec.response,
                        #     is_async=True,
                        # ),
                    )
                    for spec in specs
                )
            ),
        )

        return self.__gen_module(context, info, body)

    def __build_method_type_info(
        self,
        module: ModuleInfo,
        entrypoint: EntrypointInfo,
        group: GroupInfo,
        method: MethodInfo,
        name: str,
    ) -> TypeInfo:
        return TypeInfo(
            module=module,
            ns=[
                "".join(
                    snake2camel(part.title())
                    for part in (
                        entrypoint.name,
                        group.name,
                        method.name,
                        name,
                    )
                ),
            ],
        )

    def __gen_package(self, context: GeneratorContext, package: PackageInfo) -> GeneratedFile:
        return self.__gen_module(context, ModuleInfo(package, "__init__"), ast.Module(body=[], type_ignores=[]))

    def __gen_module(self, context: GeneratorContext, info: ModuleInfo, body: ast.Module) -> GeneratedFile:
        return GeneratedFile(path=context.output.joinpath(info.file), content=ast.unparse(body))

    def __get_builder(self, info: ModuleInfo) -> ASTBuilder:
        return ASTBuilder(ModuleDependencyResolver(info))
