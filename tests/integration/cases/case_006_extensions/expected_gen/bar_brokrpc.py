"""Source: bar.proto"""
import abc
import brokrpc.options
import brokrpc.rpc.abc
import brokrpc.rpc.client
import brokrpc.rpc.model
import brokrpc.rpc.server
import brokrpc.serializer.protobuf
import contextlib
import google.protobuf.empty_pb2
import typing

class BarServiceService(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    async def do_bar(self, request: brokrpc.rpc.model.Request[google.protobuf.empty_pb2.Empty]) -> google.protobuf.empty_pb2.Empty:
        raise NotImplementedError

def add_bar_service_service_to_server(service: BarServiceService, server: brokrpc.rpc.server.Server) -> None:
    server.register_unary_unary_handler(func=service.do_bar, routing_key='/bar/BarService/DoBar', serializer=brokrpc.serializer.protobuf.RPCProtobufSerializer(google.protobuf.empty_pb2.Empty, google.protobuf.empty_pb2.Empty), exchange=brokrpc.options.ExchangeOptions(name="bar-exchange-name", type="topic", durable=True, auto_delete=True, arguments=None), queue=brokrpc.options.QueueOptions(name="bar-queue-name", durable=True, exclusive=None, auto_delete=None, arguments=None))

class BarServiceClient:

    def __init__(self, do_bar: brokrpc.rpc.abc.Caller[google.protobuf.empty_pb2.Empty, google.protobuf.empty_pb2.Empty]) -> None:
        self.__do_bar = do_bar

    async def do_bar(self, request: google.protobuf.empty_pb2.Empty) -> brokrpc.rpc.model.Response[google.protobuf.empty_pb2.Empty]:
        return await self.__do_bar.invoke(request)

@contextlib.asynccontextmanager
async def create_client(client: brokrpc.rpc.client.Client) -> typing.AsyncIterator[BarServiceClient]:
    async with client.unary_unary_caller(routing_key='/bar/BarService/DoBar', serializer=brokrpc.serializer.protobuf.RPCProtobufSerializer(google.protobuf.empty_pb2.Empty, google.protobuf.empty_pb2.Empty), exchange=brokrpc.options.ExchangeOptions(name="bar-exchange-name", type="topic", durable=True, auto_delete=True, arguments=None)) as do_bar:
        yield BarServiceClient(do_bar=do_bar)