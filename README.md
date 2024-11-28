# pyprotostuben

[![Latest Version](https://img.shields.io/pypi/v/pyprotostuben.svg)](https://pypi.python.org/pypi/pyprotostuben)
[![Python Supported Versions](https://img.shields.io/pypi/pyversions/pyprotostuben.svg)](https://pypi.python.org/pypi/pyprotostuben)
[![MyPy Strict](https://img.shields.io/badge/mypy-strict-blue)](https://mypy.readthedocs.io/en/stable/getting_started.html#strict-mode-and-configuration)
[![Test Coverage](https://codecov.io/gh/zerlok/pyprotostuben/branch/main/graph/badge.svg)](https://codecov.io/gh/zerlok/pyprotostuben)
[![Downloads](https://img.shields.io/pypi/dm/pyprotostuben.svg)](https://pypistats.org/packages/pyprotostuben)
[![GitHub stars](https://img.shields.io/github/stars/zerlok/pyprotostuben)](https://github.com/zerlok/pyprotostuben/stargazers)

Generate Python modules from protobuf files.

## usage

[pypi package](https://pypi.python.org/pypi/pyprotostuben)

install with your favorite python package manager

```bash
pip install pyprotostuben
```

Then use protoc plugins to generate python code. See [greeting examples](examples/greeting/README.md) for more info.

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
* `message-all-init-args-optional` -- each field is optional in message constructor (even if field is not optional)
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

* `format={raw|binary|json}` (default = `raw`) -- specify output format
* `dest={path}` (default = `request.json`) -- specify file destination
