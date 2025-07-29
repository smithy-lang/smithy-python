#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from io import BytesIO

from smithy_core.aio.types import AsyncBytesProvider
from smithy_core.aio.utils import close, seek


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


async def test_seek_sync_seekable() -> None:
    stream = BytesIO(b"foo")
    assert stream.seekable()
    assert stream.tell() == 0
    stream.read()
    assert stream.tell() == 3
    assert await seek(stream, 0, 0) == 0
    assert stream.tell() == 0


class ThinAsyncSeekableWrapper:
    def __init__(self, stream: BytesIO, seekable: bool = True) -> None:
        self._stream = stream
        self._seekable = seekable

    async def read(self, n: int = -1, /) -> bytes:
        return self._stream.read(n)

    async def seek(self, offset: int, whence: int = 0, /):
        return self._stream.seek(offset, whence)

    def seekable(self) -> bool:
        return self._seekable

    def tell(self) -> int:
        return self._stream.tell()


async def test_seek_async_seekable() -> None:
    source = BytesIO(b"foo")
    stream = ThinAsyncSeekableWrapper(source)
    assert stream.seekable()
    assert stream.tell() == 0
    await stream.read()
    assert stream.tell() == 3
    assert await seek(stream, 0, 0) == 0
    assert stream.tell() == 0


async def test_seek_respects_seekable_function() -> None:
    source = BytesIO(b"foo")
    stream = ThinAsyncSeekableWrapper(source, seekable=False)
    assert not stream.seekable()
    assert source.tell() == 0
    await stream.read()
    assert source.tell() == 3
    assert await seek(stream, 0, 0) is None
    assert source.tell() == 3
