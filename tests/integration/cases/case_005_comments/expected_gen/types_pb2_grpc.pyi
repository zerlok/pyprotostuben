import abc
import builtins
import grpc
import grpc.aio
import types_pb2
import typing

class MyServiceServicer(metaclass=abc.ABCMeta):
    """this is a comment to service"""

    @abc.abstractmethod
    async def Method(self, request: types_pb2.Msg1, context: grpc.aio.ServicerContext[types_pb2.Msg1, types_pb2.Msg2]) -> types_pb2.Msg2:
        """this is a comment to method

this is a trailing comment to method"""
        ...

def add_MyServiceServicer_to_server(servicer: MyServiceServicer, server: grpc.aio.Server) -> None:...

class MyServiceStub:
    """this is a comment to service"""

    def __init__(self, channel: grpc.aio.Channel) -> None:...

    def Method(self, request: types_pb2.Msg1, *, timeout: typing.Optional[builtins.float]=None, metadata: typing.Optional[grpc.aio.MetadataType]=None, credentials: typing.Optional[grpc.CallCredentials]=None, wait_for_ready: typing.Optional[builtins.bool]=None, compression: typing.Optional[grpc.Compression]=None) -> grpc.aio.UnaryUnaryCall[types_pb2.Msg1, types_pb2.Msg2]:
        """this is a comment to method

this is a trailing comment to method"""
        ...