"""Source: gen/greeting.proto"""
import abc
import brokrpc.options
import brokrpc.rpc.abc
import brokrpc.rpc.client
import brokrpc.rpc.model
import brokrpc.rpc.server
import brokrpc.serializer.protobuf
import contextlib
import gen.greeting_pb2
import typing

class GreeterService(metaclass=abc.ABCMeta):
    """the greeter service"""

    @abc.abstractmethod
    async def greet(self, request: brokrpc.rpc.model.Request[gen.greeting_pb2.GreetRequest]) -> gen.greeting_pb2.GreetResponse:
        """the greet method"""
        raise NotImplementedError

def add_greeter_service_to_server(service: GreeterService, server: brokrpc.rpc.server.Server) -> None:
    server.register_unary_unary_handler(func=service.greet, routing_key='/greeting/Greeter/Greet', serializer=brokrpc.serializer.protobuf.RPCProtobufSerializer(gen.greeting_pb2.GreetRequest, gen.greeting_pb2.GreetResponse), exchange=brokrpc.options.ExchangeOptions(name='greetings', type=None, durable=None, auto_delete=True), queue=brokrpc.options.QueueOptions(name='/greeting/Greeter/Greet', durable=None, exclusive=None, auto_delete=True))

class GreeterClient:
    """the greeter service"""

    def __init__(self, greet: brokrpc.rpc.abc.Caller[gen.greeting_pb2.GreetRequest, gen.greeting_pb2.GreetResponse]) -> None:
        self.__greet = greet

    async def greet(self, request: gen.greeting_pb2.GreetRequest) -> brokrpc.rpc.model.Response[gen.greeting_pb2.GreetResponse]:
        """the greet method"""
        return await self.__greet.invoke(request)

@contextlib.asynccontextmanager
async def create_client(client: brokrpc.rpc.client.Client) -> typing.AsyncIterator[GreeterClient]:
    async with client.unary_unary_caller(routing_key='/greeting/Greeter/Greet', serializer=brokrpc.serializer.protobuf.RPCProtobufSerializer(gen.greeting_pb2.GreetRequest, gen.greeting_pb2.GreetResponse), exchange=brokrpc.options.ExchangeOptions(name='greetings', type=None, durable=None, auto_delete=True)) as greet:
        yield GreeterClient(greet=greet)