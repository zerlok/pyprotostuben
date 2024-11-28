import asyncio

from brokrpc.broker import Broker
from brokrpc.rpc.model import Request
from brokrpc.rpc.server import Server
from gen.greeting_brokrpc import GreeterService, add_greeter_service_to_server
from gen.greeting_pb2 import GreetRequest, GreetResponse


# implement GreeterService
class MyService(GreeterService):
    async def greet(self, request: Request[GreetRequest]) -> GreetResponse:
        print(f"{request=!s}")
        return GreetResponse(text=f"hello, {request.body.name}")


async def main() -> None:
    broker = Broker("amqp://guest:guest@localhost:5672/")

    # create base RPC server
    server = Server(broker)

    # register `MyService` as implementation of `GreeterService`
    add_greeter_service_to_server(MyService(), server)

    # connect to broker
    async with broker:
        # run RPC server until SIGINT or SIGTERM
        await server.run_until_terminated()


if __name__ == "__main__":
    asyncio.run(main())
