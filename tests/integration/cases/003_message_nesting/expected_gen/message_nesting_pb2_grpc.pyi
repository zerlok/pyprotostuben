import abc
import builtins
import grpc
import grpc.aio
import message_nesting_pb2
import typing

class ComplexServicer(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    async def UnaryUnary(self, request: message_nesting_pb2.Message1, context: grpc.aio.ServicerContext[message_nesting_pb2.Message1, message_nesting_pb2.CombinedMessage]) -> message_nesting_pb2.CombinedMessage:...

    @abc.abstractmethod
    async def StreamStream(self, request: typing.AsyncIterator[message_nesting_pb2.Message2], context: grpc.aio.ServicerContext[message_nesting_pb2.Message2, message_nesting_pb2.CombinedMessage]) -> typing.AsyncIterator[message_nesting_pb2.CombinedMessage]:...

def add_ComplexServicer_to_server(servicer: ComplexServicer, server: grpc.aio.Server) -> None:...

class ComplexStub:

    def __init__(self, channel: grpc.aio.Channel) -> None:...

    async def UnaryUnary(self, request: message_nesting_pb2.Message1, *, timeout: typing.Optional[builtins.float]=None, metadata: typing.Optional[grpc.aio.MetadataType]=None, credentials: typing.Optional[grpc.CallCredentials]=None, wait_for_ready: typing.Optional[builtins.bool]=None, compression: typing.Optional[grpc.Compression]=None) -> grpc.aio.UnaryUnaryCall[message_nesting_pb2.Message1, message_nesting_pb2.CombinedMessage]:...

    async def StreamStream(self, request: typing.AsyncIterator[message_nesting_pb2.Message2], *, timeout: typing.Optional[builtins.float]=None, metadata: typing.Optional[grpc.aio.MetadataType]=None, credentials: typing.Optional[grpc.CallCredentials]=None, wait_for_ready: typing.Optional[builtins.bool]=None, compression: typing.Optional[grpc.Compression]=None) -> grpc.aio.StreamStreamCall[message_nesting_pb2.Message2, message_nesting_pb2.CombinedMessage]:...