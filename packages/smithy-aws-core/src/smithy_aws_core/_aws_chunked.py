#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""``aws-chunked`` encoding of request payloads with a trailing checksum.

The payload is sent as a series of chunks, each its length in hex, CRLF, the data,
and CRLF. A zero-length chunk ends the payload, followed by the checksum trailer and
a final CRLF::

    10000\\r\\n<65536 bytes>\\r\\n
    a\\r\\n<10 bytes>\\r\\n
    0\\r\\n
    x-amz-checksum-crc64nvme:<base64 checksum>\\r\\n
    \\r\\n

The checksum is calculated as the payload is read, so the payload is read only once.
Exactly the declared decoded length is sent. A longer payload is cut off at that
length, and a shorter one fails the request.
"""

import io
from collections.abc import Callable
from typing import Any, Final

from smithy_core.exceptions import SmithyError

from ._private.checksums import checksum_header, create_checksum, encode_digest

CHUNK_SIZE: Final = 64 * 1024
"""The size of every chunk but the last.

Chunks must be at least 8 KiB, and 64 KiB is the recommended size.
"""


class AwsChunkedEncoder:
    """Frames data into ``aws-chunked`` chunks and writes the checksum trailer."""

    def __init__(
        self,
        *,
        decoded_length: int,
        checksum_algorithm: str,
        checksum: bytes | None,
        on_checksum: Callable[[bytes], None] | None,
        chunk_size: int,
    ) -> None:
        self.chunk_size = chunk_size
        self._decoded_length = decoded_length
        self._remaining = decoded_length
        self._algorithm = checksum_algorithm
        self._checksum = checksum
        self._on_checksum = on_checksum
        self._hash = create_checksum(checksum_algorithm) if checksum is None else None
        self._buffer = bytearray()
        self.encoded = bytearray()
        self.done = False

    @property
    def read_size(self) -> int:
        """How many bytes to read from the payload next, or 0 once it's all read."""
        return min(self.chunk_size, self._remaining)

    def write(self, data: bytes | None) -> None:
        """Add data read from the payload, framing every full chunk.

        Data past the decoded length is dropped.

        :raises SmithyError: If the payload ended before the decoded length was read.
        """
        if not data:
            raise SmithyError(
                f"The request payload ended after "
                f"{self._decoded_length - self._remaining} bytes, but its content "
                f"length is {self._decoded_length}. A payload must not get shorter "
                f"after the request is made."
            )
        data = data[: self._remaining]
        self._remaining -= len(data)
        self._buffer += data
        while len(self._buffer) >= self.chunk_size:
            self._frame(self._buffer[: self.chunk_size])
            del self._buffer[: self.chunk_size]

    def finish(self) -> None:
        """Frame the rest of the payload, then write the last chunk and trailer."""
        if self._buffer:
            self._frame(self._buffer)
            self._buffer.clear()
        digest = self._checksum
        if digest is None:
            assert self._hash is not None  # noqa: S101
            digest = self._hash.digest()
            if self._on_checksum is not None:
                self._on_checksum(digest)
        # The trailer is where the digest goes on the wire, so it's encoded here.
        trailer = f"{checksum_header(self._algorithm)}:{encode_digest(digest)}"
        self.encoded += f"0\r\n{trailer}\r\n\r\n".encode()
        self.done = True

    def take(self, size: int) -> bytes:
        """Remove and return up to ``size`` encoded bytes, or all if it's negative."""
        if size < 0 or size >= len(self.encoded):
            data = bytes(self.encoded)
            self.encoded.clear()
        else:
            data = bytes(self.encoded[:size])
            del self.encoded[:size]
        return data

    def _frame(self, data: bytearray) -> None:
        if self._hash is not None:
            self._hash.update(data)
        self.encoded += f"{len(data):x}\r\n".encode()
        self.encoded += data
        self.encoded += b"\r\n"


class AwsChunkedReader(io.RawIOBase):
    """Encodes a synchronous payload as it's read.

    :param source: The payload, as bytes or a synchronous reader.
    :param decoded_length: The payload's length before it's encoded. Exactly this
        many bytes are read from it.
    :param checksum_algorithm: The algorithm of the trailing checksum.
    :param checksum: A digest to send rather than calculating one, such as on a
        retry.
    :param on_checksum: Called with the calculated digest once the payload has been
        read to the end.
    """

    def __init__(
        self,
        source: Any,
        *,
        decoded_length: int,
        checksum_algorithm: str,
        checksum: bytes | None = None,
        on_checksum: Callable[[bytes], None] | None = None,
        chunk_size: int = CHUNK_SIZE,
    ) -> None:
        super().__init__()
        self._source = (
            io.BytesIO(source) if isinstance(source, bytes | bytearray) else source
        )
        self._encoder = AwsChunkedEncoder(
            decoded_length=decoded_length,
            checksum_algorithm=checksum_algorithm,
            checksum=checksum,
            on_checksum=on_checksum,
            chunk_size=chunk_size,
        )

    def readable(self) -> bool:
        return True

    def readinto(self, buffer: Any) -> int:
        view = memoryview(buffer).cast("B")
        while not self._encoder.encoded and not self._encoder.done:
            if size := self._encoder.read_size:
                self._encoder.write(self._source.read(size))
            else:
                self._encoder.finish()
        data = self._encoder.take(len(view))
        view[: len(data)] = data
        return len(data)
