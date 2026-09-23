#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""CBOR shape deserializer."""

import datetime
import struct as _struct
from collections.abc import Callable
from decimal import Decimal

from smithy_core.deserializers import ShapeDeserializer
from smithy_core.documents import Document
from smithy_core.exceptions import SmithyError
from smithy_core.interfaces import BytesReader
from smithy_core.schemas import Schema

from ..settings import CBORSettings

# Major type occupies the high 3 bits; the low 5 bits are the "additional information".
_MAJOR_UINT = 0
_MAJOR_NEGINT = 1
_MAJOR_BYTES = 2
_MAJOR_TEXT = 3
_MAJOR_ARRAY = 4
_MAJOR_MAP = 5
_MAJOR_TAG = 6
_MAJOR_SIMPLE = 7

# Additional-information 24-27: the following value occupies 1, 2, 4, or 8 bytes.
_W_1BYTE = 24
_W_2BYTE = 25
_W_4BYTE = 26
_W_8BYTE = 27
_INDEFINITE = 31

_SIMPLE_FALSE = 20
_SIMPLE_TRUE = 21
_SIMPLE_NULL = 22

_TAG_EPOCH = 1
_TAG_UNSIGNED_BIGNUM = 2
_TAG_NEGATIVE_BIGNUM = 3
_TAG_DECIMAL_FRACTION = 4

# ends indefinite item
_BREAK = 0xFF


class CBORDecodeError(SmithyError):
    pass


class _Cursor:
    def __init__(self, data: bytes) -> None:
        self._data = data
        self._pos = 0

    def _take(self, n: int) -> bytes:
        end = self._pos + n
        if end > len(self._data):
            raise CBORDecodeError("Unexpected end of CBOR input.")
        chunk = self._data[self._pos : end]
        self._pos = end
        return chunk

    def peek_byte(self) -> int:
        if self._pos >= len(self._data):
            raise CBORDecodeError("Unexpected end of CBOR input.")
        return self._data[self._pos]

    def read_head(self) -> tuple[int, int]:
        """For indefinite-length items the argument is returned as ``-1``."""
        major, _ai, arg = self.read_head_ai()
        return major, arg

    def read_head_ai(self) -> tuple[int, int, int]:
        """The additional-info byte is needed to recover a float's width, since the
        argument alone does not carry it. For indefinite-length items the argument is
        returned as ``-1``.
        """
        initial = self._take(1)[0]
        major = initial >> 5
        ai = initial & 0x1F
        if ai < _W_1BYTE:
            return major, ai, ai
        if ai == _W_1BYTE:
            return major, ai, self._take(1)[0]
        if ai == _W_2BYTE:
            return major, ai, int.from_bytes(self._take(2), "big")
        if ai == _W_4BYTE:
            return major, ai, int.from_bytes(self._take(4), "big")
        if ai == _W_8BYTE:
            return major, ai, int.from_bytes(self._take(8), "big")
        if ai == _INDEFINITE:
            return major, ai, -1
        raise CBORDecodeError(f"Reserved additional-information value: {ai}")

    def take(self, n: int) -> bytes:
        return self._take(n)

    def at_break(self) -> bool:
        return self._pos < len(self._data) and self._data[self._pos] == _BREAK

    def consume_break(self) -> None:
        self._take(1)


class CBORShapeDeserializer(ShapeDeserializer):
    def __init__(self, source: BytesReader, settings: CBORSettings) -> None:
        self._settings = settings
        self._cursor = _Cursor(source.read())

    def _expect(self, major: int) -> int:
        found_major, arg = self._cursor.read_head()
        while found_major == _MAJOR_TAG:
            found_major, arg = self._cursor.read_head()
        if found_major != major:
            raise CBORDecodeError(
                f"Expected CBOR major type {major}, found {found_major}."
            )
        return arg

    def read_struct(
        self,
        schema: "Schema",
        consumer: Callable[["Schema", "ShapeDeserializer"], None],
    ) -> None:
        count = self._expect(_MAJOR_MAP)
        members = schema.members

        def read_pair() -> None:
            key = self._read_text()
            member = members.get(key)
            if member is None:
                # Unrecognized member: skip its value to stay aligned.
                self._skip_value()
            elif self.is_null():
                # A null member value is equivalent to an absent member.
                self.read_null()
            else:
                consumer(member, self)

        if count == -1:
            while not self._cursor.at_break():
                read_pair()
            self._cursor.consume_break()
        else:
            for _ in range(count):
                read_pair()

    def read_list(
        self, schema: "Schema", consumer: Callable[["ShapeDeserializer"], None]
    ) -> None:
        count = self._expect(_MAJOR_ARRAY)
        if count == -1:
            while not self._cursor.at_break():
                consumer(self)
            self._cursor.consume_break()
        else:
            for _ in range(count):
                consumer(self)

    def read_map(
        self,
        schema: "Schema",
        consumer: Callable[[str, "ShapeDeserializer"], None],
    ) -> None:
        count = self._expect(_MAJOR_MAP)
        if count == -1:
            while not self._cursor.at_break():
                key = self._read_text()
                consumer(key, self)
            self._cursor.consume_break()
        else:
            for _ in range(count):
                key = self._read_text()
                consumer(key, self)

    # --- scalars ------------------------------------------------------------

    def is_null(self) -> bool:
        initial = self._cursor.peek_byte()
        return initial == ((_MAJOR_SIMPLE << 5) | _SIMPLE_NULL)

    def read_null(self) -> None:
        major, arg = self._cursor.read_head()
        if major != _MAJOR_SIMPLE or arg != _SIMPLE_NULL:
            raise CBORDecodeError("Expected CBOR null.")

    def read_boolean(self, schema: "Schema") -> bool:
        major, arg = self._cursor.read_head()
        if major != _MAJOR_SIMPLE or arg not in (_SIMPLE_FALSE, _SIMPLE_TRUE):
            raise CBORDecodeError("Expected CBOR boolean.")
        return arg == _SIMPLE_TRUE

    def read_blob(self, schema: "Schema") -> bytes:
        return self._read_string_bytes(_MAJOR_BYTES)

    def read_integer(self, schema: "Schema") -> int:
        major, arg = self._cursor.read_head()
        if major == _MAJOR_UINT:
            return arg
        if major == _MAJOR_NEGINT:
            return -1 - arg
        raise CBORDecodeError(f"Expected CBOR integer, found major type {major}.")

    def read_float(self, schema: "Schema") -> float:
        major, ai, arg = self._cursor.read_head_ai()
        if major != _MAJOR_SIMPLE:
            raise CBORDecodeError("Expected CBOR float.")
        # read_head_ai consumed the payload as a big-endian int, so the argument value
        # IS the raw IEEE bit pattern; reinterpret it by the width the ai byte encodes.
        if ai == _W_8BYTE:  # double
            return _struct.unpack(">d", arg.to_bytes(8, "big"))[0]
        if ai == _W_4BYTE:  # single
            return _struct.unpack(">f", arg.to_bytes(4, "big"))[0]
        if ai == _W_2BYTE:  # half
            return _decode_half(arg.to_bytes(2, "big"))
        raise CBORDecodeError(f"Unexpected float additional-info: {ai}.")

    def read_big_integer(self, schema: "Schema") -> int:
        major, tag = self._cursor.read_head()
        if major != _MAJOR_TAG or tag not in (
            _TAG_UNSIGNED_BIGNUM,
            _TAG_NEGATIVE_BIGNUM,
        ):
            raise CBORDecodeError("Expected CBOR bignum tag.")
        magnitude = int.from_bytes(self.read_blob(schema), "big")
        return magnitude if tag == _TAG_UNSIGNED_BIGNUM else -1 - magnitude

    def read_big_decimal(self, schema: "Schema") -> Decimal:
        major, tag = self._cursor.read_head()
        if major != _MAJOR_TAG or tag != _TAG_DECIMAL_FRACTION:
            raise CBORDecodeError("Expected CBOR decimal-fraction tag.")
        count = self._expect(_MAJOR_ARRAY)
        if count != 2:
            raise CBORDecodeError("Decimal fraction must be a 2-element array.")
        exponent = self.read_integer(schema)
        mantissa = self.read_integer(schema)
        return Decimal(mantissa).scaleb(exponent)

    def read_string(self, schema: "Schema") -> str:
        return self._read_text()

    def read_document(self, schema: "Schema") -> "Document":
        raise NotImplementedError(
            "The rpcv2Cbor protocol does not support document types."
        )

    def read_timestamp(self, schema: "Schema") -> datetime.datetime:
        major, tag = self._cursor.read_head()
        if major != _MAJOR_TAG or tag != _TAG_EPOCH:
            raise CBORDecodeError("Expected CBOR epoch-timestamp tag.")
        # The tagged value is an int or float number of epoch seconds.
        peek_major = self._cursor.peek_byte() >> 5
        if peek_major in (_MAJOR_UINT, _MAJOR_NEGINT):
            seconds: float = self.read_integer(schema)
        else:
            seconds = self.read_float(schema)
        return datetime.datetime.fromtimestamp(seconds, tz=datetime.UTC)

    def _read_text(self) -> str:
        return self._read_string_bytes(_MAJOR_TEXT).decode("utf-8")

    def _read_string_bytes(self, major: int) -> bytes:
        """An indefinite-length string (RFC 8949 §3.2.3) is a sequence of definite-length
        chunks of the same major type, terminated by a break.
        """
        found_major, arg = self._cursor.read_head()
        while found_major == _MAJOR_TAG:
            found_major, arg = self._cursor.read_head()
        if found_major != major:
            raise CBORDecodeError(
                f"Expected CBOR major type {major}, found {found_major}."
            )
        if arg != -1:
            return self._cursor.take(arg)
        chunks = bytearray()
        while not self._cursor.at_break():
            chunk_major, chunk_len = self._cursor.read_head()
            if chunk_major != major:
                raise CBORDecodeError(
                    "Indefinite-length string chunk has mismatched major type."
                )
            chunks += self._cursor.take(chunk_len)
        self._cursor.consume_break()
        return bytes(chunks)

    def _skip_value(self) -> None:
        major, arg = self._cursor.read_head()
        if major in (_MAJOR_UINT, _MAJOR_NEGINT):
            return
        if major in (_MAJOR_BYTES, _MAJOR_TEXT):
            self._cursor.take(arg)
        elif major == _MAJOR_ARRAY:
            if arg == -1:
                while not self._cursor.at_break():
                    self._skip_value()
                self._cursor.consume_break()
            else:
                for _ in range(arg):
                    self._skip_value()
        elif major == _MAJOR_MAP:
            if arg == -1:
                while not self._cursor.at_break():
                    self._skip_value()
                    self._skip_value()
                self._cursor.consume_break()
            else:
                for _ in range(arg):
                    self._skip_value()
                    self._skip_value()
        elif major == _MAJOR_TAG:
            self._skip_value()
        elif major == _MAJOR_SIMPLE:
            if arg == _W_2BYTE:
                self._cursor.take(2)
            elif arg == _W_4BYTE:
                self._cursor.take(4)
            elif arg == _W_8BYTE:
                self._cursor.take(8)


def _decode_half(data: bytes) -> float:
    """Decodes an IEEE 754 half-precision float, implementing RFC 8949 Appendix D."""
    (bits,) = _struct.unpack(">H", data)
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
