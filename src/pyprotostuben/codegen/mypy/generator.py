import typing as t
from contextlib import ExitStack

from google.protobuf.compiler.plugin_pb2 import CodeGeneratorRequest, CodeGeneratorResponse
from google.protobuf.descriptor_pb2 import GeneratedCodeInfo

from pyprotostuben.codegen.abc import CodeGenerator
from pyprotostuben.codegen.mypy.strategy.abc import Strategy
from pyprotostuben.codegen.mypy.strategy.module_ast import ModuleASTGeneratorStrategy
from pyprotostuben.logging import LoggerMixin, Logger
from pyprotostuben.pool.abc import Pool
from pyprotostuben.pool.process import SingleProcessPool, MultiProcessPool
from pyprotostuben.protobuf.context import ContextBuilder, CodeGeneratorContext
from pyprotostuben.protobuf.parser import ParameterParser


# TODO: support such options (disabled by default):
#  1. mutable message (allow field modifications after instantiation)
#  2. non strict (allow `None` value for non-optional fields)
class MypyStubCodeGenerator(CodeGenerator, LoggerMixin):
    def run(self, request: CodeGeneratorRequest) -> CodeGeneratorResponse:
        log = self._log.bind_details(request_file_to_generate=request.file_to_generate)
        log.debug("request received")

        context = ContextBuilder.build(request)

        with ExitStack() as cm_stack:
            params = ParameterParser().parse(request.parameter)
            pool = (
                SingleProcessPool()
                if params.has_flag("no-parallel") or params.has_flag("debug")
                else cm_stack.enter_context(MultiProcessPool.setup())
            )
            strategy = ModuleASTGeneratorStrategy(context.type_registry)

            resp = CodeGeneratorResponse(
                supported_features=CodeGeneratorResponse.Feature.FEATURE_PROTO3_OPTIONAL,
                file=self.__build_mypy_stubs(context, pool, strategy, log),
            )

        log.info("request handled")

        return resp

    def __build_mypy_stubs(
        self,
        context: CodeGeneratorContext,
        pool: Pool,
        strategy: Strategy,
        log: Logger,
    ) -> t.Iterable[CodeGeneratorResponse.File]:
        for results in pool.run(strategy.run, context.files):
            for src, path, content in results:
                log.debug("module content ready", path=path)

                yield CodeGeneratorResponse.File(
                    name=str(path),
                    generated_code_info=GeneratedCodeInfo(
                        annotation=[GeneratedCodeInfo.Annotation(source_file=str(src.proto_path))],
                    ),
                    content=content,
                )
