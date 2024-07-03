import abc
import builtins
import grpc
import grpc.aio
import grpc_service_pb2
import typing

class ServiceServicer(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    async def DoUnaryUnary(self, request: grpc_service_pb2.Request, context: grpc.aio.ServicerContext[grpc_service_pb2.Request, grpc_service_pb2.Response]) -> grpc_service_pb2.Response:...

    @abc.abstractmethod
    async def DoUnaryStream(self, request: grpc_service_pb2.Request, context: grpc.aio.ServicerContext[grpc_service_pb2.Request, grpc_service_pb2.Response]) -> typing.AsyncIterator[grpc_service_pb2.Response]:...

    @abc.abstractmethod
    async def DoStreamUnary(self, request: typing.AsyncIterator[grpc_service_pb2.Request], context: grpc.aio.ServicerContext[grpc_service_pb2.Request, grpc_service_pb2.Response]) -> grpc_service_pb2.Response:...

    @abc.abstractmethod
    async def DoStreamStream(self, request: typing.AsyncIterator[grpc_service_pb2.Request], context: grpc.aio.ServicerContext[grpc_service_pb2.Request, grpc_service_pb2.Response]) -> typing.AsyncIterator[grpc_service_pb2.Response]:...

def add_ServiceServicer_to_server(servicer: ServiceServicer, server: grpc.aio.Server) -> None:...

class ServiceStub:

    def __init__(self, channel: grpc.aio.Channel) -> None:...

    async def DoUnaryUnary(self, request: grpc_service_pb2.Request, *, timeout: typing.Optional[builtins.float]=None, metadata: typing.Optional[grpc.aio.MetadataType]=None, credentials: typing.Optional[grpc.CallCredentials]=None, wait_for_ready: typing.Optional[builtins.bool]=None, compression: typing.Optional[grpc.Compression]=None) -> grpc.aio.UnaryUnaryCall[grpc_service_pb2.Request, grpc_service_pb2.Response]:...

    async def DoUnaryStream(self, request: grpc_service_pb2.Request, *, timeout: typing.Optional[builtins.float]=None, metadata: typing.Optional[grpc.aio.MetadataType]=None, credentials: typing.Optional[grpc.CallCredentials]=None, wait_for_ready: typing.Optional[builtins.bool]=None, compression: typing.Optional[grpc.Compression]=None) -> grpc.aio.UnaryStreamCall[grpc_service_pb2.Request, grpc_service_pb2.Response]:...

    async def DoStreamUnary(self, request: typing.AsyncIterator[grpc_service_pb2.Request], *, timeout: typing.Optional[builtins.float]=None, metadata: typing.Optional[grpc.aio.MetadataType]=None, credentials: typing.Optional[grpc.CallCredentials]=None, wait_for_ready: typing.Optional[builtins.bool]=None, compression: typing.Optional[grpc.Compression]=None) -> grpc.aio.StreamUnaryCall[grpc_service_pb2.Request, grpc_service_pb2.Response]:...

    async def DoStreamStream(self, request: typing.AsyncIterator[grpc_service_pb2.Request], *, timeout: typing.Optional[builtins.float]=None, metadata: typing.Optional[grpc.aio.MetadataType]=None, credentials: typing.Optional[grpc.CallCredentials]=None, wait_for_ready: typing.Optional[builtins.bool]=None, compression: typing.Optional[grpc.Compression]=None) -> grpc.aio.StreamStreamCall[grpc_service_pb2.Request, grpc_service_pb2.Response]:...