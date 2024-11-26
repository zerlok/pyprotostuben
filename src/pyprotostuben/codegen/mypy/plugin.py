from contextlib import ExitStack
from itertools import chain

from google.protobuf.compiler.plugin_pb2 import CodeGeneratorRequest, CodeGeneratorResponse

from pyprotostuben.codegen.abc import ProtocPlugin, ProtoFileGenerator
from pyprotostuben.codegen.module_ast import ModuleAstProtoFileGenerator
from pyprotostuben.codegen.mypy.builder import Pb2AstBuilder, Pb2GrpcAstBuilder
from pyprotostuben.codegen.mypy.generator import MypyStubAstGenerator, MypyStubContext, MypyStubTrait
from pyprotostuben.logging import LoggerMixin
from pyprotostuben.pool.abc import Pool
from pyprotostuben.pool.process import MultiProcessPool, SingleProcessPool
from pyprotostuben.protobuf.context import ContextBuilder
from pyprotostuben.protobuf.file import ProtoFile
from pyprotostuben.protobuf.parser import CodeGeneratorParameters
from pyprotostuben.protobuf.registry import TypeRegistry
from pyprotostuben.python.ast_builder import ASTBuilder, ModuleDependencyResolver
from pyprotostuben.python.info import ModuleInfo


class MypyStubProtocPlugin(ProtocPlugin, LoggerMixin):
    def run(self, request: CodeGeneratorRequest) -> CodeGeneratorResponse:
        log = self._log.bind_details(request_file_to_generate=request.file_to_generate)
        log.debug("request received")

        with ExitStack() as cm_stack:
            context = ContextBuilder().build(request)
            factory = MypyStubFactory(context.params, context.registry)

            pool = factory.create_pool(cm_stack)
            gen = factory.create_generator()

            resp = CodeGeneratorResponse(
                supported_features=CodeGeneratorResponse.Feature.FEATURE_PROTO3_OPTIONAL,
                file=chain.from_iterable(pool.run(gen.run, context.files)),
            )

        log.info("request handled")

        return resp


class MypyStubFactory(MypyStubTrait):
    """
    A set of picklable functions that can be passed to `MultiProcessPool`.

    For more info: https://docs.python.org/3/library/multiprocessing.html#programming-guidelines
    """

    def __init__(
        self,
        params: CodeGeneratorParameters,
        registry: TypeRegistry,
    ) -> None:
        self.__params = params
        self.__registry = registry

    def create_generator(self) -> ProtoFileGenerator:
        return ModuleAstProtoFileGenerator(
            context_factory=self.create_visitor_context,
            visitor=MypyStubAstGenerator(self.__registry, self),
        )

    def create_pool(self, cm_stack: ExitStack) -> Pool:
        return (
            SingleProcessPool()
            if self.__params.has_flag("no-parallel") or self.__params.has_flag("debug")
            else cm_stack.enter_context(MultiProcessPool.setup())
        )

    def create_pb2_module(self, file: ProtoFile) -> ModuleInfo:
        return file.pb2_module

    def create_pb2_builder(self, module: ModuleInfo) -> Pb2AstBuilder:
        return Pb2AstBuilder(
            inner=ASTBuilder(ModuleDependencyResolver(module)),
            mutable=self.__params.has_flag("message-mutable"),
            all_init_args_optional=self.__params.has_flag("message-all-init-args-optional"),
            include_descriptors=self.__params.has_flag("include-descriptors"),
        )

    def create_pb2_grpc_module(self, file: ProtoFile) -> ModuleInfo:
        return ModuleInfo(file.pb2_package, f"{file.name}_pb2_grpc")

    def create_pb2_grpc_builder(self, module: ModuleInfo) -> Pb2GrpcAstBuilder:
        return Pb2GrpcAstBuilder(
            inner=ASTBuilder(ModuleDependencyResolver(module)),
            is_sync=self.__params.has_flag("grpc-sync"),
            skip_servicer=self.__params.has_flag("grpc-skip-servicer"),
            skip_stub=self.__params.has_flag("grpc-skip-stub"),
        )

    # NOTE: this method must be picklable, thus it is public
    def create_visitor_context(self, _: ProtoFile) -> MypyStubContext:
        return MypyStubContext()
