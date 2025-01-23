# servicify codegen

**Key Features:**

* Supports a Domain-Driven Design (DDD) approach where your business logic stays in the domain layer, and all
  transport-related code is generated.
* Generates FastAPI server code and HTTPX client code automatically based on your domain layer; gRPC support is planned
  for future versions.
    * simple request-response (aka grpc unary-unary calls) as POST http requests
    * streaming (aka grpc stream-stream calls) as websocket requests
* Uses Python’s built-in AST library to generate and render Python code.

## Usage

Currently, supports python 3.12 and higher.

1) Pull & install project from github (pypi will be added in the future)
2) Install project dependencies and extras (e.g. with poetry `poetry install --all-extras`)
    1) this will add `servicify` CLI to virtual environment, CLI code
       is [here](../../../src/pyprotostuben/codegen/servicify/cli.py).
3) add `@entrypoint` decorators to top-level classes in your domain layer code (
   e.g. [greeter](src/my_service/core/greeter/greeter.py))
4) enter the root directory of your project (e.g. [the directory of this readme file](./))
5) enter the virtual env (e.g. `poetry shell`)
6) you can check which entrypoints & methods `servicify` sees with `servicify show src --ignore-module-on-import-error`
6) run codegen with `servicify gen src fastapi --ignore-module-on-import-error` (e.g. this will generate `src/api` directory
   with python modules for this example project)
7) write server assembling code (e.g. [greeter server](src/my_service/test_server.py))
8) write client top-level code (e.g. [greeter client](test_client.py))
9) run server & client (don't forget to add src to python path, e.g. via env `PYTHONPATH=src`)
    1) `PYTHONPATH=src poetry run uvicorn --factory my_service.test_server:create_app`
    2) `PYTHONPATH=src poetry run python test_client.py`

**What’s Generated:**

* **api/models.py**: Pydantic models for requests and responses that mirror the domain objects.
* **api/client.py**: Client classes with async methods, ready to make API calls with appropriate typings for request and
  response data.
* **api/server.py**: Server handler classes, which include data serialization and domain logic invocation.

The generated code is complete, with no need for additional modifications.

## Target Audience

This tool is designed for Python developers working on services that follow the Domain-Driven Design (DDD) approach.
It's particularly useful for:

* Teams focusing on business logic without needing to handle the intricacies of APIs or transport layers.
* Developers building Python services with HTTP transport.
* Those looking for a way to streamline the development of API endpoints and client calls without the overhead of
  boilerplate code.

## Comparison

There are many tools for code generation in the Python ecosystem, but most are focused on simplifying specific tasks
like serialization, or generating CRUD operations. Here’s how my project differs:

* **Domain-Driven Design (DDD) Focus:** Unlike other code generation tools that focus on CRUD or specific transport
  protocols, my tool fully integrates with a DDD approach. This means developers work on the domain layer and let the
  tool handle the presentation layer (API endpoints and clients).
* **Fully Automated Code Generation:** The generated code for the server and client is complete and doesn’t require
  further modifications, saving time and reducing boilerplate.
* **Cross-Transport Flexibility:** Currently, it supports FastAPI and HTTPX, but future versions will add gRPC support,
  allowing developers to generate code for various transport mechanisms without changing their domain logic.

E.g. grpc requires `.proto` files specification first and generates client stubs & server interface, so on the server
side an additional code is required to do request deserialization from protobuf python classes to domain (value
objects), invoke domain layer and then serialize protobuf response.

By automating API and client creation, my tool aims to eliminate the repetitive and error-prone process of writing
endpoint handlers and clients from scratch, allowing developers to focus on their core business logic.
