#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""Checksum algorithms used for operations with the ``httpChecksum`` trait.

Algorithm names are the values of the ``ChecksumAlgorithm`` enum that services
model, such as ``CRC32`` or ``SHA256``, and are compared case-insensitively.
"""

import base64
import binascii
import logging
from collections.abc import Iterable
from typing import TYPE_CHECKING, Final

from smithy_core.exceptions import MissingDependencyError

logger = logging.getLogger(__name__)

try:
    import smithy_aws_checksums

    _HAS_CHECKSUMS = True
except ImportError:
    _HAS_CHECKSUMS = False  # type: ignore

if TYPE_CHECKING:
    import smithy_aws_checksums
    from smithy_aws_checksums import Checksum

_RESPONSE_VALIDATION_ORDER: Final = (
    "CRC32C",
    "CRC32",
    "CRC64NVME",
    "XXHASH64",
    "XXHASH3",
    "XXHASH128",
    "SHA1",
    "SHA256",
    "SHA512",
)
"""The supported algorithms, from the fastest to the slowest to calculate."""

SUPPORTED_ALGORITHMS: Final = frozenset(_RESPONSE_VALIDATION_ORDER)
"""The algorithms the SDK can calculate a checksum with.

MD5 isn't included: it may only be sent as a checksum the caller calculated.
"""

DEFAULT_ALGORITHM: Final = "CRC64NVME"
"""The algorithm used for request checksums when the caller doesn't choose one."""

_CHECKSUM_HEADER_PREFIX: Final = "x-amz-checksum-"

# Headers that share the checksum prefix but don't carry a checksum.
_NON_CHECKSUM_HEADERS: Final = frozenset(
    ("x-amz-checksum-type", "x-amz-checksum-mode", "x-amz-checksum-algorithm")
)


def assert_checksums_installed() -> None:
    """Raise if smithy-aws-checksums, which calculates checksums, isn't installed.

    :raises MissingDependencyError: If smithy-aws-checksums isn't installed.
    """
    if not _HAS_CHECKSUMS:
        raise MissingDependencyError(
            "Attempted to use checksums, but smithy-aws-checksums is not installed. "
            "Install smithy-aws-core[checksums]."
        )


def create_checksum(algorithm: str) -> "Checksum":
    """Create a checksum for a supported algorithm.

    :param algorithm: The name of the algorithm.
    :raises ValueError: If the algorithm isn't in ``SUPPORTED_ALGORITHMS``.
    :raises MissingDependencyError: If smithy-aws-checksums isn't installed.
    """
    if algorithm.upper() not in SUPPORTED_ALGORITHMS:
        raise ValueError(f"Unsupported checksum algorithm: {algorithm!r}")
    assert_checksums_installed()
    return smithy_aws_checksums.new(algorithm)


def checksum_header(algorithm: str) -> str:
    """The name of the header or trailer that carries a checksum of the algorithm.

    :param algorithm: The name of the algorithm.
    """
    return _CHECKSUM_HEADER_PREFIX + algorithm.lower()


def checksum_header_algorithm(name: str) -> str | None:
    """The algorithm of a header that carries a checksum, if it is one.

    Headers are matched by prefix, so that checksums of algorithms the SDK doesn't
    know yet are recognized too.

    :param name: The header name, in any case.
    :returns: The uppercase algorithm name, such as ``CRC32``, or None.
    """
    name = name.lower()
    if not name.startswith(_CHECKSUM_HEADER_PREFIX) or name in _NON_CHECKSUM_HEADERS:
        return None
    return name.removeprefix(_CHECKSUM_HEADER_PREFIX).upper()


def encode_digest(digest: bytes) -> str:
    """Encode a checksum digest the way it's sent in headers and trailers."""
    return base64.b64encode(digest).decode("ascii")


def decode_checksum(value: str) -> bytes | None:
    """Decode a checksum sent in a header or trailer.

    :param value: The base64-encoded checksum.
    :returns: The digest, or None if the value is empty or isn't valid base64, so it
        can't be validated. That includes repeated headers joined with commas, and
        composite checksums of multipart objects, which end in
        ``-<number of parts>``. A valid value of the wrong size is returned, so that
        validating it fails.
    """
    try:
        return base64.b64decode(value, validate=True) or None
    except binascii.Error:
        return None


def response_validation_order(algorithms: Iterable[str]) -> tuple[str, ...]:
    """Order the supported algorithms of a response, fastest to calculate first.

    :param algorithms: The algorithms modeled for the response. Unsupported ones,
        such as MD5, are left out.
    """
    modeled = {algorithm.upper() for algorithm in algorithms}
    return tuple(a for a in _RESPONSE_VALIDATION_ORDER if a in modeled)


class ChecksumValidator:
    """Calculates a payload's checksum as it's read and checks it at the end."""

    def __init__(self, checksum_algorithm: str, expected: bytes) -> None:
        """Initialize the validator.

        :param checksum_algorithm: The algorithm of the expected checksum.
        :param expected: The checksum the payload must match.
        :raises ValueError: If the algorithm isn't supported.
        """
        self.checksum_algorithm = checksum_algorithm
        self._checksum = create_checksum(checksum_algorithm)
        self._expected = expected
        self.validated = False

    def observe(self, data: bytes, size: int) -> None:
        """Record the result of ``read(size)``, validating at the end of the payload.

        :raises ChecksumMismatchError: If the payload ended and its checksum doesn't
            match.
        """
        if size == 0:
            return
        if data:
            self._checksum.update(data)
        if size < 0 or not data:
            self._validate()

    def _validate(self) -> None:
        if self.validated:
            return
        actual = self._checksum.digest()
        if actual != self._expected:
            # CAUTION: a module-level import is circular; ..checksums imports this one.
            from ..checksums import ChecksumMismatchError

            raise ChecksumMismatchError(
                algorithm=self.checksum_algorithm,
                expected=self._expected,
                actual=actual,
            )
        self.validated = True
        logger.debug(
            "Validated the response payload's %s checksum", self.checksum_algorithm
        )
