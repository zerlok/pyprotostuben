import typing as t
from contextlib import contextmanager
from multiprocessing.pool import Pool as _PoolImpl

from pyprotostuben.logging import LoggerMixin
from pyprotostuben.pool.abc import Pool

U_contra = t.TypeVar("U_contra", contravariant=True)
V_co = t.TypeVar("V_co", covariant=True)


class SingleProcessPool(Pool, LoggerMixin):
    def run(self, func: t.Callable[[U_contra], V_co], args: t.Iterable[U_contra]) -> t.Iterable[V_co]:
        log = self._log.bind_details(func=func)
        log.debug("started")

        for arg in args:
            yield func(arg)

        log.info("run", func=func)


class MultiProcessPool(Pool, LoggerMixin):
    @classmethod
    @contextmanager
    def setup(cls) -> t.Iterator["MultiProcessPool"]:
        with _PoolImpl() as pool:
            yield cls(pool)

    def __init__(self, impl: _PoolImpl) -> None:
        self.__impl = impl

    def run(self, func: t.Callable[[U_contra], V_co], args: t.Iterable[U_contra]) -> t.Iterable[V_co]:
        log = self._log.bind_details(func=func)
        log.debug("started")

        for result in self.__impl.imap_unordered(func=func, iterable=args):
            self._log.debug("result received")
            yield result

        log.info("run")
