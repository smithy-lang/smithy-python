#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""Async streams for payload checksums."""

from smithy_core.aio.interfaces import StreamingBlob
from smithy_core.aio.types import AsyncBytesReader

from .._private.checksums import ChecksumValidator

__all__ = ["AsyncChecksumStream"]


class AsyncChecksumStream(AsyncBytesReader):
    """An async response payload that validates its checksum once it's read to the end.

    See :py:class:`smithy_aws_core.checksums.ChecksumStream` for when it validates.
    """

    def __init__(
        self, source: StreamingBlob, *, checksum_algorithm: str, expected: bytes
    ) -> None:
        """Initialize the stream.

        :param source: The response payload.
        :param checksum_algorithm: The algorithm of the expected checksum.
        :param expected: The checksum the payload must match.
        :raises ValueError: If the algorithm isn't supported.
        """
        super().__init__(source)
        self._seekable = False
        self._validator = ChecksumValidator(checksum_algorithm, expected)

    @property
    def checksum_algorithm(self) -> str:
        """The algorithm used to validate the payload, such as ``CRC32``."""
        return self._validator.checksum_algorithm

    @property
    def validated(self) -> bool:
        """Whether the payload was read to the end and its checksum matched."""
        return self._validator.validated

    async def read(self, size: int = -1) -> bytes:
        """Read up to ``size`` bytes, or the rest of the payload if it's negative.

        :raises ChecksumMismatchError: If the payload was read to the end and its
            checksum doesn't match.
        """
        data = await super().read(size)
        self._validator.observe(data, size)
        return data
