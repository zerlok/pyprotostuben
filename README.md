# pyprotostuben

Generates Python MyPy stub modules from protobuf files.

## usage

install

```bash
poetry add pyprotostuben
```

available executables:

* `protoc-gen-pyprotostuben` -- a protoc plugin that generates MyPy stubs

## examples

#### requirements

* protoc
* [buf CLI](https://buf.build/product/cli)

#### project structure

* /
    * src/
        * foo.proto
            ```protobuf
            syntax = "proto3";
              
            package bar;
              
            message Spam {
                string eggs = 1;
                repeated int64 pizza = 2;
                optional string apple = 3;
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

##### src/foo_pb2.pyi

```python
import builtins
import typing

import google.protobuf.message


class Spam(google.protobuf.message.Message):

    def __init__(self, *, eggs: builtins.str, pizza: typing.Sequence[builtins.int],
                 apple: typing.Optional[builtins.str] = None) -> None: ...

    @builtins.property
    def eggs(self) -> builtins.str: ...

    @builtins.property
    def pizza(self) -> typing.Sequence[builtins.int]: ...

    @builtins.property
    def apple(self) -> builtins.str: ...

    def HasField(self, field_name: typing.Literal['apple']) -> bool: ...

    def WhichOneof(self, oneof_group: typing.NoReturn) -> typing.NoReturn: ...
```
