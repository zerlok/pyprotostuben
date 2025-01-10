import asyncio

import httpx
from api.client import GreeterAsyncClient
from api.model import GreeterGreetRequest, UserInfo


async def main() -> None:
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        print(await client.get("/ping"))

        greeter = GreeterAsyncClient(client)
        response = await greeter.greet(GreeterGreetRequest(user=UserInfo(id_=42, name="John")))
        print(response.payload)


if __name__ == "__main__":
    asyncio.run(main())
