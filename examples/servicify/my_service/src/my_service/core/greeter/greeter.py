from my_service.core.greeter.abc import MessageGenerator
from my_service.core.greeter.model import UserInfo
from pyprotostuben.codegen.servicify.entrypoint import entrypoint


@entrypoint
class Greeter:
    def __init__(self, greeting: MessageGenerator) -> None:
        self.__greeting = greeting
        self.__previous: list[str] = []

    def greet(self, user: UserInfo) -> str:
        """Make a greeting message for a user."""
        return self.__greeting.gen_message({"username": user.name, "previous_greetings": self.__previous})

    def notify_greeted(self, user: UserInfo, message: str) -> None:
        self.__previous.append(message)
