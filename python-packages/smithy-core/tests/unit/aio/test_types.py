#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import asyncio
from io import BytesIO
from typing import Self

import pytest

from smithy_core.aio.types import (
    AsyncBytesProvider,
    AsyncBytesReader,
    SeekableAsyncBytesReader,
)
from smithy_core.exceptions import SmithyException


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


async def test_provider_requires_positive_max_chunks() -> None:
    with pytest.raises(ValueError):
        AsyncBytesProvider(max_buffered_chunks=-1)


async def drain_provider(provider: AsyncBytesProvider, dest: list[bytes]) -> None:
    async for chunk in provider:
        dest.append(chunk)


async def test_provider_reads_initial_data() -> None:
    provider = AsyncBytesProvider(intial_data=b"foo")
    result: list[bytes] = []

    # Start the read task in the background.
    read_task = asyncio.create_task(drain_provider(provider, result))

    # Wait for the buffer to drain. At that point all the data should
    # be read, but the read task won't actually be complete yet
    # because it's still waiting on future data.
    await provider.flush()
    assert result == [b"foo"]
    assert not read_task.done()

    # Now actually close the provider, which will let the read task
    # complete.
    await provider.close()
    await read_task

    # The result should not have changed
    assert result == [b"foo"]


async def test_provider_reads_written_data() -> None:
    provider = AsyncBytesProvider()
    result: list[bytes] = []

    # Start the read task in the background.
    read_task = asyncio.create_task(drain_provider(provider, result))
    await provider.write(b"foo")

    # Wait for the buffer to drain. At that point all the data should
    # be read, but the read task won't actually be complete yet
    # because it's still waiting on future data.
    await provider.flush()
    assert result == [b"foo"]
    assert not read_task.done()

    # Now actually close the provider, which will let the read task
    # complete.
    await provider.close()
    await read_task

    # The result should not have changed
    assert result == [b"foo"]


async def test_close_stops_writes() -> None:
    provider = AsyncBytesProvider()
    await provider.close()
    with pytest.raises(SmithyException):
        await provider.write(b"foo")


async def test_close_deletes_buffered_data() -> None:
    provider = AsyncBytesProvider(b"foo")
    await provider.close()
    result: list[bytes] = []
    await drain_provider(provider, result)
    assert result == []

    # We weren't able to read data, which is what we want. But here we dig into
    # the internals to be sure that the buffer is clear and no data is haning
    # around.
    assert provider._data == []  # type: ignore


async def test_only_max_chunks_buffered() -> None:
    # Initialize the provider with a max buffer of one and immediately have it
    # filled with an initial chunk.
    provider = AsyncBytesProvider(b"foo", max_buffered_chunks=1)

    # Schedule a write task. Using create_task immediately enqueues it, though it
    # won't start executing until its turn in the loop.
    write_task = asyncio.create_task(provider.write(b"bar"))

    # Suspend the current coroutine so the write task can take over. It shouldn't
    # complete because it should be waiting on the buffer to drain. One tenth of
    # a second is way more than enough time for it to complete under normal
    # circumstances.
    await asyncio.sleep(0.1)
    assert not write_task.done()

    # Now begin the read task in the background. Since it's draining the buffer, the
    # write task will become unblocked.
    result: list[bytes] = []
    read_task = asyncio.create_task(drain_provider(provider, result))

    # The read task won't be done until we close the provider, but the write task
    # should be able to complete now.
    await write_task

    # The write task and read task don't necessarily complete at the same time,
    # so we wait until the buffer is empty here.
    await provider.flush()
    assert result == [b"foo", b"bar"]

    # Now we can close the provider and wait for the read task to end.
    await provider.close()
    await read_task


async def test_close_stops_queued_writes() -> None:
    # Initialize the provider with a max buffer of one and immediately have it
    # filled with an initial chunk.
    provider = AsyncBytesProvider(b"foo", max_buffered_chunks=1)

    # Schedule a write task. Using create_task immediately enqueues it, though it
    # can't complete until the buffer is free.
    write_task = asyncio.create_task(provider.write(b"bar"))

    # Now close the provider. The write task will raise an error.
    await provider.close()

    with pytest.raises(SmithyException):
        await write_task


async def test_close_with_flush() -> None:
    # Initialize the provider with a max buffer of one and immediately have it
    # filled with an initial chunk.
    provider = AsyncBytesProvider(b"foo", max_buffered_chunks=1)

    # Schedule a write task. Using create_task immediately enqueues it, though it
    # can't complete until the buffer is free.
    write_task = asyncio.create_task(provider.write(b"bar"))

    # Now flush the provider and close it. The read task will be able to read the
    # alredy buffered data, but the write task will fail.
    close_task = asyncio.create_task(provider.close(flush=True))

    # There is a timing issue to when a write will fail. If they're in the queue
    # before the close task, they may still make it through. Here the current
    # coroutine is suspended so that both the write task and close task have a
    # chance to check their conditions and set necessary state.
    await asyncio.sleep(0.1)

    # Now we can start the read task. We can immediately await it because the close
    # task will complete in the background, which will then stop the iteration.
    result: list[bytes] = []
    await drain_provider(provider, result)

    # Ensure that the close task is complete.
    await close_task

    # The write will have been blocked by the close task, so the read task will
    # only see the initial data. The write task will raise an exception as the
    # provider closed before it could write its data.
    assert result == [b"foo"]
    with pytest.raises(SmithyException):
        await write_task
