#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""Pure-Python CRC implementations, used when the native extension is unavailable."""

import zlib
from typing import ClassVar, Self

from .pure import PureChecksum


def _reflected_table(poly: int) -> tuple[int, ...]:
    table: list[int] = []
    for byte in range(256):
        crc = byte
        for _ in range(8):
            crc = (crc >> 1) ^ poly if crc & 1 else crc >> 1
        table.append(crc)
    return tuple(table)


class Crc32(PureChecksum):
    """CRC-32 (ISO-HDLC), backed by :func:`zlib.crc32`."""

    __slots__ = ("_crc",)

    def __init__(self) -> None:
        super().__init__()
        self._crc = 0

    def _update(self, data: bytes | bytearray) -> None:
        self._crc = zlib.crc32(data, self._crc)

    def _digest(self) -> bytes:
        return self._crc.to_bytes(4, "big")

    def _copy(self) -> Self:
        new = type(self)()
        new._crc = self._crc
        return new


class _ReflectedCrc(PureChecksum):
    """A table-driven CRC whose initial value and final XOR are all ones."""

    __slots__ = ("_crc",)

    _table: ClassVar[tuple[int, ...]]
    _mask: ClassVar[int]
    _size: ClassVar[int]

    def __init__(self) -> None:
        super().__init__()
        self._crc = self._mask

    def _update(self, data: bytes | bytearray) -> None:
        table = self._table
        crc = self._crc
        for byte in data:
            crc = table[(crc ^ byte) & 0xFF] ^ (crc >> 8)
        self._crc = crc

    def _digest(self) -> bytes:
        return (self._crc ^ self._mask).to_bytes(self._size, "big")

    def _copy(self) -> Self:
        new = type(self)()
        new._crc = self._crc
        return new


class Crc32C(_ReflectedCrc):
    """CRC-32C (Castagnoli, also called iSCSI)."""

    __slots__ = ()

    _table = _reflected_table(0x82F63B78)
    _mask = 0xFFFFFFFF
    _size = 4
