import asyncio

from brokrpc.broker import Broker
from brokrpc.rpc.client import Client
from gen.greeting_brokrpc import GreeterClient, create_client
from gen.greeting_pb2 import GreetRequest, GreetResponse


async def main() -> None:
    # connect to broker
    async with Broker("amqp://guest:guest@localhost:5672/") as broker:
        # create base RPC client
        client_session = Client(broker)

        greeting_client: GreeterClient

        # setup greeting RPC client
        async with create_client(client_session) as greeting_client:
            # send GreetRequest to GreeterService
            response = await greeting_client.greet(GreetRequest(name="Bob"))

            # work with RPC response
            print(response)
            assert isinstance(response.body, GreetResponse)
            print(response.body.text)  # hello, Bob


if __name__ == "__main__":
    asyncio.run(main())
