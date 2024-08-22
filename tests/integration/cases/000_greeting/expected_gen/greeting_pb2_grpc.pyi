import abc
import builtins
import greeting_pb2
import grpc
import grpc.aio
import typing

class GreeterServicer(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    async def Greet(self, request: greeting_pb2.GreetRequest, context: grpc.aio.ServicerContext[greeting_pb2.GreetRequest, greeting_pb2.GreetResponse]) -> greeting_pb2.GreetResponse:...

def add_GreeterServicer_to_server(servicer: GreeterServicer, server: grpc.aio.Server) -> None:...

class GreeterStub:

    def __init__(self, channel: grpc.aio.Channel) -> None:...

    async def Greet(self, request: greeting_pb2.GreetRequest, *, timeout: typing.Optional[builtins.float]=None, metadata: typing.Optional[grpc.aio.MetadataType]=None, credentials: typing.Optional[grpc.CallCredentials]=None, wait_for_ready: typing.Optional[builtins.bool]=None, compression: typing.Optional[grpc.Compression]=None) -> grpc.aio.UnaryUnaryCall[greeting_pb2.GreetRequest, greeting_pb2.GreetResponse]:...