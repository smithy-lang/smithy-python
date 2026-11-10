#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""Asynchronous ``aws-chunked`` encoding of request payloads.

See :py:mod:`smithy_aws_core._aws_chunked` for the encoding.
"""

from collections.abc import AsyncIterator, Callable
from typing import Any

from smithy_core.aio.types import AsyncBytesReader

from .._aws_chunked import CHUNK_SIZE, AwsChunkedEncoder


class AsyncAwsChunkedReader:
    """Encodes an asynchronous payload as it's read.

    :param source: The payload, as bytes or a synchronous or asynchronous stream.
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
        self._source = AsyncBytesReader(source)
        self._encoder = AwsChunkedEncoder(
            decoded_length=decoded_length,
            checksum_algorithm=checksum_algorithm,
            checksum=checksum,
            on_checksum=on_checksum,
            chunk_size=chunk_size,
        )

    async def __aiter__(self) -> AsyncIterator[bytes]:
        while data := await self.read(self._encoder.chunk_size):
            yield data

    async def read(self, size: int = -1) -> bytes:
        """Read up to ``size`` encoded bytes, or the rest if it's negative."""
        while not self._encoder.done and (
            size < 0 or len(self._encoder.encoded) < size
        ):
            if read_size := self._encoder.read_size:
                self._encoder.write(await self._source.read(read_size))
            else:
                self._encoder.finish()
        return self._encoder.take(size)

    async def close(self) -> None:
        """Close the reader, leaving the payload open.

        The caller owns the payload, and a retry rewinds it to send it again.
        """
