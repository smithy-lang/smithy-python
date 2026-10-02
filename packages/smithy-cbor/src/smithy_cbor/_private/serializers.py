#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""CBOR shape serializer.

Aggregates are definite-length: lists and maps take their element count up front, and
structs reserve a header slot sized for the schema's max member count, then patch the
actual present-member count into it on close.
"""

import datetime
import struct as _struct
from collections.abc import Callable
from contextlib import AbstractContextManager, nullcontext
from decimal import Decimal
from io import BytesIO
from types import TracebackType
from typing import Self, override

from smithy_core.documents import Document
from smithy_core.interfaces import BytesWriter
from smithy_core.schemas import Schema
from smithy_core.serializers import MapSerializer, ShapeSerializer
from smithy_core.shapes import ShapeType
from smithy_core.utils import ensure_utc

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

# Additional-information 24-27: the following value occupies 1, 2, 4, or 8 bytes.
_W_1BYTE = 24
_W_2BYTE = 25
_W_4BYTE = 26
_W_8BYTE = 27


class CBORShapeSerializer(ShapeSerializer):
    def __init__(self, sink: BytesWriter, settings: CBORSettings) -> None:
        self._sink = sink
        self.settings = settings

    def write(self, data: bytes) -> None:
        self._sink.write(data)

    @override
    def begin_struct(self, schema: Schema) -> AbstractContextManager[ShapeSerializer]:
        return _CBORStructSerializer(self, self._sink, schema)

    @override
    def begin_list(
        self, schema: Schema, size: int
    ) -> AbstractContextManager[ShapeSerializer]:
        # A definite-length list needs no per-element framing or close step, and a value
        # encodes identically inside a collection or not, so elements reuse this same
        # serializer; only the header is context-specific.
        self.write(_encode_head(_MAJOR_ARRAY, size))
        return nullcontext(self)

    @override
    def begin_map(
        self, schema: Schema, size: int
    ) -> AbstractContextManager[MapSerializer]:
        self.write(_encode_head(_MAJOR_MAP, size))
        return nullcontext(_CBORMapSerializer(self))

    @override
    def write_null(self, schema: Schema) -> None:
        self.write(bytes((_MAJOR_SIMPLE | _SIMPLE_NULL,)))

    @override
    def write_boolean(self, schema: Schema, value: bool) -> None:
        self.write(bytes((_MAJOR_SIMPLE | (_SIMPLE_TRUE if value else _SIMPLE_FALSE),)))

    @override
    def write_integer(self, schema: Schema, value: int) -> None:
        self.write(_encode_int(value))

    @override
    def write_float(self, schema: Schema, value: float) -> None:
        # A `float` shape encodes as IEEE single (major 7, add_info 26); `double` as
        # IEEE double (add_info 27). Half-precision is not emitted. NaN/Infinity
        # round-trip through struct.pack unchanged.
        if schema.shape_type is ShapeType.FLOAT:
            self.write(bytes((_MAJOR_SIMPLE | 26,)) + _struct.pack(">f", value))
        else:
            self.write(bytes((_MAJOR_SIMPLE | 27,)) + _struct.pack(">d", value))

    @override
    def write_big_integer(self, schema: Schema, value: int) -> None:
        if value >= 0:
            tag, magnitude = _TAG_UNSIGNED_BIGNUM, value
        else:
            tag, magnitude = _TAG_NEGATIVE_BIGNUM, -1 - value
        length = (magnitude.bit_length() + 7) // 8
        payload = magnitude.to_bytes(length, "big")
        self.write(_encode_head(_MAJOR_TAG, tag))
        self.write(_encode_head(_MAJOR_BYTES, len(payload)))
        self.write(payload)

    @override
    def write_big_decimal(self, schema: Schema, value: Decimal) -> None:
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

    @override
    def write_string(self, schema: Schema, value: str) -> None:
        encoded = value.encode("utf-8")
        self.write(_encode_head(_MAJOR_TEXT, len(encoded)))
        self.write(encoded)

    @override
    def write_blob(self, schema: Schema, value: bytes) -> None:
        self.write(_encode_head(_MAJOR_BYTES, len(value)))
        self.write(value)

    @override
    def write_timestamp(self, schema: Schema, value: datetime.datetime) -> None:
        # timestampFormat MUST NOT be respected.
        self.write(_encode_head(_MAJOR_TAG, _TAG_EPOCH))
        self.write_float(schema, ensure_utc(value).timestamp())

    @override
    def write_document(self, schema: Schema, value: Document) -> None:
        raise NotImplementedError(
            "The rpcv2Cbor protocol does not support document types."
        )

    @override
    def flush(self) -> None:
        # BytesWriter has no flush; the sink is written to directly.
        pass


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


def _head_width(arg: int) -> int:
    """Bytes _encode_head needs for arg. A struct reserves this for its MAX member count
    up front, then patches the actual (<=) count into that width on close.
    """
    if arg < _W_1BYTE:
        return 1
    if arg < 0x100:
        return 2
    if arg < 0x10000:
        return 3
    if arg < 0x100000000:
        return 5
    return 9


def _write_head_fixed(
    buf: memoryview, offset: int, major: int, arg: int, width: int
) -> None:
    """Patches a definite header of exactly `width` bytes into `buf` at `offset`.

    CBOR allows a non-minimal length form, so an over-reserved width just holds the same
    count in a wider encoding (e.g. 5 as 0xb8 0x05, not the minimal 0xa5) -- no gap.
    """
    if width == 1:
        buf[offset] = major | arg
        return
    add_info = {2: _W_1BYTE, 3: _W_2BYTE, 5: _W_4BYTE, 9: _W_8BYTE}[width]
    buf[offset] = major | add_info
    buf[offset + 1 : offset + width] = arg.to_bytes(width - 1, "big")


def _encode_int(value: int) -> bytes:
    if value >= 0:
        return _encode_head(_MAJOR_UINT, value)
    # Negative integers encode -1 - n as an unsigned argument.
    return _encode_head(_MAJOR_NEGINT, -1 - value)


# Attribute name under which a member schema's pre-encoded CBOR key (text header +
# UTF-8 name) is memoized. Member schemas are long-lived and shared, so encoding the
# key once per schema removes a per-serialization encode + head allocation.
_CBOR_KEY_ATTR = "_cbor_encoded_key"


def _encoded_member_key(schema: Schema) -> bytes:
    key = getattr(schema, _CBOR_KEY_ATTR, None)
    if key is None:
        encoded = schema.expect_member_name().encode("utf-8")
        key = _encode_head(_MAJOR_TEXT, len(encoded)) + encoded
        # Schema is a frozen dataclass; object.__setattr__ is its own escape hatch.
        object.__setattr__(schema, _CBOR_KEY_ATTR, key)
    return key


class _CBORStructSerializer(ShapeSerializer):
    """Emits definite-length map. Reserves the full memberCount worth of byte-width
    and writes the actual member count back to that position when completing the struct.
    This may waste up to 1 byte in edge-case conditions, but minimizes overall work.
    """

    def __init__(
        self, parent: CBORShapeSerializer, sink: BytesWriter, schema: Schema
    ) -> None:
        self._parent = parent
        # Reserve-and-patch needs a seekable buffer; Codec.serialize always supplies a
        # BytesIO, and rpcv2Cbor has no streaming-serialize path that would not.
        if not isinstance(sink, BytesIO):
            raise TypeError(
                "CBOR struct serialization requires a seekable BytesIO sink."
            )
        self._sink: BytesIO = sink
        self._width = _head_width(len(schema.members))
        self._offset = sink.tell()
        sink.write(bytes(self._width))  # reserved header slot, patched on close
        self._count = 0

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
        buf = self._sink.getbuffer()
        _write_head_fixed(buf, self._offset, _MAJOR_MAP, self._count, self._width)
        buf.release()

    @override
    def begin_struct(self, schema: Schema) -> AbstractContextManager[ShapeSerializer]:
        self._write_key(schema)
        return self._parent.begin_struct(schema)

    @override
    def begin_list(
        self, schema: Schema, size: int
    ) -> AbstractContextManager[ShapeSerializer]:
        self._write_key(schema)
        return self._parent.begin_list(schema, size)

    @override
    def begin_map(
        self, schema: Schema, size: int
    ) -> AbstractContextManager[MapSerializer]:
        self._write_key(schema)
        return self._parent.begin_map(schema, size)

    @override
    def write_null(self, schema: Schema) -> None:
        self._write_key(schema)
        self._parent.write_null(schema)

    @override
    def write_boolean(self, schema: Schema, value: bool) -> None:
        self._write_key(schema)
        self._parent.write_boolean(schema, value)

    @override
    def write_integer(self, schema: Schema, value: int) -> None:
        self._write_key(schema)
        self._parent.write_integer(schema, value)

    @override
    def write_float(self, schema: Schema, value: float) -> None:
        self._write_key(schema)
        self._parent.write_float(schema, value)

    @override
    def write_big_integer(self, schema: Schema, value: int) -> None:
        self._write_key(schema)
        self._parent.write_big_integer(schema, value)

    @override
    def write_big_decimal(self, schema: Schema, value: Decimal) -> None:
        self._write_key(schema)
        self._parent.write_big_decimal(schema, value)

    @override
    def write_string(self, schema: Schema, value: str) -> None:
        self._write_key(schema)
        self._parent.write_string(schema, value)

    @override
    def write_blob(self, schema: Schema, value: bytes) -> None:
        self._write_key(schema)
        self._parent.write_blob(schema, value)

    @override
    def write_timestamp(self, schema: Schema, value: datetime.datetime) -> None:
        self._write_key(schema)
        self._parent.write_timestamp(schema, value)

    @override
    def write_document(self, schema: Schema, value: Document) -> None:
        raise NotImplementedError(
            "The rpcv2Cbor protocol does not support document types."
        )

    @override
    def flush(self) -> None:
        pass

    def _write_key(self, schema: Schema) -> None:
        self._count += 1
        self._sink.write(_encoded_member_key(schema))


class _CBORMapSerializer(MapSerializer):
    """The definite-length map header (from `size`) is written by `begin_map` before
    this is constructed; entries stream straight to the sink.
    """

    def __init__(self, parent: CBORShapeSerializer) -> None:
        self._parent = parent

    @override
    def entry(self, key: str, value_writer: Callable[[ShapeSerializer], None]) -> None:
        encoded = key.encode("utf-8")
        self._parent.write(_encode_head(_MAJOR_TEXT, len(encoded)))
        self._parent.write(encoded)
        value_writer(self._parent)
