import abc
import typing as t

U_contra = t.TypeVar("U_contra", contravariant=True)
V_co = t.TypeVar("V_co", covariant=True)


class Pool(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def run(self, func: t.Callable[[U_contra], V_co], args: t.Iterable[U_contra]) -> t.Iterable[V_co]:
        raise NotImplementedError
