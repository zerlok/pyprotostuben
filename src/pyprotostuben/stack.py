import abc
import typing as t
from collections import deque
from itertools import islice

T = t.TypeVar("T")
V_co = t.TypeVar("V_co", covariant=True)


class Stack(t.Generic[V_co], t.Sequence[V_co], metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def get_head(self) -> V_co:
        raise NotImplementedError

    @abc.abstractmethod
    def get_last(self) -> V_co:
        raise NotImplementedError


class MutableStack(Stack[T]):
    def __init__(self, items: t.Optional[t.Sequence[T]] = None) -> None:
        self.__impl = deque[T](items or [])

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.__impl!r})"

    @t.overload
    def __getitem__(self, index: int) -> T: ...

    @t.overload
    def __getitem__(self, index: slice) -> t.Sequence[T]: ...

    def __getitem__(self, index: t.Union[int, slice]) -> t.Union[T, t.Sequence[T]]:
        if isinstance(index, int):
            return self.__impl[index]

        elif isinstance(index, slice):
            # deque does not support slice :shrug:
            return list(islice(self.__impl, index.start, index.stop, index.step))

        else:
            raise TypeError(index)

    def index(
        self,
        value: T,
        start: int = 0,
        # can't use `t.Union[int, Ellipsis]` and interface requires `int` :shrug:
        stop: int = ...,  # type: ignore[assignment]
    ) -> int:
        return self.__impl.index(value, start, stop)

    def count(self, value: T) -> int:
        return self.__impl.count(value)

    def __contains__(self, value: object) -> bool:
        return value in self.__impl

    def __iter__(self) -> t.Iterator[T]:
        return iter(self.__impl)

    def __reversed__(self) -> t.Iterator[T]:
        return reversed(self.__impl)

    def __len__(self) -> int:
        return len(self.__impl)

    def get_head(self) -> T:
        return self[0]

    def get_last(self) -> T:
        return self[-1]

    def pop(self) -> T:
        return self.__impl.pop()

    def put(self, item: T) -> None:
        self.__impl.append(item)
