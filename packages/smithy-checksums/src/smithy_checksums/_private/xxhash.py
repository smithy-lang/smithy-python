#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
#
#  Ported from xxHash (https://github.com/Cyan4973/xxHash), Copyright (C) 2012-2023
#  Yann Collet, under the BSD 2-Clause License. See LICENSE-THIRD-PARTY.
"""Pure-Python XXH64, XXH3-64, and XXH3-128, used when the native extension is unavailable.

These follow the reference implementation (https://github.com/Cyan4973/xxHash) with
a seed of zero and the default secret, which is all that checksums need.
"""

from collections.abc import Buffer
from struct import Struct
from typing import Self

from .pure import PureChecksum

_MASK64 = 0xFFFFFFFFFFFFFFFF

_PRIME32_1 = 0x9E3779B1
_PRIME32_2 = 0x85EBCA77
_PRIME32_3 = 0xC2B2AE3D
_PRIME64_1 = 0x9E3779B185EBCA87
_PRIME64_2 = 0xC2B2AE3D27D4EB4F
_PRIME64_3 = 0x165667B19E3779F9
_PRIME64_4 = 0x85EBCA77C2B2AE63
_PRIME64_5 = 0x27D4EB2F165667C5
_PRIME_MX1 = 0x165667919E3779F9
_PRIME_MX2 = 0x9FB21C651E98DF25

_U32 = Struct("<I")
_U64 = Struct("<Q")
_U64X4 = Struct("<4Q")
_U64X8 = Struct("<8Q")
_U32X16 = Struct("<16I")


def _rotl64(value: int, bits: int) -> int:
    return ((value << bits) | (value >> (64 - bits))) & _MASK64


def _read32(data: Buffer, offset: int) -> int:
    return _U32.unpack_from(data, offset)[0]


def _read64(data: Buffer, offset: int) -> int:
    return _U64.unpack_from(data, offset)[0]


def _swap32(value: int) -> int:
    return int.from_bytes(value.to_bytes(4, "little"), "big")


def _swap64(value: int) -> int:
    return int.from_bytes(value.to_bytes(8, "little"), "big")


def _fold64(lhs: int, rhs: int) -> int:
    """Multiplies two 64-bit values and XORs the halves of the 128-bit product."""
    product = lhs * rhs
    return (product ^ (product >> 64)) & _MASK64


def _xxh64_avalanche(value: int) -> int:
    value ^= value >> 33
    value = (value * _PRIME64_2) & _MASK64
    value ^= value >> 29
    value = (value * _PRIME64_3) & _MASK64
    return value ^ (value >> 32)


def _xxh3_avalanche(value: int) -> int:
    value ^= value >> 37
    value = (value * _PRIME_MX1) & _MASK64
    return value ^ (value >> 32)


# --------------------------------------------------------------------------------------
# XXH64
# --------------------------------------------------------------------------------------


def _xxh64_round(acc: int, lane: int) -> int:
    acc = (acc + lane * _PRIME64_2) & _MASK64
    return (_rotl64(acc, 31) * _PRIME64_1) & _MASK64


# Large inputs are hashed with XXH64's four lanes in one integer, 128 bits per
# lane, so that each step of a round is one operation instead of four. A lane
# times a 64-bit prime is under 2**128, so products don't spill into the next
# lane. Spreading the input into lanes has a fixed cost, so inputs shorter than
# _MIN_SPREAD bytes are hashed a lane at a time instead.
_MIN_SPREAD = 512
_LANE_BYTES = b"\xff" * 8 + b"\0" * 8
_LANE_MASK = int.from_bytes(_LANE_BYTES * 4, "little")
# Input is spread into lanes this many bytes at a time, which bounds the memory
# the spread copies take.
_SPREAD_SIZE = 65536


def _xxh64_stripes(acc: list[int], data: memoryview) -> list[int]:
    """Returns the accumulators after hashing ``data``, a whole number of stripes."""
    if len(data) < _MIN_SPREAD:
        v1, v2, v3, v4 = acc
        for l1, l2, l3, l4 in _U64X4.iter_unpack(data):
            v1 = (v1 + l1 * _PRIME64_2) & _MASK64
            v1 = (((v1 << 31) | (v1 >> 33)) * _PRIME64_1) & _MASK64
            v2 = (v2 + l2 * _PRIME64_2) & _MASK64
            v2 = (((v2 << 31) | (v2 >> 33)) * _PRIME64_1) & _MASK64
            v3 = (v3 + l3 * _PRIME64_2) & _MASK64
            v3 = (((v3 << 31) | (v3 >> 33)) * _PRIME64_1) & _MASK64
            v4 = (v4 + l4 * _PRIME64_2) & _MASK64
            v4 = (((v4 << 31) | (v4 >> 33)) * _PRIME64_1) & _MASK64
        return [v1, v2, v3, v4]

    lanes = sum(value << (128 * lane) for lane, value in enumerate(acc))
    mask = _LANE_MASK
    prime = _PRIME64_1
    from_bytes = int.from_bytes
    for start in range(0, len(data), _SPREAD_SIZE):
        piece = data[start : start + _SPREAD_SIZE]
        spread = bytearray(2 * len(piece))
        for byte in range(8):
            spread[byte::16] = piece[byte::8]
        # Multiplying every lane of the input by the prime at once is faster than
        # doing it per stripe.
        keyed = (from_bytes(spread, "little") * _PRIME64_2) & from_bytes(
            _LANE_BYTES * (len(piece) // 8), "little"
        )
        stripes = memoryview(keyed.to_bytes(len(spread), "little"))
        for offset in range(0, len(spread), 64):
            lanes = (lanes + from_bytes(stripes[offset : offset + 64], "little")) & mask
            lanes = ((((lanes << 31) | (lanes >> 33)) & mask) * prime) & mask
    return [(lanes >> (128 * lane)) & _MASK64 for lane in range(4)]


def _xxh64_merge_round(acc: int, value: int) -> int:
    acc ^= _xxh64_round(0, value)
    return (acc * _PRIME64_1 + _PRIME64_4) & _MASK64


class XxHash64(PureChecksum):
    """XXH64 with a seed of zero."""

    __slots__ = ("_acc", "_buffer", "_length")

    def __init__(self) -> None:
        super().__init__()
        self._acc: list[int] = [
            (_PRIME64_1 + _PRIME64_2) & _MASK64,
            _PRIME64_2,
            0,
            (-_PRIME64_1) & _MASK64,
        ]
        self._buffer = b""
        self._length = 0

    def _update(self, data: bytes | bytearray | memoryview) -> None:
        data = self._buffer + data
        self._length += len(data) - len(self._buffer)
        end = len(data) // 32 * 32
        if end:
            self._acc = _xxh64_stripes(self._acc, memoryview(data)[:end])
        self._buffer = bytes(data[end:])

    def _digest(self) -> bytes:
        if self._length >= 32:
            v1, v2, v3, v4 = self._acc
            acc = (
                _rotl64(v1, 1) + _rotl64(v2, 7) + _rotl64(v3, 12) + _rotl64(v4, 18)
            ) & _MASK64
            for value in self._acc:
                acc = _xxh64_merge_round(acc, value)
        else:
            acc = _PRIME64_5
        acc = (acc + self._length) & _MASK64

        tail = self._buffer
        offset = 0
        while offset + 8 <= len(tail):
            acc ^= _xxh64_round(0, _read64(tail, offset))
            acc = (_rotl64(acc, 27) * _PRIME64_1 + _PRIME64_4) & _MASK64
            offset += 8
        if offset + 4 <= len(tail):
            acc ^= (_read32(tail, offset) * _PRIME64_1) & _MASK64
            acc = (_rotl64(acc, 23) * _PRIME64_2 + _PRIME64_3) & _MASK64
            offset += 4
        for byte in tail[offset:]:
            acc ^= (byte * _PRIME64_5) & _MASK64
            acc = (_rotl64(acc, 11) * _PRIME64_1) & _MASK64

        return _xxh64_avalanche(acc).to_bytes(8, "big")

    def _copy(self) -> Self:
        new = type(self)()
        new._acc = list(self._acc)
        new._buffer = self._buffer
        new._length = self._length
        return new


# --------------------------------------------------------------------------------------
# XXH3 (shared by the 64- and 128-bit variants)
# --------------------------------------------------------------------------------------

_SECRET = bytes.fromhex(
    "b8fe6c3923a44bbe7c01812cf721ad1cded46de9839097db7240a4a4b7b3671f"
    "cb79e64eccc0e578825ad07dccff7221b8084674f743248ee03590e6813a264c"
    "3c2852bb91c300cb88d0658b1b532ea371644897a20df94e3819ef46a9deacd8"
    "a8fa763fe39c343ff9dcbbc7c70b4f1d8a51e04bcdb45931c89f7ec9d9787364"
    "eac5ac8334d3ebc3c581a0fffa1363eb170ddd51b7f0da49d316552629d4689e"
    "2b16be587d47a1fc8ff8b8d17ad031ce45cb3a8f95160428afd7fbcabb4b407e"
)
_SECRET_SIZE = len(_SECRET)
_STRIPE_LEN = 64
_STRIPES_PER_BLOCK = (_SECRET_SIZE - _STRIPE_LEN) // 8
_MIDSIZE_MAX = 240
# Input is buffered until it's clear the long-input algorithm applies, and then
# processed in chunks of at least this many bytes.
_BUFFER_SIZE = 1024

# The secret bytes each stripe of a block is keyed with, in order, so that a
# block can be keyed with one XOR. The words after them scramble the
# accumulators at the end of a block and key the last stripe.
_BLOCK_SECRET = b"".join(
    _SECRET[stripe * 8 : stripe * 8 + _STRIPE_LEN]
    for stripe in range(_STRIPES_PER_BLOCK)
)
_BLOCK_SECRET_INT = int.from_bytes(_BLOCK_SECRET, "little")
_SCRAMBLE_SECRET = _U64X8.unpack_from(_SECRET, _SECRET_SIZE - _STRIPE_LEN)
_LAST_STRIPE_SECRET = _U64X8.unpack_from(_SECRET, _SECRET_SIZE - _STRIPE_LEN - 7)

_INITIAL_ACC: tuple[int, ...] = (
    _PRIME32_3,
    _PRIME64_1,
    _PRIME64_2,
    _PRIME64_3,
    _PRIME64_4,
    _PRIME32_2,
    _PRIME64_5,
    _PRIME32_1,
)


def _mix16(data: bytes, offset: int, secret_offset: int) -> int:
    return _fold64(
        _read64(data, offset) ^ _read64(_SECRET, secret_offset),
        _read64(data, offset + 8) ^ _read64(_SECRET, secret_offset + 8),
    )


def _accumulate_stripe(
    acc: list[int], stripe: tuple[int, ...], secret: tuple[int, ...]
) -> None:
    for lane in range(8):
        value = stripe[lane]
        keyed = value ^ secret[lane]
        acc[lane ^ 1] = (acc[lane ^ 1] + value) & _MASK64
        acc[lane] = (acc[lane] + (keyed & 0xFFFFFFFF) * (keyed >> 32)) & _MASK64


def _scramble(acc: list[int]) -> None:
    for lane in range(8):
        value = acc[lane]
        value ^= value >> 47
        value ^= _SCRAMBLE_SECRET[lane]
        acc[lane] = (value * _PRIME32_1) & _MASK64


def _merge_accs(acc: list[int], secret_offset: int, start: int) -> int:
    result = start
    for pair in range(4):
        result += _fold64(
            acc[2 * pair] ^ _read64(_SECRET, secret_offset + 16 * pair),
            acc[2 * pair + 1] ^ _read64(_SECRET, secret_offset + 16 * pair + 8),
        )
    return _xxh3_avalanche(result & _MASK64)


class _Xxh3Base(PureChecksum):
    """Streaming state for XXH3 inputs longer than 240 bytes.

    Inputs of up to 240 bytes are hashed in one shot from the buffer. Longer inputs
    are consumed one 64-byte stripe at a time, always leaving at least one byte
    unconsumed so the final stripe can be keyed differently, as the algorithm
    requires.
    """

    __slots__ = ("_acc", "_buffer", "_last_consumed", "_length", "_stripes")

    def __init__(self) -> None:
        super().__init__()
        self._acc = list(_INITIAL_ACC)
        self._buffer = b""
        # The trailing bytes of consumed input, needed to build the final stripe
        # when fewer than 64 bytes remain buffered.
        self._last_consumed = b""
        self._length = 0
        # The number of stripes consumed in the current block.
        self._stripes = 0

    def _update(self, data: bytes | bytearray | memoryview) -> None:
        data = self._buffer + data
        self._length += len(data) - len(self._buffer)
        if len(data) > _BUFFER_SIZE:
            data = self._consume(data)
        self._buffer = bytes(data)

    def _consume(self, data: bytes | bytearray) -> bytes | bytearray:
        """Consumes every complete stripe in ``data`` that has at least one byte after it."""
        stripes = (len(data) - 1) // _STRIPE_LEN
        if not stripes:
            return data
        end = stripes * _STRIPE_LEN
        view = memoryview(data)
        a0, a1, a2, a3, a4, a5, a6, a7 = self._acc
        current = self._stripes
        offset = 0
        while offset < end:
            size = min(_STRIPES_PER_BLOCK - current, (end - offset) // _STRIPE_LEN)
            size *= _STRIPE_LEN
            segment = view[offset : offset + size]
            if size == len(_BLOCK_SECRET):
                secret = _BLOCK_SECRET_INT
            else:
                start = current * _STRIPE_LEN
                secret = int.from_bytes(_BLOCK_SECRET[start : start + size], "little")
            keyed = (int.from_bytes(segment, "little") ^ secret).to_bytes(
                size, "little"
            )
            # This is _accumulate_stripe unrolled, with the keyed words read as
            # 32-bit halves. The accumulators are masked once per segment.
            for words, halves in zip(
                _U64X8.iter_unpack(segment), _U32X16.iter_unpack(keyed)
            ):
                d0, d1, d2, d3, d4, d5, d6, d7 = words
                l0, h0, l1, h1, l2, h2, l3, h3, l4, h4, l5, h5, l6, h6, l7, h7 = halves
                a0 += l0 * h0 + d1
                a1 += l1 * h1 + d0
                a2 += l2 * h2 + d3
                a3 += l3 * h3 + d2
                a4 += l4 * h4 + d5
                a5 += l5 * h5 + d4
                a6 += l6 * h6 + d7
                a7 += l7 * h7 + d6
            acc = [value & _MASK64 for value in (a0, a1, a2, a3, a4, a5, a6, a7)]
            current += size // _STRIPE_LEN
            if current == _STRIPES_PER_BLOCK:
                _scramble(acc)
                current = 0
            a0, a1, a2, a3, a4, a5, a6, a7 = acc
            offset += size
        self._acc = [a0, a1, a2, a3, a4, a5, a6, a7]
        self._stripes = current
        self._last_consumed = bytes(data[end - _STRIPE_LEN : end])
        return data[end:]

    def _long_acc(self) -> list[int]:
        """Returns the accumulators after all input, including the final stripe."""
        state = self._copy()
        remaining = state._consume(state._buffer)
        last_stripe = (state._last_consumed + remaining)[-_STRIPE_LEN:]
        _accumulate_stripe(state._acc, _U64X8.unpack(last_stripe), _LAST_STRIPE_SECRET)
        return state._acc

    def _copy(self) -> Self:
        new = type(self)()
        new._acc = list(self._acc)
        new._buffer = self._buffer
        new._last_consumed = self._last_consumed
        new._length = self._length
        new._stripes = self._stripes
        return new


# --------------------------------------------------------------------------------------
# XXH3-64
# --------------------------------------------------------------------------------------


def _xxh3_64_short(data: bytes) -> int:
    length = len(data)
    if length > 128:
        return _xxh3_64_129_to_240(data)
    if length > 16:
        return _xxh3_64_17_to_128(data)
    if length > 8:
        low = _read64(data, 0) ^ (_read64(_SECRET, 24) ^ _read64(_SECRET, 32))
        high = _read64(data, length - 8) ^ (_read64(_SECRET, 40) ^ _read64(_SECRET, 48))
        acc = length + _swap64(low) + high + _fold64(low, high)
        return _xxh3_avalanche(acc & _MASK64)
    if length >= 4:
        combined = _read32(data, length - 4) + (_read32(data, 0) << 32)
        value = combined ^ (_read64(_SECRET, 8) ^ _read64(_SECRET, 16))
        value ^= _rotl64(value, 49) ^ _rotl64(value, 24)
        value = (value * _PRIME_MX2) & _MASK64
        value ^= (value >> 35) + length
        value = (value * _PRIME_MX2) & _MASK64
        return value ^ (value >> 28)
    if length:
        combined = (
            (data[0] << 16) | (data[length >> 1] << 24) | data[-1] | (length << 8)
        )
        return _xxh64_avalanche(combined ^ (_read32(_SECRET, 0) ^ _read32(_SECRET, 4)))
    return _xxh64_avalanche(_read64(_SECRET, 56) ^ _read64(_SECRET, 64))


def _xxh3_64_17_to_128(data: bytes) -> int:
    length = len(data)
    acc = length * _PRIME64_1
    if length > 32:
        if length > 64:
            if length > 96:
                acc += _mix16(data, 48, 96) + _mix16(data, length - 64, 112)
            acc += _mix16(data, 32, 64) + _mix16(data, length - 48, 80)
        acc += _mix16(data, 16, 32) + _mix16(data, length - 32, 48)
    acc += _mix16(data, 0, 0) + _mix16(data, length - 16, 16)
    return _xxh3_avalanche(acc & _MASK64)


def _xxh3_64_129_to_240(data: bytes) -> int:
    length = len(data)
    acc = length * _PRIME64_1
    for round_ in range(8):
        acc += _mix16(data, 16 * round_, 16 * round_)
    acc = _xxh3_avalanche(acc & _MASK64)
    for round_ in range(8, length // 16):
        acc += _mix16(data, 16 * round_, 16 * (round_ - 8) + 3)
    acc += _mix16(data, length - 16, 136 - 17)
    return _xxh3_avalanche(acc & _MASK64)


class XxHash3(_Xxh3Base):
    """XXH3-64 with a seed of zero and the default secret."""

    __slots__ = ()

    def _digest(self) -> bytes:
        if self._length <= _MIDSIZE_MAX:
            value = _xxh3_64_short(self._buffer)
        else:
            value = _merge_accs(
                self._long_acc(), 11, (self._length * _PRIME64_1) & _MASK64
            )
        return value.to_bytes(8, "big")


# --------------------------------------------------------------------------------------
# XXH3-128
# --------------------------------------------------------------------------------------


def _xxh3_128_short(data: bytes) -> tuple[int, int]:
    length = len(data)
    if length > 128:
        return _xxh3_128_129_to_240(data)
    if length > 16:
        return _xxh3_128_17_to_128(data)
    if length > 8:
        return _xxh3_128_9_to_16(data)
    if length >= 4:
        combined = _read32(data, 0) + (_read32(data, length - 4) << 32)
        keyed = combined ^ (_read64(_SECRET, 16) ^ _read64(_SECRET, 24))
        product = keyed * ((_PRIME64_1 + (length << 2)) & _MASK64)
        low = product & _MASK64
        high = ((product >> 64) + (low << 1)) & _MASK64
        low ^= high >> 3
        low ^= low >> 35
        low = (low * _PRIME_MX2) & _MASK64
        low ^= low >> 28
        return low, _xxh3_avalanche(high)
    if length:
        combined_low = (
            (data[0] << 16) | (data[length >> 1] << 24) | data[-1] | (length << 8)
        )
        swapped = _swap32(combined_low)
        combined_high = ((swapped << 13) | (swapped >> 19)) & 0xFFFFFFFF
        low = combined_low ^ (_read32(_SECRET, 0) ^ _read32(_SECRET, 4))
        high = combined_high ^ (_read32(_SECRET, 8) ^ _read32(_SECRET, 12))
        return _xxh64_avalanche(low), _xxh64_avalanche(high)
    return (
        _xxh64_avalanche(_read64(_SECRET, 64) ^ _read64(_SECRET, 72)),
        _xxh64_avalanche(_read64(_SECRET, 80) ^ _read64(_SECRET, 88)),
    )


def _xxh3_128_9_to_16(data: bytes) -> tuple[int, int]:
    length = len(data)
    first = _read64(data, 0)
    last = _read64(data, length - 8)
    product = (
        first ^ last ^ (_read64(_SECRET, 32) ^ _read64(_SECRET, 40))
    ) * _PRIME64_1
    low = (product + ((length - 1) << 54)) & _MASK64
    high = product >> 64
    last ^= _read64(_SECRET, 48) ^ _read64(_SECRET, 56)
    high = (high + last + (last & 0xFFFFFFFF) * (_PRIME32_2 - 1)) & _MASK64
    low ^= _swap64(high)
    product = low * _PRIME64_2
    final_low = product & _MASK64
    final_high = ((product >> 64) + high * _PRIME64_2) & _MASK64
    return _xxh3_avalanche(final_low), _xxh3_avalanche(final_high)


def _mix32(
    acc: tuple[int, int],
    data: bytes,
    first: int,
    second: int,
    secret_offset: int,
) -> tuple[int, int]:
    low, high = acc
    low += _mix16(data, first, secret_offset)
    low ^= (_read64(data, second) + _read64(data, second + 8)) & _MASK64
    high += _mix16(data, second, secret_offset + 16)
    high ^= (_read64(data, first) + _read64(data, first + 8)) & _MASK64
    return low & _MASK64, high & _MASK64


def _finish_128(acc: tuple[int, int], length: int) -> tuple[int, int]:
    low, high = acc
    final_low = (low + high) & _MASK64
    final_high = (low * _PRIME64_1 + high * _PRIME64_4 + length * _PRIME64_2) & _MASK64
    return _xxh3_avalanche(final_low), (-_xxh3_avalanche(final_high)) & _MASK64


def _xxh3_128_17_to_128(data: bytes) -> tuple[int, int]:
    length = len(data)
    acc = ((length * _PRIME64_1) & _MASK64, 0)
    if length > 32:
        if length > 64:
            if length > 96:
                acc = _mix32(acc, data, 48, length - 64, 96)
            acc = _mix32(acc, data, 32, length - 48, 64)
        acc = _mix32(acc, data, 16, length - 32, 32)
    acc = _mix32(acc, data, 0, length - 16, 0)
    return _finish_128(acc, length)


def _xxh3_128_129_to_240(data: bytes) -> tuple[int, int]:
    length = len(data)
    acc = ((length * _PRIME64_1) & _MASK64, 0)
    for offset in range(0, 128, 32):
        acc = _mix32(acc, data, offset, offset + 16, offset)
    acc = (_xxh3_avalanche(acc[0]), _xxh3_avalanche(acc[1]))
    for offset in range(128, length - 31, 32):
        acc = _mix32(acc, data, offset, offset + 16, 3 + offset - 128)
    acc = _mix32(acc, data, length - 16, length - 32, 136 - 17 - 16)
    return _finish_128(acc, length)


class XxHash128(_Xxh3Base):
    """XXH3-128 with a seed of zero and the default secret."""

    __slots__ = ()

    def _digest(self) -> bytes:
        if self._length <= _MIDSIZE_MAX:
            low, high = _xxh3_128_short(self._buffer)
        else:
            acc = self._long_acc()
            low = _merge_accs(acc, 11, (self._length * _PRIME64_1) & _MASK64)
            high = _merge_accs(
                acc,
                _SECRET_SIZE - _STRIPE_LEN - 11,
                ~(self._length * _PRIME64_2) & _MASK64,
            )
        return ((high << 64) | low).to_bytes(16, "big")
