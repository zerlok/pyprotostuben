"""Source: greeting.proto"""
import abc
import brokrpc.options
import brokrpc.rpc.abc
import brokrpc.rpc.client
import brokrpc.rpc.model
import brokrpc.rpc.server
import brokrpc.serializer.protobuf
import contextlib
import greeting_pb2
import typing

class Greeter(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    async def greet(self, request: brokrpc.rpc.model.Request[greeting_pb2.GreetRequest]) -> greeting_pb2.GreetResponse:
        raise NotImplementedError

def add_greeter_to_server(service: Greeter, server: brokrpc.rpc.server.Server) -> None:
    server.register_unary_unary_handler(func=service.greet, routing_key='/greeting/Greeter/Greet', serializer=brokrpc.serializer.protobuf.RPCProtobufSerializer(greeting_pb2.GreetRequest, greeting_pb2.GreetResponse), exchange=None, queue=brokrpc.options.QueueOptions(name='/greeting/Greeter/Greet', durable=None, exclusive=None, auto_delete=None))

class GreeterClient:

    def __init__(self, greet: brokrpc.rpc.abc.Caller[greeting_pb2.GreetRequest, greeting_pb2.GreetResponse]) -> None:
        self.__greet = greet

    async def greet(self, request: greeting_pb2.GreetRequest) -> brokrpc.rpc.model.Response[greeting_pb2.GreetResponse]:
        return await self.__greet.invoke(request)

@contextlib.asynccontextmanager
async def create_greeter_client(client: brokrpc.rpc.client.Client) -> typing.AsyncIterator[GreeterClient]:
    async with client.unary_unary_caller(routing_key='/greeting/Greeter/Greet', serializer=brokrpc.serializer.protobuf.RPCProtobufSerializer(greeting_pb2.GreetRequest, greeting_pb2.GreetResponse), exchange=None) as greet:
        yield GreeterClient(greet=greet)