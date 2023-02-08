from asyncio import iscoroutinefunction
from io import BytesIO
from typing import (
    AsyncIterator,
    Awaitable,
    Callable,
    Protocol,
    Self,
    Union,
    cast,
    runtime_checkable,
)

# The default chunk size for iterating streams.
_DEFAULT_CHUNK_SIZE = 1024


@runtime_checkable
class ByteStream(Protocol):
    """A file-like object with a read method that returns bytes."""

    def read(self, size: int = -1) -> bytes:
        pass


@runtime_checkable
class AsyncByteStream(Protocol):
    """A file-like object with an async read method."""

    async def read(self, size: int = -1) -> bytes:
        pass


# A union of all acceptable streaming blob types. Deserialized payloads will
# always return a ByteStream, or AsyncByteStream if async is enabled.
StreamingBlob = Union[
    ByteStream,
    AsyncByteStream,
    bytes,
    bytearray,
    AsyncIterator[bytes],
]


# asyncio has a StreamReader class which you might think would be appropriate here,
# but it is unfortunately tied to the asyncio http interfaces.
class AsyncBytesReader:

    # BytesIO *is* a ByteStream, but mypy will nevertheless complain if it isn't here.
    _data: ByteStream | AsyncByteStream | AsyncIterator[bytes] | BytesIO | None
    _closed = False

    def __init__(self, data: StreamingBlob):
        """A file-like object with an async read method.

        Data is read from the source on an as-needed basis and is not buffered.

        :param data: The source data to read from.
        """
        self._remainder = b""
        if isinstance(data, bytes | bytearray):
            self._data = BytesIO(data)
        else:
            self._data = data

    async def read(self, size: int = -1) -> bytes:
        """Read a number of bytes from the stream.

        :param size: The maximum number of bytes to read. If less than 0, all bytes
        will be read.
        """
        if self._closed or not self._data:
            raise ValueError("I/O operation on closed file.")

        if isinstance(self._data, ByteStream) and not iscoroutinefunction(
            self._data.read
        ):
            # Python's runtime_checkable can't actually tell the difference between
            # sync and async, so we have to check ourselves.
            return self._data.read(size)
        elif isinstance(self._data, AsyncByteStream):
            return await self._data.read(size)
        else:
            return await self._read_from_iterator(
                cast(AsyncIterator[bytes], self._data), size
            )

    async def _read_from_iterator(
        self, iterator: AsyncIterator[bytes], size: int
    ) -> bytes:
        # This takes the iterator as an arg here just to avoid mypy complaints, since
        # we know it's an iterator where this is called.
        result = self._remainder
        if size < 0:
            async for element in iterator:
                result += element
            self._remainder = b""
            return result

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

    def close(self) -> None:
        """Closes the stream, as well as the underlying stream where possible."""
        if (close := getattr(self._data, "close", None)) is not None:
            close()
        self._data = None
        self._closed = True


class SeekableAsyncBytesReader:
    def __init__(self, data: StreamingBlob):
        """A file-like object with async read and seek methods.

        Data is read from the source on an as-needed basis and buffered internally so
        that it can be rewound safely.

        :param data: The source data to read from.
        """
        if isinstance(data, bytes | bytearray):
            self._buffer = BytesIO(data)
            self._data_source = None
        elif isinstance(data, AsyncByteStream) and iscoroutinefunction(data.read):
            # Note that we need that iscoroutine check because python won't actually check
            # whether or not the read function is async.
            self._buffer = BytesIO()
            self._data_source = data
        else:
            self._buffer = BytesIO()
            self._data_source = AsyncBytesReader(data)

    async def read(self, size: int = -1) -> bytes:
        """Read a number of bytes from the stream.

        :param size: The maximum number of bytes to read. If less than 0, all bytes
        will be read.
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

    def close(self) -> None:
        """Closes the stream, as well as the underlying stream where possible."""
        if (close := getattr(self._data_source, "close", None)) is not None:
            close()
        self._data_source = None
        self._buffer.close()


class _AsyncByteStreamIterator:
    def __init__(self, read: Callable[[int], Awaitable[bytes]], chunk_size: int):
        self._read = read
        self._chunk_size = chunk_size

    def __aiter__(self) -> Self:
        return self

    async def __anext__(self) -> bytes:
        data = await self._read(self._chunk_size)
        if data:
            return data
        raise StopAsyncIteration
