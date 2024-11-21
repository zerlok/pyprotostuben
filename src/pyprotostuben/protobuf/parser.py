import typing as t
from dataclasses import dataclass


@dataclass(frozen=True)
class Parameter:
    name: t.Optional[str]
    value: str


class CodeGeneratorParameters:
    def __init__(self, params: t.Sequence[Parameter]) -> None:
        self.__params = params
        self.__flags = [param.value for param in self.__params if param.name is None]
        self.__named_params: t.Mapping[str, str] = {
            param.name: param.value for param in self.__params if param.name is not None
        }

    def get_by_index(self, idx: int) -> str:
        return self.__params[idx].value

    def has_flag(self, name: str) -> bool:
        return name in self.__flags

    @t.overload
    def get_raw_by_name(self, name: str) -> str: ...

    @t.overload
    def get_raw_by_name(self, name: str, default: str) -> str: ...

    def get_raw_by_name(self, name: str, default: t.Optional[str] = None) -> str:
        if default is not None:
            return self.__named_params.get(name, default)

        return self.__named_params[name]


class ParameterParser:
    def iter_parse(self, params: str) -> t.Iterable[Parameter]:
        for pair in params.split(","):
            try:
                name, value = pair.split("=", maxsplit=1)

            except ValueError:
                name = None
                value = pair

            yield Parameter(name, value)

    def parse(self, params: str) -> CodeGeneratorParameters:
        return CodeGeneratorParameters(list(self.iter_parse(params)))
