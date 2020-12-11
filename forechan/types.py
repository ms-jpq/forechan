from __future__ import annotations

from abc import abstractmethod
from typing import (
    Any,
    AsyncContextManager,
    AsyncIterable,
    Protocol,
    Sized,
    TypeVar,
    runtime_checkable,
)


T = TypeVar("T")


class ChannelClosed(Exception):
    pass


@runtime_checkable
class Channel(Sized, AsyncIterable[T], AsyncContextManager, Protocol[T]):
    @abstractmethod
    def __bool__(self) -> bool:
        ...

    @abstractmethod
    async def __anext__(self) -> T:
        ...

    @abstractmethod
    async def __aenter__(self) -> Channel[T]:
        ...

    @abstractmethod
    async def __aexit__(self, *_: Any) -> None:
        ...

    @abstractmethod
    async def close(self) -> None:
        ...

    @abstractmethod
    async def send(self, item: T) -> None:
        ...

    @abstractmethod
    async def recv(self) -> T:
        ...