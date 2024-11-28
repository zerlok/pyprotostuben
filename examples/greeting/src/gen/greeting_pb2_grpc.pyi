import abc
import builtins
import gen.greeting_pb2
import grpc
import grpc.aio
import typing

class GreeterServicer(metaclass=abc.ABCMeta):
    """the greeter service"""

    @abc.abstractmethod
    async def Greet(self, request: gen.greeting_pb2.GreetRequest, context: grpc.aio.ServicerContext[gen.greeting_pb2.GreetRequest, gen.greeting_pb2.GreetResponse]) -> gen.greeting_pb2.GreetResponse:
        """the greet method"""
        ...

def add_GreeterServicer_to_server(servicer: GreeterServicer, server: grpc.aio.Server) -> None:...

class GreeterStub:
    """the greeter service"""

    def __init__(self, channel: grpc.aio.Channel) -> None:...

    def Greet(self, request: gen.greeting_pb2.GreetRequest, *, timeout: typing.Optional[builtins.float]=None, metadata: typing.Optional[grpc.aio.MetadataType]=None, credentials: typing.Optional[grpc.CallCredentials]=None, wait_for_ready: typing.Optional[builtins.bool]=None, compression: typing.Optional[grpc.Compression]=None) -> grpc.aio.UnaryUnaryCall[gen.greeting_pb2.GreetRequest, gen.greeting_pb2.GreetResponse]:
        """the greet method"""
        ...