from asyncio.tasks import create_task, gather
from typing import Tuple, TypeVar

from .chan import chan
from .ops import with_closing
from .select import select
from .types import Chan

T = TypeVar("T")


async def fan_in(*cs: Chan[T], cascade_close: bool = True) -> Chan[T]:
    upstream: Chan[Tuple[Chan[T], T]] = await select(*cs)
    out: Chan[T] = chan()

    async def cont() -> None:
        async with out:
            async with with_closing(upstream, close=cascade_close):
                while out and upstream:
                    await gather(out._on_sendable(), upstream._on_recvable())
                    if out.sendable() and upstream.recvable():
                        _, item = upstream.try_recv()
                        out.try_send(item)

    create_task(cont())
    return out
