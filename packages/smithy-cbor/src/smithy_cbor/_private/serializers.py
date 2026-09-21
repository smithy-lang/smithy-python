#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""CBOR shape serializer.

Naive, non-streaming: aggregates are buffered so their length can be written as the
header. Correctness first; the byte layout is not yet minimally encoded.
"""

import datetime
import struct as _struct
from collections.abc import Callable
from contextlib import AbstractContextManager
from decimal import Decimal
from io import BytesIO
from types import TracebackType
from typing import Self

from smithy_core.documents import Document
from smithy_core.interfaces import BytesWriter
from smithy_core.schemas import Schema
from smithy_core.serializers import MapSerializer, ShapeSerializer
from smithy_core.shapes import ShapeType

from ..settings import CBORSettings

# CBOR major types, shifted into the high 3 bits of the initial byte.
_MAJOR_UINT = 0 << 5
_MAJOR_NEGINT = 1 << 5
_MAJOR_BYTES = 2 << 5
_MAJOR_TEXT = 3 << 5
_MAJOR_ARRAY = 4 << 5
_MAJOR_MAP = 5 << 5
_MAJOR_TAG = 6 << 5
_MAJOR_SIMPLE = 7 << 5

# Tags used by rpcv2Cbor.
_TAG_EPOCH = 1
_TAG_UNSIGNED_BIGNUM = 2
_TAG_NEGATIVE_BIGNUM = 3
_TAG_DECIMAL_FRACTION = 4

# Simple values (major type 7).
_SIMPLE_FALSE = 20
_SIMPLE_TRUE = 21
_SIMPLE_NULL = 22

# Additional-information values 24-27 select how many bytes hold the argument that
# follows the initial byte. 31 carries no argument: it signals an indefinite-length item.
_W_1BYTE = 24
_W_2BYTE = 25
_W_4BYTE = 26
_W_8BYTE = 27
_INDEFINITE = 31

# Indefinite-length aggregate markers.
_INDEFINITE_ARRAY = bytes((_MAJOR_ARRAY | _INDEFINITE,))  # 0x9F: indefinite array
_INDEFINITE_MAP = bytes((_MAJOR_MAP | _INDEFINITE,))  # 0xBF: indefinite-length map
_BREAK = bytes(
    (_MAJOR_SIMPLE | _INDEFINITE,)
)  # 0xFF: "break" ending an indefinite item


def _encode_head(major: int, arg: int) -> bytes:
    """Uses the smallest of the 1/2/4/8-byte length forms per RFC 8949 §3."""
    if arg < _W_1BYTE:
        return bytes((major | arg,))
    if arg < 0x100:
        return bytes((major | _W_1BYTE, arg))
    if arg < 0x10000:
        return bytes((major | _W_2BYTE,)) + arg.to_bytes(2, "big")
    if arg < 0x100000000:
        return bytes((major | _W_4BYTE,)) + arg.to_bytes(4, "big")
    return bytes((major | _W_8BYTE,)) + arg.to_bytes(8, "big")


def _encode_int(value: int) -> bytes:
    if value >= 0:
        return _encode_head(_MAJOR_UINT, value)
    # Negative integers encode -1 - n as an unsigned argument.
    return _encode_head(_MAJOR_NEGINT, -1 - value)


# Bare major-type values (not shifted) for the byte-level scanner below.
_M_BYTES = 2
_M_TEXT = 3
_M_ARRAY = 4
_M_MAP = 5
_M_TAG = 6


def _scan_head(data: bytes, pos: int) -> tuple[int, int, int]:
    """For indefinite-length items the argument is -1."""
    initial = data[pos]
    major = initial >> 5
    ai = initial & 0x1F
    pos += 1
    if ai < _W_1BYTE:
        return major, ai, pos
    if ai == _W_1BYTE:
        return major, data[pos], pos + 1
    if ai == _W_2BYTE:
        return major, int.from_bytes(data[pos : pos + 2], "big"), pos + 2
    if ai == _W_4BYTE:
        return major, int.from_bytes(data[pos : pos + 4], "big"), pos + 4
    if ai == _W_8BYTE:
        return major, int.from_bytes(data[pos : pos + 8], "big"), pos + 8
    if ai == _INDEFINITE:
        return major, -1, pos
    raise ValueError(f"Reserved CBOR additional-information value: {ai}")


def _scan_item(data: bytes, pos: int) -> int:
    major, arg, pos = _scan_head(data, pos)
    if major in (_M_BYTES, _M_TEXT):
        return pos + arg
    if major == _M_ARRAY:
        if arg == -1:
            while data[pos] != 0xFF:
                pos = _scan_item(data, pos)
            return pos + 1
        for _ in range(arg):
            pos = _scan_item(data, pos)
        return pos
    if major == _M_MAP:
        if arg == -1:
            while data[pos] != 0xFF:
                pos = _scan_item(data, pos)
                pos = _scan_item(data, pos)
            return pos + 1
        for _ in range(arg):
            pos = _scan_item(data, pos)
            pos = _scan_item(data, pos)
        return pos
    if major == _M_TAG:
        return _scan_item(data, pos)
    # Ints (major 0/1) and simple/float (major 7): the head already consumed any
    # 1/2/4/8-byte payload, so the item ends here.
    return pos


def _split_map_pairs(data: bytes) -> list[tuple[bytes, bytes]]:
    """Used to reorder a struct's buffered members by their (text) member-name key."""
    pairs: list[tuple[bytes, bytes]] = []
    pos = 0
    end = len(data)
    while pos < end:
        key_end = _scan_item(data, pos)
        value_end = _scan_item(data, key_end)
        pairs.append((data[pos:key_end], data[key_end:value_end]))
        pos = value_end
    return pairs


class CBORShapeSerializer(ShapeSerializer):
    def __init__(self, sink: BytesWriter, settings: CBORSettings) -> None:
        self._sink = sink
        self.settings = settings

    def write(self, data: bytes) -> None:
        self._sink.write(data)

    def begin_struct(
        self, schema: "Schema"
    ) -> AbstractContextManager["ShapeSerializer"]:
        return _CBORStructSerializer(self)

    def begin_list(
        self, schema: "Schema", size: int
    ) -> AbstractContextManager["ShapeSerializer"]:
        self.write(_INDEFINITE_ARRAY)
        return _CBORListSerializer(self)

    def begin_map(
        self, schema: "Schema", size: int
    ) -> AbstractContextManager["MapSerializer"]:
        self.write(_INDEFINITE_MAP)
        return _CBORMapSerializer(self)

    def write_null(self, schema: "Schema") -> None:
        self.write(bytes((_MAJOR_SIMPLE | _SIMPLE_NULL,)))

    def write_boolean(self, schema: "Schema", value: bool) -> None:
        self.write(bytes((_MAJOR_SIMPLE | (_SIMPLE_TRUE if value else _SIMPLE_FALSE),)))

    def write_integer(self, schema: "Schema", value: int) -> None:
        self.write(_encode_int(value))

    def write_float(self, schema: "Schema", value: float) -> None:
        # A `float` shape encodes as IEEE single (major 7, ai 26); `double` as IEEE
        # double (ai 27). Half-precision is not emitted. NaN/Infinity round-trip through
        # struct.pack unchanged.
        if schema.shape_type is ShapeType.FLOAT:
            self.write(bytes((_MAJOR_SIMPLE | 26,)) + _struct.pack(">f", value))
        else:
            self.write(bytes((_MAJOR_SIMPLE | 27,)) + _struct.pack(">d", value))

    def write_big_integer(self, schema: "Schema", value: int) -> None:
        if value >= 0:
            tag, magnitude = _TAG_UNSIGNED_BIGNUM, value
        else:
            tag, magnitude = _TAG_NEGATIVE_BIGNUM, -1 - value
        length = (magnitude.bit_length() + 7) // 8
        payload = magnitude.to_bytes(length, "big")
        self.write(_encode_head(_MAJOR_TAG, tag))
        self.write(_encode_head(_MAJOR_BYTES, len(payload)))
        self.write(payload)

    def write_big_decimal(self, schema: "Schema", value: Decimal) -> None:
        sign, digits, exponent = value.as_tuple()
        if not isinstance(exponent, int):  # "n"/"N"/"F" for special values
            raise ValueError(f"Cannot CBOR-encode non-finite Decimal: {value!r}")
        mantissa = int("".join(map(str, digits)) or "0")
        if sign:
            mantissa = -mantissa
        self.write(_encode_head(_MAJOR_TAG, _TAG_DECIMAL_FRACTION))
        self.write(_encode_head(_MAJOR_ARRAY, 2))
        self.write(_encode_int(exponent))
        self.write(_encode_int(mantissa))

    def write_string(self, schema: "Schema", value: str) -> None:
        encoded = value.encode("utf-8")
        self.write(_encode_head(_MAJOR_TEXT, len(encoded)))
        self.write(encoded)

    def write_blob(self, schema: "Schema", value: bytes) -> None:
        self.write(_encode_head(_MAJOR_BYTES, len(value)))
        self.write(value)

    def write_timestamp(self, schema: "Schema", value: datetime.datetime) -> None:
        # timestampFormat MUST NOT be respected.
        self.write(_encode_head(_MAJOR_TAG, _TAG_EPOCH))
        self.write_float(schema, value.timestamp())

    def write_document(self, schema: "Schema", value: "Document") -> None:
        raise NotImplementedError(
            "The rpcv2Cbor protocol does not support document types."
        )

    def flush(self) -> None:
        # BytesWriter has no flush; the sink is written to directly.
        pass


class _CBORStructSerializer(ShapeSerializer):
    """Members are re-sorted by name on close so the wire bytes match the protocol-test
    vectors, which order map keys lexicographically. CBOR maps are unordered, so this
    only affects byte-exactness, not meaning.
    """

    def __init__(self, parent: CBORShapeSerializer) -> None:
        self._parent = parent
        self._buffer = BytesIO()
        self._member = CBORShapeSerializer(self._buffer, parent.settings)

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if exc_value is not None:
            return
        pairs = _split_map_pairs(self._buffer.getvalue())
        pairs.sort(key=lambda pair: pair[0])
        self._parent.write(_INDEFINITE_MAP)
        for key_bytes, value_bytes in pairs:
            self._parent.write(key_bytes)
            self._parent.write(value_bytes)
        self._parent.write(_BREAK)

    def _write_key(self, schema: "Schema") -> None:
        member_name = schema.expect_member_name()
        encoded = member_name.encode("utf-8")
        self._buffer.write(_encode_head(_MAJOR_TEXT, len(encoded)))
        self._buffer.write(encoded)

    def begin_struct(
        self, schema: "Schema"
    ) -> AbstractContextManager["ShapeSerializer"]:
        self._write_key(schema)
        return self._member.begin_struct(schema)

    def begin_list(
        self, schema: "Schema", size: int
    ) -> AbstractContextManager["ShapeSerializer"]:
        self._write_key(schema)
        return self._member.begin_list(schema, size)

    def begin_map(
        self, schema: "Schema", size: int
    ) -> AbstractContextManager["MapSerializer"]:
        self._write_key(schema)
        return self._member.begin_map(schema, size)

    def write_null(self, schema: "Schema") -> None:
        self._write_key(schema)
        self._member.write_null(schema)

    def write_boolean(self, schema: "Schema", value: bool) -> None:
        self._write_key(schema)
        self._member.write_boolean(schema, value)

    def write_integer(self, schema: "Schema", value: int) -> None:
        self._write_key(schema)
        self._member.write_integer(schema, value)

    def write_float(self, schema: "Schema", value: float) -> None:
        self._write_key(schema)
        self._member.write_float(schema, value)

    def write_big_integer(self, schema: "Schema", value: int) -> None:
        self._write_key(schema)
        self._member.write_big_integer(schema, value)

    def write_big_decimal(self, schema: "Schema", value: Decimal) -> None:
        self._write_key(schema)
        self._member.write_big_decimal(schema, value)

    def write_string(self, schema: "Schema", value: str) -> None:
        self._write_key(schema)
        self._member.write_string(schema, value)

    def write_blob(self, schema: "Schema", value: bytes) -> None:
        self._write_key(schema)
        self._member.write_blob(schema, value)

    def write_timestamp(self, schema: "Schema", value: datetime.datetime) -> None:
        self._write_key(schema)
        self._member.write_timestamp(schema, value)

    def write_document(self, schema: "Schema", value: "Document") -> None:
        raise NotImplementedError(
            "The rpcv2Cbor protocol does not support document types."
        )

    def flush(self) -> None:
        pass


class _CBORListSerializer(ShapeSerializer):
    """Serializes as an indefinite-length array (0x9F ... 0xFF), so no size is needed;
    elements go straight to the sink, closed by a break byte.
    """

    def __init__(self, parent: CBORShapeSerializer) -> None:
        self._parent = parent

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if exc_value is not None:
            return
        self._parent.write(_BREAK)

    def begin_struct(
        self, schema: "Schema"
    ) -> AbstractContextManager["ShapeSerializer"]:
        return self._parent.begin_struct(schema)

    def begin_list(
        self, schema: "Schema", size: int
    ) -> AbstractContextManager["ShapeSerializer"]:
        return self._parent.begin_list(schema, size)

    def begin_map(
        self, schema: "Schema", size: int
    ) -> AbstractContextManager["MapSerializer"]:
        return self._parent.begin_map(schema, size)

    def write_null(self, schema: "Schema") -> None:
        self._parent.write_null(schema)

    def write_boolean(self, schema: "Schema", value: bool) -> None:
        self._parent.write_boolean(schema, value)

    def write_integer(self, schema: "Schema", value: int) -> None:
        self._parent.write_integer(schema, value)

    def write_float(self, schema: "Schema", value: float) -> None:
        self._parent.write_float(schema, value)

    def write_big_integer(self, schema: "Schema", value: int) -> None:
        self._parent.write_big_integer(schema, value)

    def write_big_decimal(self, schema: "Schema", value: Decimal) -> None:
        self._parent.write_big_decimal(schema, value)

    def write_string(self, schema: "Schema", value: str) -> None:
        self._parent.write_string(schema, value)

    def write_blob(self, schema: "Schema", value: bytes) -> None:
        self._parent.write_blob(schema, value)

    def write_timestamp(self, schema: "Schema", value: datetime.datetime) -> None:
        self._parent.write_timestamp(schema, value)

    def write_document(self, schema: "Schema", value: "Document") -> None:
        self._parent.write_document(schema, value)

    def flush(self) -> None:
        pass


class _CBORMapSerializer(MapSerializer):
    def __init__(self, parent: CBORShapeSerializer) -> None:
        self._parent = parent

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if exc_value is not None:
            return
        self._parent.write(_BREAK)

    def entry(self, key: str, value_writer: Callable[[ShapeSerializer], None]) -> None:
        encoded = key.encode("utf-8")
        self._parent.write(_encode_head(_MAJOR_TEXT, len(encoded)))
        self._parent.write(encoded)
        value_writer(self._parent)
