import abc
import foo_pb2
import grpc
import grpc.aio
import typing

class SpamServiceServicer(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    async def Do(self, request: foo_pb2.SpamRequest, context: grpc.aio.ServicerContext[foo_pb2.SpamRequest, foo_pb2.SpamResponse]) -> foo_pb2.SpamResponse:...

    @abc.abstractmethod
    async def Stream(self, request: typing.AsyncIterator[foo_pb2.SpamRequest], context: grpc.aio.ServicerContext[foo_pb2.SpamRequest, foo_pb2.SpamResponse]) -> typing.AsyncIterator[foo_pb2.SpamResponse]:...

def add_SpamServiceServicer_to_server(servicer: SpamServiceServicer, server: grpc.aio.Server) -> None: ...

class SpamServiceStub:

    def __init__(self, channel: grpc.aio.Channel) -> None:...

    async def Do(self, request: foo_pb2.SpamRequest, *, timeout: typing.Optional[float]=None, metadata: typing.Optional[grpc.aio.MetadataType]=None, credentials: typing.Optional[grpc.CallCredentials]=None, wait_for_ready: typing.Optional[bool]=None, compression: typing.Optional[grpc.Compression]=None) -> grpc.aio.UnaryUnaryCall[foo_pb2.SpamRequest, foo_pb2.SpamResponse]:...

    async def Stream(self, request: typing.AsyncIterator[foo_pb2.SpamRequest], *, timeout: typing.Optional[float]=None, metadata: typing.Optional[grpc.aio.MetadataType]=None, credentials: typing.Optional[grpc.CallCredentials]=None, wait_for_ready: typing.Optional[bool]=None, compression: typing.Optional[grpc.Compression]=None) -> grpc.aio.StreamStreamCall[foo_pb2.SpamRequest, foo_pb2.SpamResponse]:...