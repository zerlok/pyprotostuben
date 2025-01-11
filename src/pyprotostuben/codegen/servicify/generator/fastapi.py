import ast
import typing as t
from itertools import chain

from pyprotostuben.codegen.model import ModelDefBuilder, PydanticModelFactory
from pyprotostuben.codegen.servicify.abc import ServicifyCodeGenerator
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
        model_builder = self.__build_model_module(context, builder)
        self.__build_server_module(context, builder, model_builder)
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
                        doc=method.doc,
                        is_async=True,
                    )
                    for method in entrypoint.methods
                ],
                doc=entrypoint.doc,
            )
            for entrypoint in context.entrypoints
        )
        mod.build()

    def __build_model_module(
        self,
        context: GeneratorContext,
        pkg: PackageASTBuilder,
    ) -> ModelDefBuilder:
        mod = pkg.module(ModuleInfo(None, "model"))

        models = ModelDefBuilder(PydanticModelFactory(mod))
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
                    doc=f"Request model for `{entrypoint.name}.{method.name}` entrypoint method",
                ),
                models.create(
                    name=self.__build_model_name(entrypoint, method, "Response"),
                    fields={"payload": models.resolve(method.returns)},
                    doc=f"Response model for `{entrypoint.name}.{method.name}` entrypoint method",
                )
                if method.returns is not None
                else None,
            )
            for entrypoint in context.entrypoints
            for method in entrypoint.methods
        )

        mod.build()

        return models

    def __build_server_module(self, context: GeneratorContext, pkg: PackageASTBuilder, models: ModelDefBuilder) -> None:
        mod = pkg.module(ModuleInfo(None, "server"))

        abc_ref = ModuleInfo(pkg.info, "abc")
        model_ref = ModuleInfo(pkg.info, "model")

        for entrypoint in context.entrypoints:
            handler_name = f"{snake2camel(entrypoint.name)}Handler"

            mod.append(
                mod.func_def(
                    name=f"create_{camel2snake(entrypoint.name)}_router",
                    args=[
                        mod.pos_arg(
                            name="entrypoint",
                            annotation=TypeInfo.build(ModuleInfo(pkg.info, "abc"), snake2camel(entrypoint.name)),
                        ),
                    ],
                    returns=TypeInfo.build(ModuleInfo(None, "fastapi"), "APIRouter"),
                    body=[
                        mod.assign(
                            "router",
                            value=mod.call(
                                func=TypeInfo.build(ModuleInfo(None, "fastapi"), "APIRouter"),
                                kwargs={
                                    "prefix": mod.const(f"/{camel2snake(entrypoint.name)}"),
                                    "tags": mod.const([entrypoint.name]),
                                },
                            ),
                        ),
                        *(
                            mod.call_stmt(
                                func=mod.call(
                                    func=mod.attr("router", "post"),
                                    kwargs={
                                        "path": mod.const(f"/{method.name}"),
                                        "description": mod.const(method.doc)
                                        if method.doc is not None
                                        else mod.none_ref(),
                                    },
                                ),
                                args=[mod.attr("entrypoint", method.name)],
                            )
                            for method in entrypoint.methods
                        ),
                        mod.return_stmt(mod.attr("router")),
                    ],
                )
            )

            mod.append(
                mod.class_def(
                    name=handler_name,
                    bases=[mod.ref(TypeInfo.build(abc_ref, snake2camel(entrypoint.name)))],
                    body=[
                        mod.init_attrs_def(
                            args=[
                                mod.pos_arg(
                                    name="impl",
                                    annotation=entrypoint.type_,
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
                                    *(
                                        mod.assign(
                                            f"input_{param.name}",
                                            value=models.assign_expr(
                                                source=mod.attr("request", param.name),
                                                type_=param.annotation,
                                                mode="original",
                                                builder=mod,
                                            ),
                                        )
                                        for param in method.params
                                    ),
                                    mod.assign(
                                        "output",
                                        value=mod.call(
                                            func=mod.attr("self", "__impl", method.name),
                                            kwargs={
                                                param.name: mod.attr(f"input_{param.name}") for param in method.params
                                            },
                                        ),
                                    ),
                                    *(
                                        (
                                            mod.assign(
                                                "response",
                                                value=mod.call(
                                                    func=TypeInfo.build(
                                                        model_ref,
                                                        self.__build_model_name(entrypoint, method, "Response"),
                                                    ),
                                                    kwargs={
                                                        "payload": models.assign_expr(
                                                            source=mod.attr("output"),
                                                            type_=method.returns,
                                                            mode="model",
                                                            builder=mod,
                                                        ),
                                                    },
                                                ),
                                            ),
                                            mod.return_stmt(mod.attr("response")),
                                        )
                                        if method.returns is not None
                                        else ()
                                    ),
                                ],
                                is_async=True,
                                is_override=True,
                            )
                            for method in entrypoint.methods
                        ),
                    ],
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
                                                        "by_alias": mod.const(value=True),
                                                        "exclude_none": mod.const(value=True),
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
                                                    "by_alias": mod.const(value=True),
                                                    "exclude_none": mod.const(value=True),
                                                },
                                            ),
                                        },
                                        is_async=True,
                                    ),
                                ],
                                is_async=True,
                                is_override=True,
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
