# pyprotostuben

[![Latest Version](https://img.shields.io/pypi/v/pyprotostuben.svg)](https://pypi.python.org/pypi/pyprotostuben)
[![Python Supported Versions](https://img.shields.io/pypi/pyversions/pyprotostuben.svg)](https://pypi.python.org/pypi/pyprotostuben)
[![MyPy Strict](https://img.shields.io/badge/mypy-strict-blue)](https://mypy.readthedocs.io/en/stable/getting_started.html#strict-mode-and-configuration)
[![Test Coverage](https://codecov.io/gh/zerlok/pyprotostuben/branch/main/graph/badge.svg)](https://codecov.io/gh/zerlok/pyprotostuben)
[![Downloads](https://img.shields.io/pypi/dm/pyprotostuben.svg)](https://pypistats.org/packages/pyprotostuben)
[![GitHub stars](https://img.shields.io/github/stars/zerlok/pyprotostuben)](https://github.com/zerlok/pyprotostuben/stargazers)

Generate Python modules from protobuf files.

## installation

[pypi package](https://pypi.python.org/pypi/pyprotostuben)

install with your favorite python package manager

```bash
pip install pyprotostuben
```

## protoc plugins

### protoc-gen-mypy-stub

Generates python stubs (`*_pb2.pyi` & `*_pb2_grpc.pyi` files which then used by MyPy type checker / IDE syntax highlits 
& suggestions).

**features:**

* choose message structure immutability / mutability
* choose async / sync grpc module stubs
* grpc servicer abstract methods have full signature (with appropriate type args in generics), thus it is easier to
  implement methods in IDE

**plugin options:**

* `message-mutable` -- add setters for fields, use mutable containers
* `message-all-init-args-optional` -- each field is optional in message constructor (event if required)
* `grpc-sync` -- use sync grpc stubs instead of grpc.aio module and async defs
* `grpc-skip-servicer` -- don't generate code for servicers
* `grpc-skip-stub` -- don't generate code for stubs
* `no-parallel` -- disable multiprocessing
* `debug` -- turn on plugin debugging

### protoc-gen-brokrpc

Generates `*_brokrpc.py` modules for [BrokRPC](https://github.com/zerlok/BrokRPC) framework. This is similar to gRPC 
codegen (`*_pb2_grpc.py` modules).

**plugin options:**

* `no-parallel` -- disable multiprocessing
* `debug` -- turn on plugin debugging

### protoc-gen-echo

Saves protoc plugin input to a file. Helps develop protoc plugins.

**plugin options:**

* `format={binary|json}` (default = `json`) -- specify output format
* `dest={path}` (default = `request.json`) -- specify file destination

## examples

requirements:

* [buf CLI](https://buf.build/product/cli)
* [protoc](https://grpc.io/docs/protoc-installation/)

### mypy stubs

the following project structure with protobuf file in `proto3` syntax & buf `v1beta1` condigs:

* `/`
    * `src/`
        * `greeting.proto`
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
    * `buf.yaml`
        ```yaml
        version: v1beta1
        build:
          roots:
            - src
        ```
    * `buf.gen.yaml`
        ```yaml
        version: v1
        managed:
        enabled: true
        plugins:
        - plugin: pyprotostuben
          out: out
          strategy: all
        ```

run codegen

```bash
buf generate
```

the output:

* `src/greeting_pb2.pyi`
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
* `src/greeting_pb2_grpc.pyi`
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

### BrokRPC

requirements:

* [BrokRPC](https://github.com/zerlok/BrokRPC) -- to run RPC server & client code. Installed with pip `pip install BrokRPC[aiormq]`.

create files:

* `buf.yaml`
  ```yaml
  version: v2
  modules:
    - path: src
  lint:
    use:
      - DEFAULT
  breaking:
    use:
      - FILE
  ```
* `buf.gen.yaml`
  ```yaml
  version: v2
  managed:
    enabled: true
  plugins:
    # generates python protobuf message modules (the builtin protoc python codegen)
    - protoc_builtin: python
      out: out
    # generates python mypy stubs for protobuf messages (stub generator from pyprotostuben)
    - protoc_builtin: mypy-stub
      out: out
    # generates brokrpc files with server interface and client factory (also from pyprotostuben)
    - protoc_builtin: brokrpc
      out: out
      strategy: all
  ```
* `src/greeting.proto`
  ```protobuf
  syntax = "proto3";
  
  package greeting;
  
  // the greet request
  message GreetRequest {
    string name = 1;
  }
  
  // the greet response
  message GreetResponse {
    string text = 1;
  }
  
  // the greeter service
  service Greeter {
    // the greet method
    rpc Greet(GreetRequest) returns (GreetResponse) {}
  }
  ```

then run codegen

```shell
buf generate
```

output:

* `out/greeting_pb2.py` -- generated protobuf messages
* `out/greeting_pb2.pyi` -- generated mypy stubs for messages
* `out/greeting_brokrpc.py`
  ```python
  """Source: greeting.proto"""
  import abc
  import brokrpc.rpc.abc
  import brokrpc.rpc.client
  import brokrpc.rpc.model
  import brokrpc.rpc.server
  import brokrpc.serializer.protobuf
  import contextlib
  import greeting_pb2
  import typing
  
  class GreeterService(metaclass=abc.ABCMeta):
      """the greeter service"""
  
      @abc.abstractmethod
      async def greet(self, request: brokrpc.rpc.model.Request[greeting_pb2.GreetRequest]) -> greeting_pb2.GreetResponse:
          """the greet method"""
          raise NotImplementedError
  
  def add_greeter_service_to_server(service: GreeterService, server: brokrpc.rpc.server.Server) -> None:
      server.register_unary_unary_handler(func=service.greet, routing_key='/greeting/Greeter/greet', serializer=brokrpc.serializer.protobuf.RPCProtobufSerializer(greeting_pb2.GreetRequest, greeting_pb2.GreetResponse))
  
  class GreeterClient:
      """the greeter service"""
  
      def __init__(self, greet: brokrpc.rpc.abc.Caller[greeting_pb2.GreetRequest, greeting_pb2.GreetResponse]) -> None:
          self.__greet = greet
  
      async def greet(self, request: greeting_pb2.GreetRequest) -> brokrpc.rpc.model.Response[greeting_pb2.GreetResponse]:
          """the greet method"""
          return await self.__greet.invoke(request)
  
  @contextlib.asynccontextmanager
  async def create_client(client: brokrpc.rpc.client.Client) -> typing.AsyncIterator[GreeterClient]:
      async with client.unary_unary_caller(routing_key='/greeting/Greeter/greet', serializer=brokrpc.serializer.protobuf.RPCProtobufSerializer(greeting_pb2.GreetRequest, greeting_pb2.GreetResponse)) as greet:
          yield GreeterClient(greet=greet)
  ```

now on the server side you can implement the `GreeterService`, pass it to `add_greeter_service_to_server` and run the
**RPC server**.

```python
import asyncio

from brokrpc.broker import Broker
from brokrpc.options import ExchangeOptions
from brokrpc.rpc.model import Request
from brokrpc.rpc.server import Server
from greeting_pb2 import GreetRequest, GreetResponse
from greeting_brokrpc import GreeterService, add_greeter_service_to_server


class MyService(GreeterService):
    async def greet(self, request: Request[GreetRequest]) -> GreetResponse:
        return GreetResponse(text=f"hello, {request.body.name}")


async def main() -> None:
    broker = Broker("amqp://guest:guest@localhost:5672/", default_exchange=ExchangeOptions(name="test-greet-codegen"))
    
    server = Server(broker)
    add_greeter_service_to_server(MyService(), server)
    
    await server.run_until_terminated()

    
if __name__ == "__main__":
  asyncio.run(main())
```

on the client side you just have to get the client from `create_client` using **RPC client** and you ready to send
requests to greeter RPC server.

```python
import asyncio

from brokrpc.broker import Broker
from brokrpc.options import ExchangeOptions
from brokrpc.rpc.client import Client
from greeting_pb2 import GreetRequest, GreetResponse
from greeting_brokrpc import GreeterClient, create_client


async def main() -> None:
    async with Broker("amqp://guest:guest@localhost:5672/", default_exchange=ExchangeOptions(name="test-greet-codegen")) as broker:
        client_session = Client(broker)
        
        greeting_client: GreeterClient
        
        async with create_client(client_session) as greeting_client:
            response = await greeting_client.greet(GreetRequest(name="Bob"))
            print(response)
            assert isinstance(response.body, GreetResponse)
            print(response.body.text)  # hello, Bob


if __name__ == "__main__":
  asyncio.run(main())
```
