#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""Generic, schema-free CBOR decoding.

For STRUCTURAL comparison: CBOR admits several encodings of the same value (definite vs
indefinite length, map key order, integer width), so comparing two encoded bodies
byte-for-byte gives false mismatches. Decoding both with :func:`loads` and comparing the
resulting Python values compares meaning, not layout. The generated protocol tests use
this to compare request bodies.
"""

import struct as _struct
from decimal import Decimal
from typing import Any

_TAG_EPOCH = 1
_TAG_UNSIGNED_BIGNUM = 2
_TAG_NEGATIVE_BIGNUM = 3
_TAG_DECIMAL_FRACTION = 4

# Additional-information values 24-27 select how many bytes hold the argument that
# follows the initial byte. 31 carries no argument: it signals an indefinite-length item.
_W_1BYTE = 24
_W_2BYTE = 25
_W_4BYTE = 26
_W_8BYTE = 27
_INDEFINITE = 31

_BREAK = 0xFF


def loads(data: bytes) -> Any:
    return _decode(data, 0)[0]


def strip_default_members(payload: bytes, defaults: dict[str, Any]) -> bytes:
    """Used by the rpcv2Cbor client to omit top-level input members left at their
    default, which the protocol's request vectors expect. Nested maps are untouched.
    """
    major, _ai, arg, pos = _read_head(payload, 0)
    if major != 5:
        return payload
    kept: list[bytes] = []
    end = len(payload)

    def _matches_default(key_bytes: bytes, value_bytes: bytes) -> bool:
        key = loads(key_bytes)
        if not isinstance(key, str) or key not in defaults:
            return False
        return loads(value_bytes) == defaults[key]

    if arg == -1:
        while payload[pos] != _BREAK:
            key_end = _scan_item(payload, pos)
            value_end = _scan_item(payload, key_end)
            if not _matches_default(payload[pos:key_end], payload[key_end:value_end]):
                kept.append(payload[pos:value_end])
            pos = value_end
    else:
        for _ in range(arg):
            if pos >= end:
                break
            key_end = _scan_item(payload, pos)
            value_end = _scan_item(payload, key_end)
            if not _matches_default(payload[pos:key_end], payload[key_end:value_end]):
                kept.append(payload[pos:value_end])
            pos = value_end

    return b"\xbf" + b"".join(kept) + b"\xff"


def _scan_head(data: bytes, pos: int) -> tuple[int, int, int]:
    major, _ai, arg, next_pos = _read_head(data, pos)
    return major, arg, next_pos


def _scan_item(data: bytes, pos: int) -> int:
    major, arg, pos = _scan_head(data, pos)
    if major in (2, 3):
        if arg == -1:
            while data[pos] != _BREAK:
                _m, clen, pos = _scan_head(data, pos)
                pos += clen
            return pos + 1
        return pos + arg
    if major == 4:
        if arg == -1:
            while data[pos] != _BREAK:
                pos = _scan_item(data, pos)
            return pos + 1
        for _ in range(arg):
            pos = _scan_item(data, pos)
        return pos
    if major == 5:
        if arg == -1:
            while data[pos] != _BREAK:
                pos = _scan_item(data, pos)
                pos = _scan_item(data, pos)
            return pos + 1
        for _ in range(arg):
            pos = _scan_item(data, pos)
            pos = _scan_item(data, pos)
        return pos
    if major == 6:
        return _scan_item(data, pos)
    return pos


def _read_head(data: bytes, pos: int) -> tuple[int, int, int, int]:
    """Indefinite arg is -1."""
    initial = data[pos]
    major = initial >> 5
    ai = initial & 0x1F
    pos += 1
    if ai < _W_1BYTE:
        return major, ai, ai, pos
    if ai == _W_1BYTE:
        return major, ai, data[pos], pos + 1
    if ai == _W_2BYTE:
        return major, ai, int.from_bytes(data[pos : pos + 2], "big"), pos + 2
    if ai == _W_4BYTE:
        return major, ai, int.from_bytes(data[pos : pos + 4], "big"), pos + 4
    if ai == _W_8BYTE:
        return major, ai, int.from_bytes(data[pos : pos + 8], "big"), pos + 8
    if ai == _INDEFINITE:
        return major, ai, -1, pos
    raise ValueError(f"Reserved CBOR additional-information value: {ai}")


def _decode(data: bytes, pos: int) -> tuple[Any, int]:
    major, ai, arg, pos = _read_head(data, pos)
    if major == 0:
        return arg, pos
    if major == 1:
        return -1 - arg, pos
    if major == 2:
        return _decode_bytes(data, pos, arg, major)
    if major == 3:
        raw, pos = _decode_bytes(data, pos, arg, major)
        return raw.decode("utf-8"), pos
    if major == 4:
        return _decode_array(data, pos, arg)
    if major == 5:
        return _decode_map(data, pos, arg)
    if major == 6:
        return _decode_tagged(data, pos, arg)
    return _decode_simple(data, ai, arg, pos)


def _decode_bytes(data: bytes, pos: int, arg: int, major: int) -> tuple[bytes, int]:
    if arg != -1:
        return data[pos : pos + arg], pos + arg
    # Indefinite-length string: concatenation of definite-length chunks until break.
    chunks = bytearray()
    while data[pos] != _BREAK:
        _cmajor, _cai, clen, pos = _read_head(data, pos)
        chunks += data[pos : pos + clen]
        pos += clen
    return bytes(chunks), pos + 1


def _decode_array(data: bytes, pos: int, arg: int) -> tuple[list[Any], int]:
    items: list[Any] = []
    if arg == -1:
        while data[pos] != _BREAK:
            value, pos = _decode(data, pos)
            items.append(value)
        return items, pos + 1
    for _ in range(arg):
        value, pos = _decode(data, pos)
        items.append(value)
    return items, pos


def _decode_map(data: bytes, pos: int, arg: int) -> tuple[dict[Any, Any], int]:
    result: dict[Any, Any] = {}
    if arg == -1:
        while data[pos] != _BREAK:
            key, pos = _decode(data, pos)
            value, pos = _decode(data, pos)
            result[key] = value
        return result, pos + 1
    for _ in range(arg):
        key, pos = _decode(data, pos)
        value, pos = _decode(data, pos)
        result[key] = value
    return result, pos


def _decode_tagged(data: bytes, pos: int, tag: int) -> tuple[Any, int]:
    if tag in (_TAG_UNSIGNED_BIGNUM, _TAG_NEGATIVE_BIGNUM):
        magnitude_bytes, pos = _decode(data, pos)
        magnitude = int.from_bytes(magnitude_bytes, "big")
        return (magnitude if tag == _TAG_UNSIGNED_BIGNUM else -1 - magnitude), pos
    if tag == _TAG_DECIMAL_FRACTION:
        array, pos = _decode(data, pos)
        exponent, mantissa = array
        return Decimal(mantissa).scaleb(exponent), pos
    if tag == _TAG_EPOCH:
        seconds, pos = _decode(data, pos)
        return seconds, pos
    # Unknown tag: return the tagged content unchanged.
    return _decode(data, pos)


def _decode_simple(data: bytes, ai: int, arg: int, pos: int) -> tuple[Any, int]:
    if ai == 20:
        return False, pos
    if ai == 21:
        return True, pos
    if ai in (22, 23):
        return None, pos
    if ai == 25:
        return _decode_half(arg), pos
    if ai == 26:
        return _struct.unpack(">f", arg.to_bytes(4, "big"))[0], pos
    if ai == 27:
        return _struct.unpack(">d", arg.to_bytes(8, "big"))[0], pos
    return arg, pos


def _decode_half(bits: int) -> float:
    sign = (bits >> 15) & 0x1
    exp = (bits >> 10) & 0x1F
    mant = bits & 0x3FF
    if exp == 0:
        value = (mant / 1024.0) * (2.0**-14)
    elif exp == 0x1F:
        value = float("inf") if mant == 0 else float("nan")
    else:
        value = (1.0 + mant / 1024.0) * (2.0 ** (exp - 15))
    return -value if sign else value
