#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""Payload checksums for operations with the ``aws.protocols#httpChecksum`` trait.

The stream that validates response payloads is
:py:class:`smithy_aws_core.aio.checksums.AsyncChecksumStream`.
"""

from dataclasses import dataclass

from smithy_core.exceptions import CallError, Fault, SmithyError

from ._private.checksums import encode_digest
from .config.types import RequestChecksumCalculation, ResponseChecksumValidation

__all__ = [
    "ChecksumMismatchError",
    "RequestChecksumCalculation",
    "ResponseChecksumValidation",
    "UnsupportedChecksumAlgorithmError",
]


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
