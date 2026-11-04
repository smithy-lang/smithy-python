#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""Payload checksums for operations with the ``aws.protocols#httpChecksum`` trait."""

import logging
from dataclasses import dataclass

from smithy_core.aio.interfaces import StreamingBlob
from smithy_core.aio.types import AsyncBytesReader
from smithy_core.exceptions import CallError, Fault

from ._private.checksums import create_checksum, decode_checksum, encode_digest
from .config.types import ResponseChecksumValidation

__all__ = [
    "ChecksumMismatchError",
    "ChecksumValidatingStream",
    "ResponseChecksumValidation",
]

logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class ChecksumMismatchError(CallError):
    """The checksum of a payload didn't match the checksum sent with it."""

    algorithm: str
    """The checksum algorithm, such as ``CRC32``."""

    expected: str
    """The base64-encoded checksum sent with the payload."""

    actual: str
    """The base64-encoded checksum of the payload that was received."""

    fault: Fault = "server"
    is_retry_safe: bool | None = False


class ChecksumValidatingStream(AsyncBytesReader):
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
        self, source: StreamingBlob, *, checksum_algorithm: str, expected: str
    ) -> None:
        """Initialize the stream.

        :param source: The response payload.
        :param checksum_algorithm: The algorithm of the expected checksum.
        :param expected: The base64-encoded checksum sent with the payload.
        :raises ValueError: If the algorithm isn't supported, or if ``expected`` is
            empty or isn't valid base64.
        """
        super().__init__(source)
        self._seekable = False
        self._checksum = create_checksum(checksum_algorithm)
        expected_digest = decode_checksum(expected)
        if expected_digest is None:
            raise ValueError(f"Invalid {checksum_algorithm} checksum: {expected!r}")
        self._expected = expected_digest
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
            expected, received = encode_digest(self._expected), encode_digest(actual)
            raise ChecksumMismatchError(
                f"Expected a {self.checksum_algorithm} checksum of {expected}, but "
                f"the response payload's checksum was {received}.",
                algorithm=self.checksum_algorithm,
                expected=expected,
                actual=received,
            )
        self._validated = True
        logger.debug(
            "Validated the response payload's %s checksum", self.checksum_algorithm
        )
