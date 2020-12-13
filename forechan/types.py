from __future__ import annotations

from abc import abstractmethod, abstractproperty
from typing import (
    AsyncContextManager,
    AsyncIterable,
    ContextManager,
    Protocol,
    Sized,
    TypeVar,
    runtime_checkable,
)

T = TypeVar("T")


class ChanClosed(Exception):
    pass


class AsyncCloseable(Protocol):
    @abstractmethod
    async def close(self) -> None:
        ...


@runtime_checkable
class Chan(
    Sized, AsyncIterable[T], AsyncContextManager[None], AsyncCloseable, Protocol[T]
):
    @abstractproperty
    def maxlen(self) -> int:
        ...

    @abstractmethod
    def __bool__(self) -> bool:
        ...

    @abstractmethod
    async def __anext__(self) -> T:
        ...

    @abstractmethod
    async def send(self, item: T) -> None:
        ...

    @abstractmethod
    async def recv(self) -> T:
        ...


@runtime_checkable
class WaitGroup(Sized, ContextManager[None], Protocol):
    @abstractmethod
    async def wait(self) -> None:
        ...
