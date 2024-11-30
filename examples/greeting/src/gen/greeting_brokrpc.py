"""Source: gen/greeting.proto"""
import abc
import brokrpc.abc
import brokrpc.message
import brokrpc.model
import brokrpc.options
import brokrpc.rpc.abc
import brokrpc.rpc.client
import brokrpc.rpc.model
import brokrpc.rpc.server
import brokrpc.serializer.protobuf
import contextlib
import gen.greeting_pb2
import typing

class Greeter(metaclass=abc.ABCMeta):
    """the greeter service"""

    @abc.abstractmethod
    async def greet(self, request: brokrpc.rpc.model.Request[gen.greeting_pb2.GreetRequest]) -> gen.greeting_pb2.GreetResponse:
        """the greet method"""
        raise NotImplementedError

    @abc.abstractmethod
    async def notify_greet(self, message: brokrpc.message.Message[gen.greeting_pb2.GreetResponse]) -> brokrpc.model.ConsumerResult:
        raise NotImplementedError

def add_greeter_to_server(service: Greeter, server: brokrpc.rpc.server.Server) -> None:
    server.register_unary_unary_handler(func=service.greet, routing_key='/greeting/Greeter/Greet', serializer=brokrpc.serializer.protobuf.RPCProtobufSerializer(gen.greeting_pb2.GreetRequest, gen.greeting_pb2.GreetResponse), exchange=brokrpc.options.ExchangeOptions(name='greetings', type=None, durable=None, auto_delete=True), queue=brokrpc.options.QueueOptions(name='/greeting/Greeter/Greet', durable=None, exclusive=None, auto_delete=True))
    server.register_consumer(func=service.notify_greet, routing_key='/greeting/Greeter/NotifyGreet', serializer=brokrpc.serializer.protobuf.ProtobufSerializer(gen.greeting_pb2.GreetResponse), exchange=brokrpc.options.ExchangeOptions(name='greetings', type=None, durable=None, auto_delete=True), queue=brokrpc.options.QueueOptions(name='/greeting/Greeter/NotifyGreet', durable=True, exclusive=None, auto_delete=None))

class GreeterClient:
    """the greeter service"""

    def __init__(self, greet: brokrpc.rpc.abc.Caller[gen.greeting_pb2.GreetRequest, gen.greeting_pb2.GreetResponse], notify_greet: brokrpc.abc.Publisher[gen.greeting_pb2.GreetResponse, brokrpc.model.PublisherResult]) -> None:
        self.__greet = greet
        self.__notify_greet = notify_greet

    async def greet(self, request: gen.greeting_pb2.GreetRequest) -> brokrpc.rpc.model.Response[gen.greeting_pb2.GreetResponse]:
        """the greet method"""
        return await self.__greet.invoke(request)

    async def notify_greet(self, message: gen.greeting_pb2.GreetResponse) -> None:
        await self.__notify_greet.publish(message)

@contextlib.asynccontextmanager
async def create_greeter_client(client: brokrpc.rpc.client.Client) -> typing.AsyncIterator[GreeterClient]:
    async with client.unary_unary_caller(routing_key='/greeting/Greeter/Greet', serializer=brokrpc.serializer.protobuf.RPCProtobufSerializer(gen.greeting_pb2.GreetRequest, gen.greeting_pb2.GreetResponse), exchange=brokrpc.options.ExchangeOptions(name='greetings', type=None, durable=None, auto_delete=True)) as greet, client.publisher(routing_key='/greeting/Greeter/NotifyGreet', serializer=brokrpc.serializer.protobuf.ProtobufSerializer(gen.greeting_pb2.GreetResponse), exchange=brokrpc.options.ExchangeOptions(name='greetings', type=None, durable=None, auto_delete=True)) as notify_greet:
        yield GreeterClient(greet=greet, notify_greet=notify_greet)