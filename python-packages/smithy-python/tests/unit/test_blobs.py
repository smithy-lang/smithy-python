from io import BytesIO
from typing import Self

import pytest

from smithy_python.interfaces.blobs import AsyncBytesReader, SeekableAsyncBytesReader


class _AsyncIteratorWrapper:
    def __init__(self, source: BytesIO, chunk_size: int = -1):
        self._source = source
        self._chunk_size = chunk_size

    def __aiter__(self) -> Self:
        return self

    async def __anext__(self) -> bytes:
        data = self._source.read(self._chunk_size)
        if data:
            return data
        raise StopAsyncIteration


async def test_read_bytes() -> None:
    reader = AsyncBytesReader(b"foo")
    assert await reader.read() == b"foo"


async def test_seekable_read_byes() -> None:
    reader = SeekableAsyncBytesReader(b"foo")
    assert reader.tell() == 0
    assert await reader.read() == b"foo"
    assert reader.tell() == 3


async def test_read_bytearray() -> None:
    reader = AsyncBytesReader(bytearray(b"foo"))
    assert await reader.read() == b"foo"


async def test_seekable_read_bytearray() -> None:
    reader = SeekableAsyncBytesReader(bytearray(b"foo"))
    assert reader.tell() == 0
    assert await reader.read() == b"foo"
    assert reader.tell() == 3


async def test_read_byte_stream() -> None:
    source = BytesIO(b"foo")
    reader = AsyncBytesReader(source)
    assert source.tell() == 0
    assert await reader.read() == b"foo"
    assert source.tell() == 3


async def test_seekable_read_byte_stream() -> None:
    source = BytesIO(b"foo")
    reader = SeekableAsyncBytesReader(source)
    assert reader.tell() == 0
    assert source.tell() == 0
    assert await reader.read() == b"foo"
    assert reader.tell() == 3
    assert source.tell() == 3


async def test_read_async_byte_stream() -> None:
    source = BytesIO(b"foo")
    reader = AsyncBytesReader(AsyncBytesReader(source))
    assert source.tell() == 0
    assert await reader.read() == b"foo"
    assert source.tell() == 3


async def test_seekable_read_async_byte_stream() -> None:
    source = BytesIO(b"foo")
    reader = SeekableAsyncBytesReader(AsyncBytesReader(source))
    assert reader.tell() == 0
    assert source.tell() == 0
    assert await reader.read() == b"foo"
    assert reader.tell() == 3
    assert source.tell() == 3


async def test_read_async_iterator() -> None:
    source = BytesIO(b"foo")
    reader = AsyncBytesReader(_AsyncIteratorWrapper(source))
    assert source.tell() == 0
    assert await reader.read() == b"foo"
    assert source.tell() == 3

    source = BytesIO(b"foo,bar,baz\n")
    reader = AsyncBytesReader(_AsyncIteratorWrapper(source, chunk_size=6))
    assert source.tell() == 0
    assert await reader.read(4) == b"foo,"
    assert source.tell() == 6
    assert await reader.read(4) == b"bar,"
    assert source.tell() == 12
    assert await reader.read(4) == b"baz\n"
    assert source.tell() == 12


async def test_seekable_read_async_iterator() -> None:
    source = BytesIO(b"foo")
    reader = SeekableAsyncBytesReader(_AsyncIteratorWrapper(source))
    assert reader.tell() == 0
    assert source.tell() == 0
    assert await reader.read() == b"foo"
    assert reader.tell() == 3
    assert source.tell() == 3

    source = BytesIO(b"foo,bar,baz\n")
    reader = SeekableAsyncBytesReader(_AsyncIteratorWrapper(source, chunk_size=6))
    assert source.tell() == 0
    assert reader.tell() == 0
    assert await reader.read(4) == b"foo,"
    assert source.tell() == 6
    assert reader.tell() == 4
    assert await reader.read(4) == b"bar,"
    assert source.tell() == 12
    assert reader.tell() == 8
    assert await reader.read(4) == b"baz\n"
    assert source.tell() == 12
    assert reader.tell() == 12


async def test_close_closeable_source() -> None:
    source = BytesIO(b"foo")
    reader = AsyncBytesReader(source)

    assert not reader.closed
    assert not source.closed

    reader.close()

    assert reader.closed
    assert source.closed

    with pytest.raises(ValueError):
        await reader.read()


async def test_close_non_closeable_source() -> None:
    source = _AsyncIteratorWrapper(BytesIO(b"foo"))
    reader = AsyncBytesReader(source)

    assert not reader.closed
    reader.close()
    assert reader.closed

    with pytest.raises(ValueError):
        await reader.read()


async def test_seekable_close_closeable_source() -> None:
    source = BytesIO(b"foo")
    reader = SeekableAsyncBytesReader(source)

    assert not reader.closed
    assert not source.closed
    assert reader.tell() == 0

    reader.close()

    assert reader.closed
    assert source.closed

    with pytest.raises(ValueError):
        await reader.read()

    with pytest.raises(ValueError):
        reader.tell()


async def test_seekable_close_non_closeable_source() -> None:
    source = _AsyncIteratorWrapper(BytesIO(b"foo"))
    reader = SeekableAsyncBytesReader(source)

    assert not reader.closed
    assert reader.tell() == 0
    reader.close()
    assert reader.closed

    with pytest.raises(ValueError):
        await reader.read()

    with pytest.raises(ValueError):
        reader.tell()


async def test_seek() -> None:
    source = BytesIO(b"foo")
    reader = SeekableAsyncBytesReader(source)

    assert source.tell() == 0
    assert reader.tell() == 0

    assert await reader.seek(2, 0) == 2

    assert source.tell() == 2
    assert reader.tell() == 2

    assert await reader.seek(1, 1) == 3

    assert source.tell() == 3
    assert reader.tell() == 3

    assert await reader.seek(0, 0) == 0

    assert source.tell() == 3
    assert reader.tell() == 0

    source = BytesIO(b"foo")
    reader = SeekableAsyncBytesReader(source)

    assert await reader.seek(-3, 2) == 0

    assert source.tell() == 3
    assert reader.tell() == 0


async def test_read_as_iterator() -> None:
    source = BytesIO(b"foo")
    reader = AsyncBytesReader(source)

    result = b""
    async for chunk in reader:
        result += chunk

    assert result == b"foo"


async def test_seekable_read_as_iterator() -> None:
    source = BytesIO(b"foo")
    reader = SeekableAsyncBytesReader(source)

    assert reader.tell() == 0

    result = b""
    async for chunk in reader:
        result += chunk

    assert reader.tell() == 3
    assert result == b"foo"


async def test_iter_chunks() -> None:
    source = BytesIO(b"foo")
    reader = AsyncBytesReader(source)

    result = b""
    async for chunk in reader.iter_chunks(chunk_size=1):
        assert len(chunk) == 1
        result += chunk

    assert result == b"foo"


async def test_seekable_iter_chunks() -> None:
    source = BytesIO(b"foo")
    reader = SeekableAsyncBytesReader(source)

    assert reader.tell() == 0

    result = b""
    async for chunk in reader.iter_chunks(chunk_size=1):
        assert len(chunk) == 1
        result += chunk

    assert reader.tell() == 3
    assert result == b"foo"
