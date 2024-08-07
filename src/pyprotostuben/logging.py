import functools as ft
import json
import os
import re
import typing as t
from functools import cached_property
from logging import LogRecord, LoggerAdapter, getLogger, Formatter
from logging.config import dictConfig
from pathlib import Path


class Logger(
    LoggerAdapter,  # type: ignore[type-arg]
):
    @classmethod
    def configure(cls) -> None:
        config_path = Path(os.getenv("LOGGING_CONFIG", "logging.json"))

        if not config_path.exists():
            config = {
                "version": 1,
                "formatters": {
                    "brief": {
                        "format": "%(asctime)-25s %(levelname)-10s %(name)-50s %(message)s",
                    },
                    "verbose": {
                        "()": SoftFormatter,
                        "fmt": "%(asctime)-25s %(levelname)-10s %(process)-10s [%(name)s %(self)s %(funcName)s] %(message)s %(details)s",
                    },
                },
                "handlers": {
                    "stderr": {
                        "class": "logging.StreamHandler",
                        "formatter": os.getenv("LOGGING_FORMATTER", "brief"),
                        "stream": "ext://sys.stderr",
                    },
                },
                "root": {
                    "level": os.getenv("LOGGING_LEVEL", "INFO").strip().upper(),
                    "handlers": ["stderr"],
                },
            }

        else:
            with config_path.open("r") as config_fd:
                config = json.load(config_fd)

        dictConfig(config)
        cls.get(__name__).info("configured", config_path=config_path, config=config)

    # noinspection PyMethodParameters
    @classmethod
    def get(__cls, __name: str, **kwargs: object) -> "Logger":
        return __cls(getLogger(__name), kwargs)

    def process(
        self,
        msg: object,
        kwargs: t.MutableMapping[str, object],
    ) -> t.Tuple[object, t.MutableMapping[str, object]]:
        exc_info = kwargs.pop("exc_info", None)
        return msg, {
            "exc_info": exc_info,
            "extra": {**self.extra, "details": {**self.details, **kwargs}},
        }

    @ft.cached_property
    def details(self) -> t.Mapping[str, object]:
        value = self.extra.get("details")
        return value if isinstance(value, dict) else {}

    def bind(self, **kwargs: object) -> "Logger":
        return self.__class__(self.logger, {**self.extra, **kwargs}) if kwargs else self

    def bind_details(self, **kwargs: object) -> "Logger":
        return self.bind(details=kwargs) if kwargs else self


class LoggerMixin:
    @cached_property
    def _log(self) -> Logger:
        return Logger.get(f"{self.__class__.__module__}.{self.__class__.__name__}", self=hex(id(self)))


class SoftFormatter(Formatter):
    def __init__(
        self,
        fmt: t.Optional[str] = None,
        datefmt: t.Optional[str] = None,
        defaults: t.Optional[t.Mapping[str, str]] = None,
    ) -> None:
        super().__init__(fmt, datefmt)
        self.__defaults = defaults or {}
        self.__fields: t.Sequence[str] = re.findall(r"%\((?P<field>\w+)\)", fmt) if fmt is not None else []

    def formatMessage(self, record: LogRecord) -> str:
        assert self._fmt is not None
        return self._fmt % {field: getattr(record, field, self.__defaults.get(field, "")) for field in self.__fields}
