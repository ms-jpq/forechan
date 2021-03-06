from asyncio import TimeoutError, gather, wait_for
from itertools import islice
from random import shuffle
from typing import Any, Awaitable, MutableSequence, TypeVar
from unittest import IsolatedAsyncioTestCase

from ...forechan.chan import chan
from ...forechan.types import Chan, ChanClosed, ChanEmpty, ChanFull
from ..consts import BIG_REP_FACTOR, MODICUM_TIME, SMOL_REP_FACTOR, SMOL_TIME

T = TypeVar("T")


class Setup:
    class Chan(IsolatedAsyncioTestCase):
        async def asyncSetUp(self) -> None:
            self.ch = chan(int)


class TypeConformance(Setup.Chan):
    async def test_1(self) -> None:
        self.assertIsInstance(self.ch, Chan)


class Close(Setup.Chan):
    async def test_1(self) -> None:
        self.assertTrue(self.ch)

    async def test_2(self) -> None:
        await self.ch.aclose()
        self.assertFalse(self.ch)

    async def test_3(self) -> None:
        await (self.ch << 1)

        async def c1() -> None:
            with self.assertRaises(ChanClosed):
                await (self.ch << 1)

        async def c2() -> None:
            with self.assertRaises(ChanClosed):
                await (self.ch << 1)

        await self.ch.aclose()
        await gather(c1(), c2())

    async def test_4(self) -> None:
        async def c1() -> None:
            with self.assertRaises(ChanClosed):
                await ([] << self.ch)

        async def c2() -> None:
            with self.assertRaises(ChanClosed):
                await ([] << self.ch)

        await self.ch.aclose()
        await gather(c1(), c2())


class SendRecvSync(Setup.Chan):
    async def test_1(self) -> None:
        (self.ch < 1)
        iden = [] < self.ch
        self.assertEqual(iden, 1)

    async def test_2(self) -> None:
        (self.ch < 1)
        with self.assertRaises(ChanFull):
            (self.ch < 1)

    async def test_3(self) -> None:
        with self.assertRaises(ChanEmpty):
            ([] < self.ch)


class SendRecv(Setup.Chan):
    async def test_1(self) -> None:
        await (self.ch << 1)
        iden = await ([] << self.ch)
        self.assertEqual(iden, 1)

    async def test_2(self) -> None:
        await (self.ch << 1)
        self.assertTrue(self.ch.recvable())

    async def test_3(self) -> None:
        (self.ch < 1)
        self.assertTrue(self.ch.recvable())

    async def test_4(self) -> None:
        self.assertFalse(self.ch.recvable())

class SendToClosed(Setup.Chan):
    async def test_1(self) -> None:
        await self.ch.aclose()
        with self.assertRaises(ChanClosed):
            await (self.ch << 1)


class RecvFromClosed(Setup.Chan):
    async def test_1(self) -> None:
        await self.ch.aclose()
        with self.assertRaises(ChanClosed):
            await ([] << self.ch)


class DoubleSend(Setup.Chan):
    async def test_1(self) -> None:
        with self.assertRaises(TimeoutError):
            await (self.ch << 1)
            await wait_for(self.ch << 1, timeout=SMOL_TIME)


class EmptyRecv(Setup.Chan):
    async def test_1(self) -> None:
        with self.assertRaises(TimeoutError):
            await wait_for([] << self.ch, timeout=SMOL_TIME)


class ManySendRecv(Setup.Chan):
    async def test_1(self) -> None:
        await (self.ch << 1)
        await gather(self.ch << 1, [] << self.ch)
        await ([] << self.ch)
        self.assertEqual(len(self.ch), 0)

    async def test_2(self) -> None:
        async def cont() -> None:
            await gather([] << self.ch, [] << self.ch)

        await wait_for(gather(cont(), self.ch << 1, self.ch << 1), timeout=SMOL_TIME)

    async def test_3(self) -> None:
        async def c1() -> None:
            async with self.ch:
                for i in range(SMOL_REP_FACTOR + 1):
                    await (self.ch << i)

        async def c2() -> None:
            i = -1
            async for i in self.ch:
                pass
            self.assertEqual(i, SMOL_REP_FACTOR)

        await wait_for(gather(c1(), c2()), timeout=MODICUM_TIME)

    async def test_4(self) -> None:
        sends = islice(iter(lambda: self.ch << 1, None), BIG_REP_FACTOR)
        recvs = islice(iter(lambda: () << self.ch, None), BIG_REP_FACTOR)
        cos: MutableSequence[Awaitable[Any]] = [*sends, *recvs]
        shuffle(cos)
        await wait_for(gather(*cos), timeout=MODICUM_TIME)
        self.assertEqual(len(self.ch), 0)


class ClosedNotif(Setup.Chan):
    async def test_1(self) -> None:
        with self.assertRaises(TimeoutError):
            await wait_for(self.ch._on_closed(), timeout=SMOL_TIME)

    async def test_2(self) -> None:
        await self.ch.aclose()
        await wait_for(self.ch._on_closed(), timeout=SMOL_TIME)

    async def test_3(self) -> None:
        await self.ch.aclose()
        ch1 = await wait_for(self.ch._on_sendable(), timeout=SMOL_TIME)
        ch2 = await wait_for(self.ch._on_recvable(), timeout=SMOL_TIME)
        self.assertFalse(ch1)
        self.assertFalse(ch2)


class SendableNotif(Setup.Chan):
    async def test_1(self) -> None:
        await (self.ch << 1)
        with self.assertRaises(TimeoutError):
            await wait_for(self.ch._on_sendable(), timeout=SMOL_TIME)

    async def test_2(self) -> None:
        await wait_for(self.ch._on_sendable(), timeout=SMOL_TIME)


class RecvableNotif(Setup.Chan):
    async def test_1(self) -> None:
        with self.assertRaises(TimeoutError):
            await wait_for(self.ch._on_recvable(), timeout=SMOL_TIME)

    async def test_2(self) -> None:
        await (self.ch << 1)
        await wait_for(self.ch._on_recvable(), timeout=SMOL_TIME)
