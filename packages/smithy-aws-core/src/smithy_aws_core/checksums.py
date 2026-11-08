#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""Payload checksums for operations with the ``aws.protocols#httpChecksum`` trait.

Sync clients validate response payloads with :py:class:`ChecksumStream`, and async
clients with :py:class:`smithy_aws_core.aio.checksums.AsyncChecksumStream`.
"""

from collections.abc import Iterator
from dataclasses import dataclass
from io import BytesIO

from smithy_core.exceptions import CallError, Fault, SmithyError
from smithy_core.interfaces import BytesReader

from ._private.checksums import ChecksumValidator, encode_digest
from .config.types import RequestChecksumCalculation, ResponseChecksumValidation

__all__ = [
    "ChecksumMismatchError",
    "ChecksumStream",
    "RequestChecksumCalculation",
    "ResponseChecksumValidation",
    "UnsupportedChecksumAlgorithmError",
]

_DEFAULT_CHUNK_SIZE = 1024


@dataclass(kw_only=True)
class ChecksumMismatchError(CallError):
    """The checksum of a payload didn't match the checksum sent with it."""

    algorithm: str
    """The checksum algorithm, such as ``CRC32``."""

    expected: bytes
    """The checksum sent with the payload."""

    actual: bytes
    """The checksum of the payload that was received."""

    fault: Fault = "server"
    is_retry_safe: bool | None = False

    def __post_init__(self) -> None:
        if not self.message:
            self.message = (
                f"Expected a {self.algorithm} checksum of "
                f"{encode_digest(self.expected)}, but the payload's checksum was "
                f"{encode_digest(self.actual)}."
            )
        super().__post_init__()


class UnsupportedChecksumAlgorithmError(SmithyError):
    """The checksum algorithm chosen for a request isn't supported.

    To use an algorithm the SDK can't calculate, such as MD5, calculate the checksum
    and set it on the request instead.
    """

    def __init__(self, algorithm: str) -> None:
        super().__init__(
            f"Unsupported checksum algorithm: {algorithm!r}. To use it, calculate "
            "the checksum and set it on the request."
        )
        self.algorithm = algorithm
        """The algorithm that was chosen."""


class ChecksumStream:
    """A response payload that validates its checksum once it's read to the end.

    The checksum is calculated as the payload is read. Validation happens when the
    stream is read to the end: when ``read()`` is called without a size, when a
    sized ``read()`` returns no data, or when iteration finishes. A mismatch raises
    ``ChecksumMismatchError`` from that read, after the earlier data was returned. A
    payload that isn't read to the end isn't validated.

    The stream can't be seeked, since that would invalidate the checksum.
    """

    def __init__(
        self,
        source: BytesReader | bytes | bytearray,
        *,
        checksum_algorithm: str,
        expected: bytes,
    ) -> None:
        """Initialize the stream.

        :param source: The response payload.
        :param checksum_algorithm: The algorithm of the expected checksum.
        :param expected: The checksum the payload must match.
        :raises ValueError: If the algorithm isn't supported.
        """
        self._source: BytesReader | None = (
            BytesIO(source) if isinstance(source, bytes | bytearray) else source
        )
        self._validator = ChecksumValidator(checksum_algorithm, expected)

    def __iter__(self) -> Iterator[bytes]:
        return self.iter_chunks()

    @property
    def checksum_algorithm(self) -> str:
        """The algorithm used to validate the payload, such as ``CRC32``."""
        return self._validator.checksum_algorithm

    @property
    def validated(self) -> bool:
        """Whether the payload was read to the end and its checksum matched."""
        return self._validator.validated

    @property
    def closed(self) -> bool:
        """Whether the stream is closed."""
        return self._source is None

    def read(self, size: int = -1) -> bytes:
        """Read up to ``size`` bytes, or the rest of the payload if it's negative.

        :raises ChecksumMismatchError: If the payload was read to the end and its
            checksum doesn't match.
        """
        if self._source is None:
            raise ValueError("I/O operation on closed file.")
        data = self._source.read(size)
        self._validator.observe(data, size)
        return data

    def iter_chunks(self, chunk_size: int = _DEFAULT_CHUNK_SIZE) -> Iterator[bytes]:
        """Iterate over the payload in chunks of up to ``chunk_size`` bytes."""
        while data := self.read(chunk_size):
            yield data

    def readable(self) -> bool:
        """Whether the stream is readable."""
        return True

    def writeable(self) -> bool:
        """Whether the stream is writeable."""
        return False

    def seekable(self) -> bool:
        """Whether the stream is seekable, which it never is."""
        return False

    def seek(self, offset: int, whence: int = 0) -> int:
        """Seeking isn't supported, since it would invalidate the checksum."""
        raise NotImplementedError

    def close(self) -> None:
        """Close the stream and its source."""
        if self._source is not None and (close := getattr(self._source, "close", None)):
            close()
        self._source = None
