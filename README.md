# pyprotostuben

Generates Python MyPy stub modules from protobuf files.

## usage

install

```bash
poetry add pyprotostuben
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
            
            message GreetRequest {
              string name = 1;
            }
            
            message GreetResponse {
              string text = 1;
            }
            
            service Greeter {
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

    def __init__(self, *, name: builtins.str) -> None:...

    @builtins.property
    def name(self) -> builtins.str:...

    def HasField(self, field_name: typing.NoReturn) -> typing.NoReturn:...

    def WhichOneof(self, oneof_group: typing.NoReturn) -> typing.NoReturn:...

class GreetResponse(google.protobuf.message.Message):

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

    @abc.abstractmethod
    async def Greet(self, request: greeting_pb2.GreetRequest, context: grpc.aio.ServicerContext[greeting_pb2.GreetRequest, greeting_pb2.GreetResponse]) -> greeting_pb2.GreetResponse:...

def add_GreeterServicer_to_server(servicer: GreeterServicer, server: grpc.aio.Server) -> None:...

class GreeterStub:

    def __init__(self, channel: grpc.aio.Channel) -> None:...

    def Greet(self, request: greeting_pb2.GreetRequest, *, timeout: typing.Optional[builtins.float]=None, metadata: typing.Optional[grpc.aio.MetadataType]=None, credentials: typing.Optional[grpc.CallCredentials]=None, wait_for_ready: typing.Optional[builtins.bool]=None, compression: typing.Optional[grpc.Compression]=None) -> grpc.aio.UnaryUnaryCall[greeting_pb2.GreetRequest, greeting_pb2.GreetResponse]:...
```
