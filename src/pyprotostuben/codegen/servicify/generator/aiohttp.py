import ast
import typing as t
from itertools import chain

from pyprotostuben.codegen.servicify.abc import ServicifyCodeGenerator
from pyprotostuben.codegen.servicify.generator.dataclasses import DataclassASTBuilder
from pyprotostuben.codegen.servicify.model import EntrypointInfo, GeneratedFile, GeneratorContext, MethodInfo
from pyprotostuben.python.builder import PackageASTBuilder
from pyprotostuben.python.info import ModuleInfo, PackageInfo, TypeInfo
from pyprotostuben.string_case import snake2camel


# TODO: try to reuse this code in protobuf brokrpc generator. Use some kind of factory to inject custom module naming
#  (protobuf message types & serializer_module).
class AiohttpServicifyCodeGenerator(ServicifyCodeGenerator):
    def generate(self, context: GeneratorContext) -> t.Sequence[GeneratedFile]:
        builder = PackageASTBuilder(PackageInfo(None, context.package or "api"))

        builder.package(None).build()
        self.__build_abc_module(context, builder)
        self.__build_model_module(context, builder)

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

        mod.build(
            body=[
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
            ],
        )

    def __build_model_module(
        self,
        context: GeneratorContext,
        pkg: PackageASTBuilder,
    ) -> None:
        mod = pkg.module(ModuleInfo(None, "model"))

        nested_types = DataclassASTBuilder(mod)
        nested_types.update(
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

        mod.build(
            body=list(
                chain(
                    nested_types.get_all_defs(),
                    chain.from_iterable(
                        (
                            mod.dataclass_def(
                                name=self.__build_model_name(entrypoint, method, "Request"),
                                fields={param.name: nested_types.resolve(param.annotation) for param in method.params},
                                frozen=True,
                                kw_only=True,
                            ),
                            mod.dataclass_def(
                                name=self.__build_model_name(entrypoint, method, "Response"),
                                fields={"payload": nested_types.resolve(method.returns)},
                                frozen=True,
                                kw_only=True,
                            )
                            if method.returns is not None
                            else None,
                        )
                        for entrypoint in context.entrypoints
                        for method in entrypoint.methods
                    ),
                ),
            ),
        )

    def __build_model_name(
        self,
        entrypoint: EntrypointInfo,
        method: MethodInfo,
        suffix: str,
    ) -> str:
        return "".join(snake2camel(s) for s in (entrypoint.name, method.name, suffix))
