#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""Selects the native checksum implementations, or the pure-Python ones if unavailable."""

from collections.abc import Callable, Mapping
from typing import Protocol, Self


class ChecksumImpl(Protocol):
    """The interface shared by the native and pure-Python implementations.

    Callers normalize input with :func:`.buffers.as_byte_view` first.
    """

    def update(self, data: bytes | bytearray | memoryview, /) -> None: ...

    def digest(self) -> bytes: ...

    def copy(self) -> Self: ...


type ImplFactory = Callable[[], ChecksumImpl]


def _load() -> tuple[bool, Mapping[str, ImplFactory]]:
    try:
        from smithy_checksums import _native
    except ImportError:
        from smithy_checksums._private import crc, xxhash

        return False, {
            "crc32": crc.Crc32,
            "crc32c": crc.Crc32C,
            "crc64nvme": crc.Crc64Nvme,
            "xxhash64": xxhash.XxHash64,
            "xxhash3": xxhash.XxHash3,
            "xxhash128": xxhash.XxHash128,
        }

    return True, {
        "crc32": _native.Crc32,
        "crc32c": _native.Crc32C,
        "crc64nvme": _native.Crc64Nvme,
        "xxhash64": _native.XxHash64,
        "xxhash3": _native.XxHash3,
        "xxhash128": _native.XxHash128,
    }


NATIVE, IMPLEMENTATIONS = _load()
