#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import asyncio
from asyncio import iscoroutinefunction
from collections import deque
from collections.abc import AsyncIterable, AsyncIterator, Awaitable, Callable
from io import BytesIO
from typing import Any, Self, cast

from ..exceptions import SmithyException
from ..interfaces import BytesReader
from .interfaces import AsyncByteStream, StreamingBlob
from .utils import close

# The default chunk size for iterating streams.
_DEFAULT_CHUNK_SIZE = 1024


# asyncio has a StreamReader class which you might think would be appropriate here,
# but it is unfortunately tied to the asyncio http interfaces.
class AsyncBytesReader:
    """A file-like object with an async read method."""

    # BytesIO *is* a ByteStream, but mypy will nevertheless complain if it isn't here.
    _data: BytesReader | AsyncByteStream | AsyncIterable[bytes] | BytesIO | None
    _closed = False

    def __init__(self, data: StreamingBlob):
        """Initializes self.

        Data is read from the source on an as-needed basis and is not buffered.

        :param data: The source data to read from.
        """
        self._remainder = b""
        # pylint: disable-next=isinstance-second-argument-not-valid-type
        if isinstance(data, bytes | bytearray):
            self._data = BytesIO(data)
        else:
            self._data = data

    async def read(self, size: int = -1) -> bytes:
        """Read a number of bytes from the stream.

        :param size: The maximum number of bytes to read. If less than 0, all bytes will
            be read.
        """
        if self._closed or not self._data:
            raise ValueError("I/O operation on closed file.")

        if isinstance(self._data, BytesReader) and not iscoroutinefunction(  # type: ignore - TODO(pyright)
            self._data.read
        ):
            # Python's runtime_checkable can't actually tell the difference between
            # sync and async, so we have to check ourselves.
            return self._data.read(size)

        if isinstance(self._data, AsyncByteStream):  # type: ignore - TODO(pyright)
            return await self._data.read(size)

        return await self._read_from_iterable(
            cast(AsyncIterable[bytes], self._data), size
        )

    async def _read_from_iterable(
        self, iterator: AsyncIterable[bytes], size: int
    ) -> bytes:
        # This takes the iterator as an arg here just to avoid mypy complaints, since
        # we know it's an iterator where this is called.
        result = self._remainder
        if size < 0:
            async for element in iterator:
                result += element
            self._remainder = b""
            return result

        if len(result) < size:
            async for element in iterator:
                result += element
                if len(result) >= size:
                    break

        self._remainder = result[size:]
        return result[:size]

    def __aiter__(self) -> AsyncIterator[bytes]:
        return self.iter_chunks()

    def iter_chunks(
        self, chunk_size: int = _DEFAULT_CHUNK_SIZE
    ) -> AsyncIterator[bytes]:
        """Iterate over the reader in chunks of a given size.

        :param chunk_size: The maximum size of each chunk. If less than 0, the entire
            reader will be read into one chunk.
        """
        return _AsyncByteStreamIterator(self.read, chunk_size)

    def readable(self) -> bool:
        """Returns whether the stream is readable."""
        return True

    def writeable(self) -> bool:
        """Returns whether the stream is writeable."""
        return False

    def seekable(self) -> bool:
        """Returns whether the stream is seekable."""
        return False

    @property
    def closed(self) -> bool:
        """Returns whether the stream is closed."""
        return self._closed

    async def close(self) -> None:
        """Closes the stream, as well as the underlying stream where possible."""
        self._closed = True
        await close(self._data)
        self._data = None


class SeekableAsyncBytesReader:
    """A file-like object with async read and seek methods."""

    def __init__(self, data: StreamingBlob):
        """Initializes self.

        Data is read from the source on an as-needed basis and buffered internally so
        that it can be rewound safely.

        :param data: The source data to read from.
        """
        # pylint: disable-next=isinstance-second-argument-not-valid-type
        if isinstance(data, bytes | bytearray):
            self._buffer = BytesIO(data)
            self._data_source = None
        elif isinstance(data, AsyncByteStream) and iscoroutinefunction(data.read):  # type: ignore - TODO(pyright)
            # Note that we need that iscoroutine check because python won't actually check
            # whether or not the read function is async.
            self._buffer = BytesIO()
            self._data_source = data
        else:
            self._buffer = BytesIO()
            self._data_source = AsyncBytesReader(data)

    async def read(self, size: int = -1) -> bytes:
        """Read a number of bytes from the stream.

        :param size: The maximum number of bytes to read. If less than 0, all bytes will
            be read.
        """
        if self._data_source is None or size == 0:
            return self._buffer.read(size)

        start = self._buffer.tell()
        current_buffer_size = self._buffer.seek(0, 2)

        if size < 0:
            await self._read_into_buffer(size)
        elif (target := start + size) > current_buffer_size:
            amount_to_read = target - current_buffer_size
            await self._read_into_buffer(amount_to_read)

        self._buffer.seek(start, 0)
        return self._buffer.read(size)

    async def seek(self, offset: int, whence: int = 0) -> int:
        """Moves the cursor to a position relatve to the position indicated by whence.

        Whence can have one of three values:

        * 0 => The offset is relative to the start of the stream.

        * 1 => The offset is relative to the current location of the cursor.

        * 2 => The offset is relative to the end of the stream.

        :param offset: The amount of movement to be done relative to whence.
        :param whence: The location the offset is relative to.
        :returns: Returns the new position of the cursor.
        """
        if self._data_source is None:
            return self._buffer.seek(offset, whence)

        if whence >= 2:
            # If the seek is relative to the end of the stream, we need to read the
            # whole thing in from the source.
            self._buffer.seek(0, 2)
            self._buffer.write(await self._data_source.read())
            return self._buffer.seek(offset, whence)

        start = self.tell()
        target = offset
        if whence == 1:
            target += start

        current_buffer_size = self._buffer.seek(0, 2)
        if current_buffer_size < target:
            await self._read_into_buffer(target - current_buffer_size)

        return self._buffer.seek(target, 0)

    async def _read_into_buffer(self, size: int) -> None:
        if self._data_source is None:
            return

        read_bytes = await self._data_source.read(size)
        if len(read_bytes) < size or size < 0:
            self._data_source = None

        self._buffer.seek(0, 2)
        self._buffer.write(read_bytes)

    def tell(self) -> int:
        """Returns the position of the cursor."""
        return self._buffer.tell()

    def __aiter__(self) -> AsyncIterator[bytes]:
        return self.iter_chunks()

    def iter_chunks(
        self, chunk_size: int = _DEFAULT_CHUNK_SIZE
    ) -> AsyncIterator[bytes]:
        """Iterate over the reader in chunks of a given size.

        :param chunk_size: The maximum size of each chunk. If less than 0, the entire
            reader will be read into one chunk.
        """
        return _AsyncByteStreamIterator(self.read, chunk_size)

    def readable(self) -> bool:
        """Returns whether the stream is readable."""
        return True

    def writeable(self) -> bool:
        """Returns whether the stream is writeable."""
        return False

    def seekable(self) -> bool:
        """Returns whether the stream is seekable."""
        return True

    @property
    def closed(self) -> bool:
        """Returns whether the stream is closed."""
        return self._buffer.closed

    async def close(self) -> None:
        """Closes the stream, as well as the underlying stream where possible."""
        self._buffer.close()
        await close(self._data_source)
        self._data_source = None


class _AsyncByteStreamIterator:
    """An async bytes iterator that operates over an async read method."""

    def __init__(self, read: Callable[[int], Awaitable[bytes]], chunk_size: int):
        """Initializes self.

        :param read: An async callable that reads a given number of bytes from some
            source.
        :param chunk_size: The number of bytes to read in each iteration.
        """
        self._read = read
        self._chunk_size = chunk_size

    def __aiter__(self) -> Self:
        return self

    async def __anext__(self) -> bytes:
        data = await self._read(self._chunk_size)
        if data:
            return data
        raise StopAsyncIteration


class AsyncBytesProvider:
    """A buffer that allows chunks of bytes to be exchanged asynchronously.

    Bytes are written in chunks to an internal buffer, that is then drained via an async
    iterator.
    """

    def __init__(
        self, intial_data: bytes | None = None, max_buffered_chunks: int = 16
    ) -> None:
        """Initialize the AsyncBytesProvider.

        :param initial_data: An initial chunk of bytes to make available.
        :param max_buffered_chunks: The maximum number of chunks of data to buffer.
            Calls to ``write`` will block until the number of chunks is less than this
            number. Default is 16.
        """
        self._data = deque[bytes]()
        if intial_data is not None:
            self._data.append(intial_data)

        if max_buffered_chunks < 1:
            raise ValueError(
                "The maximum number of buffered chunks must be greater than 0."
            )

        self._closed = False
        self._closing = False
        self._flushing = False
        self._max_buffered_chunks = max_buffered_chunks

        # Create a Condition to synchronize access to the data chunk pool.
        self._data_condition = asyncio.Condition()

    async def write(self, data: bytes) -> None:
        if self._closed:
            raise SmithyException("Attempted to write to a closed provider.")

        # Acquire a lock on the data buffer, releasing it automatically when the
        # block exits.
        async with self._data_condition:
            # Wait for the number of chunks in the buffer to be less than the
            # specified maximum. This also releases the lock until that condition
            # is met.
            await self._data_condition.wait_for(self._can_write)

            # The provider could have been closed while waiting to write, so an
            # additional check is done here for safety.
            if self._closed or self._closing:
                # Notify to allow other coroutines to check their conditions.
                self._data_condition.notify()
                raise SmithyException(
                    "Attempted to write to a closed or closing provider."
                )

            # Add a new chunk of data to the buffer and notify the next waiting
            # coroutine.
            self._data.append(data)
            self._data_condition.notify()

    def _can_write(self) -> bool:
        return (
            self._closed
            or self._closing
            or (len(self._data) < self._max_buffered_chunks and not self._flushing)
        )

    @property
    def closed(self) -> bool:
        """Returns whether the provider is closed."""
        return self._closed

    async def flush(self) -> None:
        """Waits for all buffered data to be consumed."""
        if self._closed:
            return

        # Acquire a lock on the data buffer, releasing it automatically when the
        # block exits.
        async with self._data_condition:
            # Block writes
            self._flushing = True

            # Wait for the stream to be closed or for the data buffer to be empty,
            # releasing the lock until the condition is met.
            await self._data_condition.wait_for(lambda: len(self._data) == 0)

            # Unblock writes
            self._flushing = False

    async def close(self, flush: bool = True) -> None:
        """Closes the provider.

        Pending writing tasks queued after this will fail, so such tasks should be
        awaited before this. Write tasks queued before this may succeed, however.

        :param flush: Whether to flush buffered data before closing. If false, all
            buffered data will be lost. Default is False.
        """
        if self._closed:
            return

        # Acquire a lock on the data buffer, releasing it automatically when the
        # block exits. Notably this will not wait on a condition to move forward.
        async with self._data_condition:
            self._closing = True
            if flush:
                # Release the lock until the buffer is empty.
                await self._data_condition.wait_for(lambda: len(self._data) == 0)
            else:
                # Clear out any pending data, freeing up memory.
                self._data.clear()

            self._closed = True
            self._closing = False

            # Notify all waiting coroutines that the provider has closed.
            self._data_condition.notify_all()

    def __aiter__(self) -> Self:
        return self

    async def __anext__(self) -> bytes:
        # Acquire a lock on the data buffer, releasing it automatically when the
        # block exits.
        async with self._data_condition:
            # Wait for the stream to be closed or for the data buffer to be non-empty.
            # This also releases the lock until that condition is met.
            await self._data_condition.wait_for(
                lambda: self._closed or len(self._data) > 0
            )

            # If the provider is closed, end the iteration.
            if self._closed:
                raise StopAsyncIteration

            # Pop the next chunk of data from the buffer, then notify any waiting
            # coroutines, returning immediately after.
            result = self._data.popleft()
            self._data_condition.notify()
            return result

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        await self.close(flush=True)
