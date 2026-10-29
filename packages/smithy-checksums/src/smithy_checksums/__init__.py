#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""Checksum algorithms for Smithy clients.

CRC32 and CRC32C use a native extension when one is available for the platform
and fall back to pure Python otherwise. The fallback produces identical results
but is orders of magnitude slower, except for CRC32, which uses :mod:`zlib`. SHA-1, SHA-256, SHA-512, and MD5 are available
through :func:`new` and always use :mod:`hashlib`.
"""

import hashlib
from collections.abc import Buffer
from importlib.metadata import version
from typing import ClassVar, Final, Protocol, Self, runtime_checkable

from ._private.buffers import as_byte_view as _as_byte_view
from ._private.selection import IMPLEMENTATIONS as _IMPLEMENTATIONS
from ._private.selection import NATIVE as _NATIVE
from ._private.selection import ChecksumImpl as _ChecksumImpl

__version__ = version("smithy-checksums")
__all__ = (
    "CRC32",
    "CRC32C",
    "HAS_NATIVE_EXTENSION",
    "Checksum",
    "new",
)

HAS_NATIVE_EXTENSION: Final[bool] = _NATIVE
"""Whether the native extension is in use.

When it isn't, CRC32C is computed in pure Python.
"""


@runtime_checkable
class Checksum(Protocol):
    """A streaming checksum.

    Objects returned by :mod:`hashlib` also satisfy this protocol.
    """

    @property
    def name(self) -> str:
        """The lowercase name of the algorithm, such as ``crc32c``."""
        ...

    @property
    def digest_size(self) -> int:
        """The size of the digest in bytes."""
        ...

    def update(self, data: Buffer, /) -> None:
        """Feeds bytes to the checksum.

        :param data: The bytes to add. Buffers that aren't C-contiguous are rejected.
        """
        ...

    def digest(self) -> bytes:
        """Returns the checksum of the data passed to :meth:`update` so far.

        The digest is big-endian, the byte order used by checksum headers such as
        ``x-amz-checksum-crc32c``. Calling this doesn't reset the checksum.
        """
        ...

    def copy(self) -> Self:
        """Returns an independent copy of the checksum's current state."""
        ...


class _BaseChecksum:
    __slots__ = ("_impl",)

    name: ClassVar[str]
    digest_size: ClassVar[int]

    _impl: _ChecksumImpl

    def __init__(self) -> None:
        self._impl = _IMPLEMENTATIONS[self.name]()

    def update(self, data: Buffer, /) -> None:
        """Feeds bytes to the checksum.

        :param data: The bytes to add. Buffers that aren't C-contiguous are rejected.
        """
        self._impl.update(_as_byte_view(data))

    def digest(self) -> bytes:
        """Returns the big-endian checksum of the data passed to :meth:`update` so far.

        Calling this doesn't reset the checksum.
        """
        return self._impl.digest()

    def copy(self) -> Self:
        """Returns an independent copy of the checksum's current state."""
        new = object.__new__(type(self))
        new._impl = self._impl.copy()
        return new


class CRC32(_BaseChecksum):
    """CRC-32 (ISO-HDLC), the variant used by zlib and gzip."""

    __slots__ = ()

    name = "crc32"
    digest_size = 4


class CRC32C(_BaseChecksum):
    """CRC-32C (Castagnoli)."""

    __slots__ = ()

    name = "crc32c"
    digest_size = 4


_CHECKSUMS: Final = {cls.name: cls for cls in (CRC32, CRC32C)}
_HASHLIB_ALGORITHMS: Final = frozenset(("sha1", "sha256", "sha512"))


def new(name: str) -> Checksum:
    """Creates a checksum from the name of its algorithm.

    Names are case-insensitive, so the values of a checksum algorithm enum such as
    ``CRC32C`` or ``SHA256`` can be passed directly.

    :param name: One of ``crc32``, ``crc32c``, ``sha1``, ``sha256``, ``sha512``, or
        ``md5``.
    :raises ValueError: If the algorithm isn't supported.
    """
    key = name.lower()
    if (checksum := _CHECKSUMS.get(key)) is not None:
        return checksum()
    if key in _HASHLIB_ALGORITHMS:
        return hashlib.new(key)
    if key == "md5":
        return hashlib.md5(usedforsecurity=False)
    raise ValueError(f"Unsupported checksum algorithm: {name!r}")
