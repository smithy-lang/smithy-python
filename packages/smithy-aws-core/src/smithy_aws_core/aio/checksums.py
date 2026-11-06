#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""Async streams for payload checksums."""

import logging

from smithy_core.aio.interfaces import StreamingBlob
from smithy_core.aio.types import AsyncBytesReader

from .._private.checksums import create_checksum
from ..checksums import ChecksumMismatchError

__all__ = ["AsyncChecksumStream"]

logger = logging.getLogger(__name__)


class AsyncChecksumStream(AsyncBytesReader):
    """A response payload that validates its checksum once it's read to the end.

    The checksum is calculated as the payload is read. Validation happens when the
    stream is read to the end: when ``read()`` is called without a size, when a
    sized ``read()`` returns no data, or when iteration finishes. A mismatch raises
    ``ChecksumMismatchError`` from that read, after the earlier data was returned. A
    payload that isn't read to the end isn't validated.

    The stream can't be seeked, since that would invalidate the checksum.
    """

    checksum_algorithm: str
    """The algorithm used to validate the payload, such as ``CRC32``."""

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
        self._checksum = create_checksum(checksum_algorithm)
        self._expected = expected
        self._validated = False
        self.checksum_algorithm = checksum_algorithm

    @property
    def validated(self) -> bool:
        """Whether the payload was read to the end and its checksum matched."""
        return self._validated

    async def read(self, size: int = -1) -> bytes:
        """Read up to ``size`` bytes, or the rest of the payload if it's negative.

        :raises ChecksumMismatchError: If the payload was read to the end and its
            checksum doesn't match.
        """
        data = await super().read(size)
        if size == 0:
            return data
        if data:
            self._checksum.update(data)
        if size < 0 or not data:
            self._validate()
        return data

    def _validate(self) -> None:
        if self._validated:
            return
        actual = self._checksum.digest()
        if actual != self._expected:
            raise ChecksumMismatchError(
                algorithm=self.checksum_algorithm,
                expected=self._expected,
                actual=actual,
            )
        self._validated = True
        logger.debug(
            "Validated the response payload's %s checksum", self.checksum_algorithm
        )
