#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""Pure-Python CRC implementations, used when the native extension is unavailable."""

import zlib
from functools import cache
from typing import ClassVar, Self

from .pure import PureChecksum

# Input is buffered and hashed this many bytes at a time with the masks from
# _chunk_masks. It must be a power of two.
_CHUNK_SIZE = 16384
# Remainders shorter than this are hashed a byte at a time from the table, which
# is faster than a pass over the masks.
_MIN_MASKED_TAIL = 1024


def _reflected_table(poly: int) -> tuple[int, ...]:
    table: list[int] = []
    for byte in range(256):
        crc = byte
        for _ in range(8):
            crc = (crc >> 1) ^ poly if crc & 1 else crc >> 1
        table.append(crc)
    return tuple(table)


def _apply(columns: list[int], value: int) -> int:
    """Multiplies the GF(2) matrix with the given columns by ``value``."""
    result = 0
    for column in columns:
        if value & 1:
            result ^= column
        value >>= 1
    return result


@cache
def _chunk_masks(table: tuple[int, ...], width: int) -> tuple[int, ...]:
    """Returns masks that compute a CRC over a chunk with big-integer operations.

    Without its initial value and final XOR, a CRC is linear over GF(2), so each
    bit of the CRC of a message is the parity of a fixed subset of the message's
    bits. Bit ``r`` of the CRC of a ``_CHUNK_SIZE``-byte chunk, read as a
    little-endian integer ``m``, is the parity of ``m & masks[r]``. This does the
    per-byte work in C, which is many times faster than a table lookup per byte.

    The masks are built for one byte and then doubled: the CRC of ``a + b`` is the
    CRC of ``a`` shifted through ``len(b)`` zero bytes, XORed with the CRC of
    ``b``. The shift is linear too, and ``columns[s]`` holds its effect on bit
    ``s`` of the CRC.
    """
    masks = [0] * width
    for bit in range(8):
        for row in range(width):
            if (table[1 << bit] >> row) & 1:
                masks[row] |= 1 << bit
    columns = [(table[(1 << s) & 0xFF] ^ ((1 << s) >> 8)) for s in range(width)]
    length = 1
    while length < _CHUNK_SIZE:
        shifted = [0] * width
        for s, column in enumerate(columns):
            for row in range(width):
                if (column >> row) & 1:
                    shifted[row] ^= masks[s]
        masks = [low | (high << (8 * length)) for low, high in zip(shifted, masks)]
        columns = [_apply(columns, column) for column in columns]
        length *= 2
    return tuple(masks)


class Crc32(PureChecksum):
    """CRC-32 (ISO-HDLC), backed by :func:`zlib.crc32`."""

    __slots__ = ("_crc",)

    def __init__(self) -> None:
        super().__init__()
        self._crc = 0

    def _update(self, data: bytes | bytearray | memoryview) -> None:
        self._crc = zlib.crc32(data, self._crc)

    def _digest(self) -> bytes:
        return self._crc.to_bytes(4, "big")

    def _copy(self) -> Self:
        new = type(self)()
        new._crc = self._crc
        return new


class _ReflectedCrc(PureChecksum):
    """A table-driven CRC whose initial value and final XOR are all ones.

    Whole chunks are hashed with the masks from :func:`_chunk_masks`. Up to a
    chunk of input is buffered, so that the speed doesn't depend on how the input
    is split between updates.
    """

    __slots__ = ("_buffer", "_crc")

    _table: ClassVar[tuple[int, ...]]
    _mask: ClassVar[int]
    _size: ClassVar[int]

    def __init__(self) -> None:
        super().__init__()
        self._crc = self._mask
        self._buffer = bytearray()

    def _update(self, data: bytes | bytearray | memoryview) -> None:
        buffer = self._buffer
        view = memoryview(data)
        if buffer:
            needed = _CHUNK_SIZE - len(buffer)
            buffer += view[:needed]
            if len(buffer) < _CHUNK_SIZE:
                return
            self._crc = self._hash_chunk(self._crc, buffer)
            buffer.clear()
            view = view[needed:]
        end = len(view) - len(view) % _CHUNK_SIZE
        crc = self._crc
        for offset in range(0, end, _CHUNK_SIZE):
            crc = self._hash_chunk(crc, view[offset : offset + _CHUNK_SIZE])
        self._crc = crc
        buffer += view[end:]

    def _hash_chunk(self, crc: int, chunk: bytes | bytearray | memoryview) -> int:
        """Returns the CRC after ``chunk``, which may be shorter than a chunk.

        A reflected CRC's state can be XORed into the next bytes of input and
        cleared instead, and leading zero bytes don't change a CRC of zero. A short
        chunk must still be at least as long as the CRC.
        """
        message = (int.from_bytes(chunk, "little") ^ crc) << (
            8 * (_CHUNK_SIZE - len(chunk))
        )
        result = 0
        for row, mask in enumerate(_chunk_masks(self._table, 8 * self._size)):
            result |= ((message & mask).bit_count() & 1) << row
        return result

    def _digest(self) -> bytes:
        crc = self._crc
        tail = self._buffer
        if len(tail) >= _MIN_MASKED_TAIL:
            crc = self._hash_chunk(crc, tail)
        else:
            table = self._table
            for byte in tail:
                crc = table[(crc ^ byte) & 0xFF] ^ (crc >> 8)
        return (crc ^ self._mask).to_bytes(self._size, "big")

    def _copy(self) -> Self:
        new = type(self)()
        new._crc = self._crc
        new._buffer = self._buffer.copy()
        return new


class Crc32C(_ReflectedCrc):
    """CRC-32C (Castagnoli, also called iSCSI)."""

    __slots__ = ()

    _table = _reflected_table(0x82F63B78)
    _mask = 0xFFFFFFFF
    _size = 4


class Crc64Nvme(_ReflectedCrc):
    """CRC-64/NVME."""

    __slots__ = ()

    _table = _reflected_table(0x9A6C9329AC4BC9B5)
    _mask = 0xFFFFFFFFFFFFFFFF
    _size = 8
