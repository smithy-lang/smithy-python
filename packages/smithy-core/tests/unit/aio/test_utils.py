#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from io import BytesIO

from smithy_core.aio.types import AsyncBytesProvider
from smithy_core.aio.utils import close


async def test_close_sync_closeable() -> None:
    stream = BytesIO()
    assert not stream.closed
    await close(stream)
    assert stream.closed


async def test_close_async_closeable() -> None:
    stream = AsyncBytesProvider()
    assert not stream.closed
    await close(stream)
    assert stream.closed


async def test_close_non_closeable() -> None:
    await close(b"foo")
