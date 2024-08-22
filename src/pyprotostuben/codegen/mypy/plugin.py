import typing as t
from contextlib import ExitStack

from google.protobuf.compiler.plugin_pb2 import CodeGeneratorRequest, CodeGeneratorResponse
from google.protobuf.descriptor_pb2 import GeneratedCodeInfo

from pyprotostuben.codegen.abc import ProtocPlugin, ProtoFileGenerator
from pyprotostuben.codegen.module_ast import ModuleASTBasedProtoFileGenerator
from pyprotostuben.codegen.mypy.generator import MypyStubASTGeneratorFactory
from pyprotostuben.logging import Logger, LoggerMixin
from pyprotostuben.pool.abc import Pool
from pyprotostuben.pool.process import MultiProcessPool, SingleProcessPool
from pyprotostuben.protobuf.context import CodeGeneratorContext, ContextBuilder


# TODO: support such options (disabled by default):
#  1. mutable message (allow field modifications after instantiation)
#  2. non strict (allow `None` value for non-optional fields)
class MypyStubProtocPlugin(ProtocPlugin, LoggerMixin):
    def run(self, request: CodeGeneratorRequest) -> CodeGeneratorResponse:
        log = self._log.bind_details(request_file_to_generate=request.file_to_generate)
        log.debug("request received")

        context = ContextBuilder.build(request)
        gen = ModuleASTBasedProtoFileGenerator(MypyStubASTGeneratorFactory(context))

        with ExitStack() as cm_stack:
            pool = (
                SingleProcessPool()
                if context.params.has_flag("no-parallel") or context.params.has_flag("debug")
                else cm_stack.enter_context(MultiProcessPool.setup())
            )

            resp = CodeGeneratorResponse(
                supported_features=CodeGeneratorResponse.Feature.FEATURE_PROTO3_OPTIONAL,
                file=self.__build_mypy_stubs(context, pool, gen, log),
            )

        log.info("request handled")

        return resp

    def __build_mypy_stubs(
        self,
        context: CodeGeneratorContext,
        pool: Pool,
        gen: ProtoFileGenerator,
        log: Logger,
    ) -> t.Iterable[CodeGeneratorResponse.File]:
        for results in pool.run(gen.run, context.files):
            for src, path, content in results:
                log.debug("module content ready", path=path)

                yield CodeGeneratorResponse.File(
                    name=str(path),
                    generated_code_info=GeneratedCodeInfo(
                        annotation=[GeneratedCodeInfo.Annotation(source_file=str(src.proto_path))],
                    ),
                    content=content,
                )
