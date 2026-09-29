#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""CBOR shape deserializer."""

import datetime
import struct as _struct
from collections.abc import Callable
from decimal import Decimal
from typing import override

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

# Initial byte of a CBOR null (major 7, simple value 22).
_NULL_BYTE = (_MAJOR_SIMPLE << 5) | _SIMPLE_NULL


class CBORDecodeError(SmithyError):
    pass


class CBORShapeDeserializer(ShapeDeserializer):
    def __init__(self, source: BytesReader, settings: CBORSettings) -> None:
        self._settings = settings
        self._data = source.read()
        self._len: int = len(self._data)
        self._pos: int = 0

    @override
    def read_struct(
        self,
        schema: Schema,
        consumer: Callable[[Schema, ShapeDeserializer], None],
    ) -> None:
        count = self._expect(_MAJOR_MAP)
        members_get = schema.members.get
        cursor = self
        read_text = self._read_text
        skip_value = self._skip_value
        read_null = self.read_null

        indefinite = count == -1
        remaining = count
        while True:
            if indefinite:
                if cursor._at_break():
                    cursor._consume_break()
                    break
            else:
                if remaining <= 0:
                    break
                remaining -= 1
            key = read_text()
            member = members_get(key)
            if member is None:
                skip_value()
            elif cursor._at_null():
                read_null()
            else:
                consumer(member, self)

    @override
    def read_list(
        self, schema: Schema, consumer: Callable[[ShapeDeserializer], None]
    ) -> None:
        count = self._expect(_MAJOR_ARRAY)
        if count == -1:
            while not self._at_break():
                consumer(self)
            self._consume_break()
        else:
            for _ in range(count):
                consumer(self)

    @override
    def read_map(
        self,
        schema: Schema,
        consumer: Callable[[str, ShapeDeserializer], None],
    ) -> None:
        count = self._expect(_MAJOR_MAP)
        if count == -1:
            while not self._at_break():
                key = self._read_text()
                consumer(key, self)
            self._consume_break()
        else:
            for _ in range(count):
                key = self._read_text()
                consumer(key, self)

    @override
    def is_null(self) -> bool:
        initial = self._peek_byte()
        return initial == ((_MAJOR_SIMPLE << 5) | _SIMPLE_NULL)

    @override
    def read_null(self) -> None:
        major, arg = self._read_head()
        if major != _MAJOR_SIMPLE or arg != _SIMPLE_NULL:
            raise CBORDecodeError("Expected CBOR null.")

    @override
    def read_boolean(self, schema: Schema) -> bool:
        major, arg = self._read_head()
        if major != _MAJOR_SIMPLE or arg not in (_SIMPLE_FALSE, _SIMPLE_TRUE):
            raise CBORDecodeError("Expected CBOR boolean.")
        return arg == _SIMPLE_TRUE

    @override
    def read_blob(self, schema: Schema) -> bytes:
        return self._read_string_bytes(_MAJOR_BYTES)

    @override
    def read_integer(self, schema: Schema) -> int:
        major, arg = self._read_head()
        if major == _MAJOR_UINT:
            return arg
        if major == _MAJOR_NEGINT:
            return -1 - arg
        raise CBORDecodeError(f"Expected CBOR integer, found major type {major}.")

    @override
    def read_float(self, schema: Schema) -> float:
        major, add_info, arg = self._read_head_add_info()
        if major != _MAJOR_SIMPLE:
            raise CBORDecodeError("Expected CBOR float.")
        if add_info == _W_8BYTE:  # double
            return _struct.unpack(">d", arg.to_bytes(8, "big"))[0]
        if add_info == _W_4BYTE:  # single
            return _struct.unpack(">f", arg.to_bytes(4, "big"))[0]
        if add_info == _W_2BYTE:  # half
            return _decode_half(arg.to_bytes(2, "big"))
        raise CBORDecodeError(f"Unexpected float additional-info: {add_info}.")

    @override
    def read_big_integer(self, schema: Schema) -> int:
        major, tag = self._read_head()
        if major != _MAJOR_TAG or tag not in (
            _TAG_UNSIGNED_BIGNUM,
            _TAG_NEGATIVE_BIGNUM,
        ):
            raise CBORDecodeError("Expected CBOR bignum tag.")
        magnitude = int.from_bytes(self.read_blob(schema), "big")
        return magnitude if tag == _TAG_UNSIGNED_BIGNUM else -1 - magnitude

    @override
    def read_big_decimal(self, schema: Schema) -> Decimal:
        major, tag = self._read_head()
        if major != _MAJOR_TAG or tag != _TAG_DECIMAL_FRACTION:
            raise CBORDecodeError("Expected CBOR decimal-fraction tag.")
        count = self._expect(_MAJOR_ARRAY)
        if count != 2:
            raise CBORDecodeError("Decimal fraction must be a 2-element array.")
        exponent = self.read_integer(schema)
        mantissa = self.read_integer(schema)
        return Decimal(mantissa).scaleb(exponent)

    @override
    def read_string(self, schema: Schema) -> str:
        return self._read_text()

    @override
    def read_document(self, schema: Schema) -> Document:
        raise NotImplementedError(
            "This version of the Smithy RPCv2 CBOR protocol does not support document types."
        )

    @override
    def read_timestamp(self, schema: Schema) -> datetime.datetime:
        major, tag = self._read_head()
        if major != _MAJOR_TAG or tag != _TAG_EPOCH:
            raise CBORDecodeError("Expected CBOR epoch-timestamp tag.")
        # The tagged value is an int or float number of epoch seconds.
        peek_major = self._peek_byte() >> 5
        if peek_major in (_MAJOR_UINT, _MAJOR_NEGINT):
            seconds: float = self.read_integer(schema)
        else:
            seconds = self.read_float(schema)
        return datetime.datetime.fromtimestamp(seconds, tz=datetime.UTC)

    def _read_text(self) -> str:
        text = self._try_read_text()
        if text is not None:
            return text
        return self._read_string_bytes(_MAJOR_TEXT).decode("utf-8")

    def _read_string_bytes(self, major: int) -> bytes:
        """An indefinite-length string (RFC 8949 §3.2.3) is a sequence of definite-length
        chunks of the same major type, terminated by a break.
        """
        found_major, arg = self._read_head()
        while found_major == _MAJOR_TAG:
            found_major, arg = self._read_head()
        if found_major != major:
            raise CBORDecodeError(
                f"Expected CBOR major type {major}, found {found_major}."
            )
        if arg != -1:
            return self._take(arg)
        chunks = bytearray()
        while not self._at_break():
            chunk_major, chunk_len = self._read_head()
            if chunk_major != major:
                raise CBORDecodeError(
                    "Indefinite-length string chunk has mismatched major type."
                )
            chunks += self._take(chunk_len)
        self._consume_break()
        return bytes(chunks)

    def _skip_value(self) -> None:
        """e.g. unrecognized member."""
        major, arg = self._read_head()
        if major in (_MAJOR_UINT, _MAJOR_NEGINT):
            return
        if major in (_MAJOR_BYTES, _MAJOR_TEXT):
            self._take(arg)
        elif major == _MAJOR_ARRAY:
            if arg == -1:
                while not self._at_break():
                    self._skip_value()
                self._consume_break()
            else:
                for _ in range(arg):
                    self._skip_value()
        elif major == _MAJOR_MAP:
            if arg == -1:
                while not self._at_break():
                    self._skip_value()
                    self._skip_value()
                self._consume_break()
            else:
                for _ in range(arg):
                    self._skip_value()
                    self._skip_value()
        elif major == _MAJOR_TAG:
            self._skip_value()
        elif major == _MAJOR_SIMPLE:
            if arg == _W_2BYTE:
                self._take(2)
            elif arg == _W_4BYTE:
                self._take(4)
            elif arg == _W_8BYTE:
                self._take(8)

    def _expect(self, major: int) -> int:
        found_major, arg = self._read_head()
        while found_major == _MAJOR_TAG:
            found_major, arg = self._read_head()
        if found_major != major:
            raise CBORDecodeError(
                f"Expected CBOR major type {major}, found {found_major}."
            )
        return arg

    def _take(self, n: int) -> bytes:
        end = self._pos + n
        if end > self._len:
            raise CBORDecodeError("Unexpected end of CBOR input.")
        chunk = self._data[self._pos : end]
        self._pos = end
        return chunk

    def _peek_byte(self) -> int:
        pos = self._pos
        if pos >= self._len:
            raise CBORDecodeError("Unexpected end of CBOR input.")
        return self._data[pos]

    def _read_head(self) -> tuple[int, int]:
        """For indefinite-length items the argument is returned as ``-1``."""
        data = self._data
        pos = self._pos
        if pos >= self._len:
            raise CBORDecodeError("Unexpected end of CBOR input.")
        initial = data[pos]
        major = initial >> 5
        add_info = initial & 0x1F
        if add_info < _W_1BYTE:
            self._pos = pos + 1
            return major, add_info
        if add_info == _W_1BYTE:
            end = pos + 2
            if end > self._len:
                raise CBORDecodeError("Unexpected end of CBOR input.")
            self._pos = end
            return major, data[pos + 1]
        if add_info == _W_2BYTE:
            width = 2
        elif add_info == _W_4BYTE:
            width = 4
        elif add_info == _W_8BYTE:
            width = 8
        elif add_info == _INDEFINITE:
            self._pos = pos + 1
            return major, -1
        else:
            raise CBORDecodeError(f"Reserved additional-information value: {add_info}")
        start = pos + 1
        end = start + width
        if end > self._len:
            raise CBORDecodeError("Unexpected end of CBOR input.")
        self._pos = end
        return major, int.from_bytes(data[start:end], "big")

    def _read_head_add_info(self) -> tuple[int, int, int]:
        """Returns (major, add_info, arg): major type, raw additional-info bits, and the
        decoded argument. add_info is kept to recover a float's width, which arg alone
        loses; arg is -1 for an indefinite-length item.
        """
        data = self._data
        pos = self._pos
        if pos >= self._len:
            raise CBORDecodeError("Unexpected end of CBOR input.")
        initial = data[pos]
        major = initial >> 5
        add_info = initial & 0x1F
        if add_info < _W_1BYTE:
            self._pos = pos + 1
            return major, add_info, add_info
        if add_info == _W_1BYTE:
            end = pos + 2
            if end > self._len:
                raise CBORDecodeError("Unexpected end of CBOR input.")
            self._pos = end
            return major, add_info, data[pos + 1]
        if add_info == _W_2BYTE:
            width = 2
        elif add_info == _W_4BYTE:
            width = 4
        elif add_info == _W_8BYTE:
            width = 8
        elif add_info == _INDEFINITE:
            self._pos = pos + 1
            return major, add_info, -1
        else:
            raise CBORDecodeError(f"Reserved additional-information value: {add_info}")
        start = pos + 1
        end = start + width
        if end > self._len:
            raise CBORDecodeError("Unexpected end of CBOR input.")
        self._pos = end
        return major, add_info, int.from_bytes(data[start:end], "big")

    def _at_break(self) -> bool:
        pos = self._pos
        return pos < self._len and self._data[pos] == _BREAK

    def _consume_break(self) -> None:
        self._take(1)

    def _try_read_text(self) -> str | None:
        """Fast path for a definite-length text string (major 3, no tag prefix), which
        is every struct key and every string value in practice. Returns ``None`` when
        the next item is not such a string, so the caller falls back to the general path.
        """
        data = self._data
        pos = self._pos
        if pos >= self._len:
            return None
        initial = data[pos]
        if (initial >> 5) != _MAJOR_TEXT:
            return None
        add_info = initial & 0x1F
        if add_info < _W_1BYTE:
            start = pos + 1
            end = start + add_info
        elif add_info == _W_1BYTE and pos + 1 < self._len:
            length = data[pos + 1]
            start = pos + 2
            end = start + length
        else:
            return None
        if end > self._len:
            return None
        self._pos = end
        return data[start:end].decode("utf-8")

    def _at_null(self) -> bool:
        pos = self._pos
        return pos < self._len and self._data[pos] == _NULL_BYTE


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
