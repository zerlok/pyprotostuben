import abc
import builtins
import google.protobuf.empty_pb2
import grpc
import grpc.aio
import typing

class BarServiceServicer(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    async def DoBar(self, request: google.protobuf.empty_pb2.Empty, context: grpc.aio.ServicerContext[google.protobuf.empty_pb2.Empty, google.protobuf.empty_pb2.Empty]) -> google.protobuf.empty_pb2.Empty:...

def add_BarServiceServicer_to_server(servicer: BarServiceServicer, server: grpc.aio.Server) -> None:...

class BarServiceStub:

    def __init__(self, channel: grpc.aio.Channel) -> None:...

    def DoBar(self, request: google.protobuf.empty_pb2.Empty, *, timeout: typing.Optional[builtins.float]=None, metadata: typing.Optional[grpc.aio.MetadataType]=None, credentials: typing.Optional[grpc.CallCredentials]=None, wait_for_ready: typing.Optional[builtins.bool]=None, compression: typing.Optional[grpc.Compression]=None) -> grpc.aio.UnaryUnaryCall[google.protobuf.empty_pb2.Empty, google.protobuf.empty_pb2.Empty]:...