from core.greeter.abc import MessageGenerator
from core.greeter.model import UserInfo
from pyprotostuben.codegen.servicify.entrypoint import entrypoint


@entrypoint
class Greeter:
    def __init__(self, greeting: MessageGenerator) -> None:
        self.__greeting = greeting

    def greet(self, user: UserInfo) -> str:
        return self.__greeting.gen_message({"username": user.name})
