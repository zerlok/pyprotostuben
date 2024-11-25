from contextlib import ExitStack
from functools import partial
from itertools import chain

from google.protobuf.compiler.plugin_pb2 import CodeGeneratorRequest, CodeGeneratorResponse

from pyprotostuben.codegen.abc import ProtocPlugin, ProtoFileGenerator
from pyprotostuben.codegen.module_ast import ModuleASTBasedProtoFileGenerator
from pyprotostuben.codegen.mypy.context import GRPCContext, MessageContext
from pyprotostuben.codegen.mypy.generator import MypyStubASTGenerator, MypyStubContext
from pyprotostuben.logging import LoggerMixin
from pyprotostuben.pool.abc import Pool
from pyprotostuben.pool.process import MultiProcessPool, SingleProcessPool
from pyprotostuben.protobuf.builder.grpc import GRPCASTBuilder
from pyprotostuben.protobuf.builder.message import MessageASTBuilder
from pyprotostuben.protobuf.context import CodeGeneratorContext, ContextBuilder
from pyprotostuben.protobuf.file import ProtoFile
from pyprotostuben.protobuf.parser import CodeGeneratorParameters
from pyprotostuben.python.ast_builder import ASTBuilder, ModuleDependencyResolver
from pyprotostuben.python.info import ModuleInfo
from pyprotostuben.stack import MutableStack


class MypyStubProtocPlugin(ProtocPlugin, LoggerMixin):
    def run(self, request: CodeGeneratorRequest) -> CodeGeneratorResponse:
        log = self._log.bind_details(request_file_to_generate=request.file_to_generate)
        log.debug("request received")

        with ExitStack() as cm_stack:
            context = ContextBuilder().build(request)
            gen = self.__create_generator(context)
            pool = self.__create_pool(context.params, cm_stack)

            resp = CodeGeneratorResponse(
                supported_features=CodeGeneratorResponse.Feature.FEATURE_PROTO3_OPTIONAL,
                file=chain.from_iterable(pool.run(gen.run, context.files)),
            )

        log.info("request handled")

        return resp

    def __create_generator(self, context: CodeGeneratorContext) -> ProtoFileGenerator:
        return ModuleASTBasedProtoFileGenerator(
            context_factory=partial(_MultiProcessFuncs.create_visitor_context, context.params),
            visitor=MypyStubASTGenerator(context.registry),
        )

    def __create_pool(self, params: CodeGeneratorParameters, cm_stack: ExitStack) -> Pool:
        return (
            SingleProcessPool()
            if params.has_flag("no-parallel") or params.has_flag("debug")
            else cm_stack.enter_context(MultiProcessPool.setup())
        )


class _MultiProcessFuncs:
    """
    A set of picklable functions that can be passed to `MultiProcessPool`.

    For more info: https://docs.python.org/3/library/multiprocessing.html#programming-guidelines
    """

    @staticmethod
    def create_visitor_context(params: CodeGeneratorParameters, file: ProtoFile) -> MypyStubContext:
        message_module = file.pb2_module
        grpc_module = ModuleInfo(file.pb2_package, f"{file.name}_pb2_grpc")

        return MypyStubContext(
            file=file,
            modules={},
            descriptors=MutableStack(
                [
                    MessageContext(
                        file=file,
                        module=message_module,
                        builder=MessageASTBuilder(
                            inner=ASTBuilder(ModuleDependencyResolver(message_module)),
                            mutable=params.has_flag("message-mutable"),
                            all_init_args_optional=params.has_flag("message-all-init-args-optional"),
                        ),
                    ),
                ],
            ),
            grpcs=MutableStack(
                [
                    GRPCContext(
                        file=file,
                        module=grpc_module,
                        builder=GRPCASTBuilder(
                            inner=ASTBuilder(ModuleDependencyResolver(grpc_module)),
                            is_sync=params.has_flag("grpc-sync"),
                            skip_servicer=params.has_flag("grpc-skip-servicer"),
                            skip_stub=params.has_flag("grpc-skip-stub"),
                        ),
                    )
                ],
            ),
        )
