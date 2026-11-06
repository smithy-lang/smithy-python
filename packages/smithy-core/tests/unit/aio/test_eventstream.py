#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from typing import Any

from smithy_core.aio.interfaces.eventstream import AsyncEventReceiver


class _Receiver(AsyncEventReceiver[Any]):
    def __init__(self) -> None:
        self.closed = False

    async def receive(self) -> Any:
        return None

    async def close(self) -> None:
        self.closed = True


async def test_receiver_async_context_manager_closes() -> None:
    receiver = _Receiver()
    async with receiver as entered:
        assert entered is receiver
    assert receiver.closed
