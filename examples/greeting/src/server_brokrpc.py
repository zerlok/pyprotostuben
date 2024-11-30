import asyncio

from brokrpc.broker import Broker
from brokrpc.message import Message
from brokrpc.rpc.model import Request
from brokrpc.rpc.server import Server
from gen.greeting_brokrpc import Greeter, add_greeter_to_server
from gen.greeting_pb2 import GreetRequest, GreetResponse


# implement Greeter
class MyGreeter(Greeter):
    async def greet(self, request: Request[GreetRequest]) -> GreetResponse:
        print(f"greet: {request=!s}")
        return GreetResponse(text=f"hello, {request.body.name}")

    async def notify_greet(self, message: Message[GreetResponse]) -> None:
        print(f"started notify: {message!s}")
        # simulate long message consumption
        await asyncio.sleep(5.0)
        print(f"finished notify: {message!s}")


async def main() -> None:
    broker = Broker("amqp://guest:guest@localhost:5672/")

    # create base RPC server
    server = Server(broker)

    # register `MyGreeter` as implementation of `Greeter`
    add_greeter_to_server(MyGreeter(), server)

    # connect to broker
    async with broker:
        # run RPC server until SIGINT or SIGTERM
        await server.run_until_terminated()


if __name__ == "__main__":
    asyncio.run(main())
