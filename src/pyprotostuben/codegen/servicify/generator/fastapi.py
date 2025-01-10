import ast
import typing as t
from itertools import chain

from pyprotostuben.codegen.servicify.abc import ServicifyCodeGenerator
from pyprotostuben.codegen.servicify.generator.model import ModelASTBuilder, PydanticModelFactory
from pyprotostuben.codegen.servicify.model import EntrypointInfo, GeneratedFile, GeneratorContext, MethodInfo
from pyprotostuben.python.builder import PackageASTBuilder
from pyprotostuben.python.info import ModuleInfo, PackageInfo, TypeInfo
from pyprotostuben.string_case import camel2snake, snake2camel


# TODO: try to reuse this code in protobuf brokrpc generator. Use some kind of factory to inject custom module naming
#  (protobuf message types & serializer_module).
class FastAPIServicifyCodeGenerator(ServicifyCodeGenerator):
    def generate(self, context: GeneratorContext) -> t.Sequence[GeneratedFile]:
        builder = PackageASTBuilder(PackageInfo(None, context.package or "api"))

        builder.package(None).build()
        self.__build_abc_module(context, builder)
        self.__build_model_module(context, builder)
        self.__build_server_module(context, builder)
        self.__build_client_module(context, builder)

        return [
            GeneratedFile(
                path=context.output.joinpath(module.file),
                content=ast.unparse(body),
            )
            for module, body in builder.build()
        ]

    def __build_abc_module(
        self,
        context: GeneratorContext,
        pkg: PackageASTBuilder,
    ) -> None:
        mod = pkg.module(ModuleInfo(None, "abc"))

        mod.extend(
            mod.abstract_class_def(
                name=entrypoint.name,
                body=[
                    mod.abstract_method_def(
                        name=method.name,
                        args=[
                            mod.pos_arg(
                                name="request",
                                annotation=TypeInfo.build(
                                    ModuleInfo(pkg.info, "model"),
                                    self.__build_model_name(entrypoint, method, "Request"),
                                ),
                            )
                        ],
                        returns=TypeInfo.build(
                            ModuleInfo(pkg.info, "model"),
                            self.__build_model_name(entrypoint, method, "Response"),
                        )
                        if method.returns is not None
                        else mod.none_ref(),
                        is_async=True,
                    )
                    for method in entrypoint.methods
                ],
            )
            for entrypoint in context.entrypoints
        )
        mod.build()

    def __build_model_module(
        self,
        context: GeneratorContext,
        pkg: PackageASTBuilder,
    ) -> None:
        mod = pkg.module(ModuleInfo(None, "model"))

        models = ModelASTBuilder(PydanticModelFactory(mod))
        models.update(
            set(
                chain.from_iterable(
                    chain(
                        (param.annotation for param in method.params),
                        (method.returns,) if method.returns is not None else (),
                    )
                    for entrypoint in context.entrypoints
                    for method in entrypoint.methods
                )
            )
        )

        mod.extend(models.get_all_defs())
        mod.extend(
            (
                models.create(
                    name=self.__build_model_name(entrypoint, method, "Request"),
                    fields={param.name: models.resolve(param.annotation) for param in method.params},
                ),
                models.create(
                    name=self.__build_model_name(entrypoint, method, "Response"),
                    fields={"payload": models.resolve(method.returns)},
                )
                if method.returns is not None
                else None,
            )
            for entrypoint in context.entrypoints
            for method in entrypoint.methods
        )

        mod.build()

    def __build_server_module(self, context: GeneratorContext, pkg: PackageASTBuilder) -> None:
        mod = pkg.module(ModuleInfo(None, "server"))

        raw_request_ref = TypeInfo.build(ModuleInfo(PackageInfo(None, "starlette"), "requests"), "Request")
        model_ref = ModuleInfo(pkg.info, "model")

        mod.append(
            mod.func_def(
                name="create_app",
                args=[
                    mod.pos_arg(
                        name=camel2snake(entrypoint.name),
                        annotation=TypeInfo.build(ModuleInfo(pkg.info, "abc"), snake2camel(entrypoint.name)),
                    )
                    for entrypoint in context.entrypoints
                ],
                returns=TypeInfo.build(ModuleInfo(None, "fastapi"), "FastAPI"),
                body=[
                    mod.func_def(
                        name="init_lifespan",
                        args=[
                            mod.pos_arg(name="_", annotation=TypeInfo.build(ModuleInfo(None, "fastapi"), "FastAPI")),
                        ],
                        body=[
                            mod.yield_stmt(
                                mod.dict_expr(
                                    {
                                        mod.const(camel2snake(entrypoint.name)): mod.attr(camel2snake(entrypoint.name))
                                        for entrypoint in context.entrypoints
                                    }
                                )
                            )
                        ],
                        returns=mod.mapping_ref(mod.str_ref(), TypeInfo.from_type(object)),
                        is_async=True,
                        is_context_manager=True,
                    ),
                    mod.assign(
                        "app",
                        value=mod.call(
                            func=TypeInfo.build(ModuleInfo(None, "fastapi"), "FastAPI"),
                            kwargs={
                                "lifespan": mod.attr("init_lifespan"),
                            },
                        ),
                    ),
                    *(
                        mod.call_stmt(
                            func=mod.attr("app", "include_router"),
                            args=[mod.attr(f"{camel2snake(entrypoint.name)}_router")],
                        )
                        for entrypoint in context.entrypoints
                    ),
                    mod.return_stmt(mod.attr("app")),
                ],
            )
        )

        for entrypoint in context.entrypoints:
            dependency_name = f"get_{camel2snake(entrypoint.name)}_dependency"
            router_name = f"{camel2snake(entrypoint.name)}_router"
            entrypoint_abc_ref = TypeInfo.build(ModuleInfo(pkg.info, "abc"), snake2camel(entrypoint.name))

            mod.extend(
                mod.assign(
                    router_name,
                    value=mod.call(
                        func=TypeInfo.build(ModuleInfo(None, "fastapi"), "APIRouter"),
                        kwargs={
                            "prefix": mod.const(f"/{camel2snake(entrypoint.name)}"),
                        },
                    ),
                ),
            )

            mod.append(
                mod.func_def(
                    name=dependency_name,
                    args=[
                        mod.pos_arg(
                            name="raw_request",
                            annotation=mod.ref(raw_request_ref),
                        ),
                    ],
                    returns=entrypoint_abc_ref,
                    body=[mod.return_stmt(mod.attr("raw_request", "state", camel2snake(entrypoint.name)))],
                )
            )

            for method in entrypoint.methods:
                mod.append(
                    mod.func_def(
                        name=f"handle_{camel2snake(entrypoint.name)}_{method.name}",
                        decorators=[
                            mod.call(
                                func=mod.attr(router_name, "post"),
                                kwargs={
                                    "path": mod.const(f"/{method.name}"),
                                    "description": mod.const(method.doc) if method.doc is not None else mod.none_ref(),
                                },
                            )
                        ],
                        args=[
                            mod.pos_arg(
                                name="request",
                                annotation=TypeInfo.build(
                                    model_ref, self.__build_model_name(entrypoint, method, "Request")
                                ),
                            ),
                            mod.pos_arg(
                                name="entrypoint",
                                annotation=entrypoint_abc_ref,
                                default=mod.call(
                                    func=TypeInfo.build(ModuleInfo(None, "fastapi"), "Depends"),
                                    args=[mod.attr(dependency_name)],
                                ),
                            ),
                        ],
                        returns=TypeInfo.build(model_ref, self.__build_model_name(entrypoint, method, "Response"))
                        if method.returns is not None
                        else None,
                        body=[
                            mod.assign(
                                "response",
                                value=mod.call(
                                    func=mod.attr("entrypoint", method.name),
                                    args=[mod.attr("request")],
                                    is_async=True,
                                ),
                            ),
                            mod.return_stmt(mod.attr("response")),
                        ]
                        if method.returns is not None
                        else [
                            mod.call_stmt(
                                func=mod.attr("entrypoint", method.name),
                                args=[mod.attr("request")],
                                is_async=True,
                            )
                        ],
                        is_async=True,
                    )
                )

        mod.build()

    def __build_client_module(self, context: GeneratorContext, pkg: PackageASTBuilder) -> None:
        mod = pkg.module(ModuleInfo(None, "client"))

        abc_ref = ModuleInfo(pkg.info, "abc")
        model_ref = ModuleInfo(pkg.info, "model")
        client_impl_ref = TypeInfo.build(ModuleInfo(None, "httpx"), "AsyncClient")

        for entrypoint in context.entrypoints:
            client_name = f"{snake2camel(entrypoint.name)}AsyncClient"

            mod.append(
                mod.class_def(
                    name=client_name,
                    bases=[mod.ref(TypeInfo.build(abc_ref, snake2camel(entrypoint.name)))],
                    body=[
                        mod.init_attrs_def(
                            args=[
                                mod.pos_arg(
                                    name="impl",
                                    annotation=client_impl_ref,
                                ),
                            ],
                        ),
                        *(
                            mod.method_def(
                                name=method.name,
                                args=[
                                    mod.pos_arg(
                                        name="request",
                                        annotation=TypeInfo.build(
                                            model_ref, self.__build_model_name(entrypoint, method, "Request")
                                        ),
                                    )
                                ],
                                returns=TypeInfo.build(
                                    model_ref, self.__build_model_name(entrypoint, method, "Response")
                                )
                                if method.returns is not None
                                else mod.none_ref(),
                                body=[
                                    mod.assign(
                                        "raw_response",
                                        value=mod.call(
                                            func=mod.attr("self", "__impl", "post"),
                                            kwargs={
                                                "url": mod.const(f"/{camel2snake(entrypoint.name)}/{method.name}"),
                                                "json": mod.call(
                                                    func=mod.attr("request", "model_dump"),
                                                    kwargs={
                                                        "mode": mod.const("json"),
                                                        "by_alias": mod.const(True),
                                                        "exclude_none": mod.const(True),
                                                    },
                                                ),
                                            },
                                            is_async=True,
                                        ),
                                    ),
                                    mod.assign(
                                        "response",
                                        value=mod.method_call(
                                            obj=TypeInfo.build(
                                                model_ref, self.__build_model_name(entrypoint, method, "Response")
                                            ),
                                            name="model_validate_json",
                                            args=[
                                                mod.call(func=mod.attr("raw_response", "read")),
                                            ],
                                        ),
                                    ),
                                    mod.return_stmt(mod.attr("response")),
                                ]
                                if method.returns is not None
                                else [
                                    mod.call_stmt(
                                        func=mod.attr("self", "__impl", "post"),
                                        kwargs={
                                            "url": mod.const(f"/{camel2snake(entrypoint.name)}/{method.name}"),
                                            "json": mod.call(
                                                func=mod.attr("request", "model_dump"),
                                                kwargs={
                                                    "mode": mod.const("json"),
                                                    "by_alias": mod.const(True),
                                                    "exclude_none": mod.const(True),
                                                },
                                            ),
                                        },
                                        is_async=True,
                                    ),
                                ],
                                is_async=True,
                            )
                            for method in entrypoint.methods
                        ),
                    ],
                )
            )

        mod.build()

    def __build_model_name(
        self,
        entrypoint: EntrypointInfo,
        method: MethodInfo,
        suffix: str,
    ) -> str:
        return "".join(snake2camel(s) for s in (entrypoint.name, method.name, suffix))
