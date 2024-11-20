# pyprotostuben

[![Python Supported versions](https://img.shields.io/pypi/pyversions/pyprotostuben.svg)](https://pypi.python.org/pypi/pyprotostuben)
[![MyPy Strict](https://img.shields.io/badge/mypy-strict-blue)](https://mypy.readthedocs.io/en/stable/getting_started.html#strict-mode-and-configuration)
[![Test Coverage](https://codecov.io/gh/zerlok/pyprotostuben/branch/main/graph/badge.svg)](https://codecov.io/gh/zerlok/pyprotostuben)
[![Downloads](https://img.shields.io/pypi/dm/pyprotostuben.svg)](https://pypistats.org/packages/pyprotostuben)
[![GitHub stars](https://img.shields.io/github/stars/zerlok/pyprotostuben)](https://github.com/zerlok/pyprotostuben/stargazers)

Generate Python MyPy stub modules from protobuf files.

## usage

install into dev dependencies group

```bash
poetry add --group dev pyprotostuben
```

### protoc-gen-pyprotostuben

a protoc plugin that generates MyPy stubs

#### features

* choose message structure immutability / mutability
* choose async / sync grpc module stubs
* grpc servicer abstract methods have full signature (with appropriate type args in generics), thus it is easier to
  implement methods in IDE

#### flags

* `message-mutable` -- add setters for fields, use mutable containers
* `message-all-init-args-optional` -- each field is optional in message constructor (event if required)
* `grpc-sync` -- use sync grpc stubs instead of grpc.aio module and async defs
* `grpc-skip-servicer` -- don't generate code for servicers
* `grpc-skip-stub` -- don't generate code for stubs

## examples

#### requirements

* protoc
* [buf CLI](https://buf.build/product/cli)

#### project structure

* /
    * src/
        * greeting.proto
            ```protobuf
            syntax = "proto3";
            
            package greeting;
            
            // RPC request for greeting
            message GreetRequest {
              string name = 1;
            }
            
            // RPC response for greeting
            message GreetResponse {
              string text = 1;
            }
            
            // RPC service that provides greet functionality
            service Greeter {
              // RPC method for greeting
              rpc Greet(GreetRequest) returns (GreetResponse) {}
            }
            ```
    * buf.yaml
        ```yaml
        version: v1beta1
        build:
          roots:
            - src
        ```
    * buf.gen.yaml
        ```yaml
        version: v1
        managed:
        enabled: true
        plugins:
        - plugin: pyprotostuben
          out: out
          strategy: all
        ```

#### run codegen

```bash
buf generate
```

#### output

##### src/greeting_pb2.pyi

```python
import builtins
import google.protobuf.message
import typing

class GreetRequest(google.protobuf.message.Message):
    """RPC request for greeting"""

    def __init__(self, *, name: builtins.str) -> None:...

    @builtins.property
    def name(self) -> builtins.str:...

    def HasField(self, field_name: typing.NoReturn) -> typing.NoReturn:...

    def WhichOneof(self, oneof_group: typing.NoReturn) -> typing.NoReturn:...

class GreetResponse(google.protobuf.message.Message):
    """RPC response for greeting"""

    def __init__(self, *, text: builtins.str) -> None:...

    @builtins.property
    def text(self) -> builtins.str:...

    def HasField(self, field_name: typing.NoReturn) -> typing.NoReturn:...

    def WhichOneof(self, oneof_group: typing.NoReturn) -> typing.NoReturn:...
```

##### src/greeting_pb2_grpc.pyi

```python
import abc
import builtins
import greeting_pb2
import grpc
import grpc.aio
import typing

class GreeterServicer(metaclass=abc.ABCMeta):
    """RPC service that provides greet functionality"""

    @abc.abstractmethod
    async def Greet(self, request: greeting_pb2.GreetRequest, context: grpc.aio.ServicerContext[greeting_pb2.GreetRequest, greeting_pb2.GreetResponse]) -> greeting_pb2.GreetResponse:
        """RPC method for greeting"""
        ...

def add_GreeterServicer_to_server(servicer: GreeterServicer, server: grpc.aio.Server) -> None:...

class GreeterStub:
    """RPC service that provides greet functionality"""

    def __init__(self, channel: grpc.aio.Channel) -> None:...

    def Greet(self, request: greeting_pb2.GreetRequest, *, timeout: typing.Optional[builtins.float]=None, metadata: typing.Optional[grpc.aio.MetadataType]=None, credentials: typing.Optional[grpc.CallCredentials]=None, wait_for_ready: typing.Optional[builtins.bool]=None, compression: typing.Optional[grpc.Compression]=None) -> grpc.aio.UnaryUnaryCall[greeting_pb2.GreetRequest, greeting_pb2.GreetResponse]:
        """RPC method for greeting"""
        ...
```
