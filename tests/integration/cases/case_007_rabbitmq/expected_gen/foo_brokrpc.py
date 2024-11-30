"""Source: foo.proto"""
import abc
import brokrpc.abc
import brokrpc.message
import brokrpc.model
import brokrpc.options
import brokrpc.rpc.client
import brokrpc.rpc.server
import brokrpc.serializer.protobuf
import contextlib
import foo_pb2
import typing

class FooService(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    async def notify_foo(self, message: brokrpc.message.Message[foo_pb2.Payload]) -> brokrpc.model.ConsumerResult:
        """this is a definition of publisher / consumer method (no response)."""
        raise NotImplementedError

def add_foo_service_to_server(service: FooService, server: brokrpc.rpc.server.Server) -> None:
    server.register_consumer(func=service.notify_foo, routing_key='/foo/FooService/NotifyFoo', serializer=brokrpc.serializer.protobuf.ProtobufSerializer(foo_pb2.Payload), exchange=None, queue=brokrpc.options.QueueOptions(name='/foo/FooService/NotifyFoo', durable=None, exclusive=None, auto_delete=None))

class FooServiceClient:

    def __init__(self, notify_foo: brokrpc.abc.Publisher[foo_pb2.Payload, brokrpc.model.PublisherResult]) -> None:
        self.__notify_foo = notify_foo

    async def notify_foo(self, message: foo_pb2.Payload) -> None:
        """this is a definition of publisher / consumer method (no response)."""
        await self.__notify_foo.publish(message)

@contextlib.asynccontextmanager
async def create_foo_service_client(client: brokrpc.rpc.client.Client) -> typing.AsyncIterator[FooServiceClient]:
    async with client.publisher(routing_key='/foo/FooService/NotifyFoo', serializer=brokrpc.serializer.protobuf.ProtobufSerializer(foo_pb2.Payload), exchange=None) as notify_foo:
        yield FooServiceClient(notify_foo=notify_foo)