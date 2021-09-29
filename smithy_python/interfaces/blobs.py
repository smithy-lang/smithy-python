from typing import Union, Protocol, runtime_checkable


@runtime_checkable
class ByteStream(Protocol):
    """A file-like object with a read method that returns bytes."""

    def read(self, size: int = -1) -> bytes:
        pass


@runtime_checkable
class SeekableByteStream(ByteStream, Protocol):
    """A file-like object with read, seek, and tell methods."""

    def seek(self, offset: int, whence: int = 0) -> int:
        pass

    def tell(self) -> int:
        pass


@runtime_checkable
class AsyncByteStream(Protocol):
    """A file-like object with an async read method."""

    async def read(self, size: int = -1) -> bytes:
        pass


# A union of all acceptable streaming blob types. Deserialized payloads will
# always return a ByteStream, or AsyncByteStream if async is enabled.
StreamingBlob = Union[
    ByteStream, SeekableByteStream, AsyncByteStream, bytes, bytearray,
]
