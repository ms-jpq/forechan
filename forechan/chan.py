from collections import deque
from typing import Deque, TypeVar, cast

from ._base import LockedBaseChan
from .types import ChannelClosed

T = TypeVar("T")


class Chan(LockedBaseChan[T]):
    def __init__(self, maxlen: int = 1) -> None:
        super().__init__()
        self._q: Deque[T] = deque(maxlen=max(1, maxlen))
        self._closed = False

    @property
    def maxlen(self) -> int:
        return cast(int, self._q.maxlen)

    def __bool__(self) -> bool:
        return not self._closed

    def __len__(self) -> int:
        return len(self._q)

    async def close(self) -> None:
        self._closed = True
        self._q.clear()
        await super().close()

    async def send(self, item: T) -> None:
        async with self._sc:
            if not self:
                raise ChannelClosed()
            elif len(self) < self.maxlen:
                async with self._rc:
                    self._rc.notify()
                    self._q.append(item)
            else:
                await self._sc.wait()
                async with self._rc:
                    if not self:
                        raise ChannelClosed()
                    else:
                        self._rc.notify()
                        self._q.append(item)

    async def recv(self) -> T:
        async with self._rc:
            if not self:
                raise ChannelClosed()
            elif len(self):
                async with self._sc:
                    self._sc.notify()
                    return self._q.popleft()
            else:
                await self._rc.wait()
                async with self._sc:
                    if not self:
                        raise ChannelClosed()
                    else:
                        self._sc.notify()
                        return self._q.popleft()
