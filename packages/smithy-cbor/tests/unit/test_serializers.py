#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal
from io import BytesIO
from typing import Any

import pytest
from smithy_cbor import CBORCodec
from smithy_core.prelude import (
    BIG_DECIMAL,
    BIG_INTEGER,
    BLOB,
    BOOLEAN,
    DOUBLE,
    INTEGER,
    STRING,
    TIMESTAMP,
)
from smithy_core.schemas import Schema
from smithy_core.serializers import ShapeSerializer
from smithy_core.shapes import ShapeID, ShapeType


def _encode(writer: Callable[[ShapeSerializer], object]) -> bytes:
    sink = BytesIO()
    serializer = CBORCodec().create_serializer(sink)
    writer(serializer)
    serializer.flush()
    return sink.getvalue()


def test_media_type() -> None:
    assert CBORCodec().media_type == "application/cbor"


# (value, expected initial bytes) -- RFC 8949 known vectors.
@pytest.mark.parametrize(
    "value, expected",
    [
        (0, b"\x00"),
        (1, b"\x01"),
        (23, b"\x17"),
        (24, b"\x18\x18"),
        (1000, b"\x19\x03\xe8"),
        (-1, b"\x20"),
        (-24, b"\x37"),
        (-1000, b"\x39\x03\xe7"),
    ],
)
def test_integer_vectors(value: int, expected: bytes) -> None:
    assert _encode(lambda s: s.write_integer(INTEGER, value)) == expected


def test_boolean_vectors() -> None:
    assert _encode(lambda s: s.write_boolean(BOOLEAN, True)) == b"\xf5"
    assert _encode(lambda s: s.write_boolean(BOOLEAN, False)) == b"\xf4"


def test_null_vector() -> None:
    assert _encode(lambda s: s.write_null(STRING)) == b"\xf6"


def test_string_vector() -> None:
    assert _encode(lambda s: s.write_string(STRING, "IETF")) == b"\x64IETF"


def test_blob_vector() -> None:
    assert _encode(lambda s: s.write_blob(BLOB, b"\x01\x02\x03\x04")) == (
        b"\x44\x01\x02\x03\x04"
    )


def test_double_vector() -> None:
    assert _encode(lambda s: s.write_float(DOUBLE, 1.5)) == (
        b"\xfb\x3f\xf8\x00\x00\x00\x00\x00\x00"
    )


def test_big_integer_vector() -> None:
    got = _encode(lambda s: s.write_big_integer(BIG_INTEGER, 2**64))
    assert got == b"\xc2\x49\x01\x00\x00\x00\x00\x00\x00\x00\x00"


def test_big_decimal_vector() -> None:
    got = _encode(lambda s: s.write_big_decimal(BIG_DECIMAL, Decimal("273.15")))
    assert got == b"\xc4\x82\x21\x19\x6a\xb3"


def test_timestamp_vector() -> None:
    ts = datetime(1970, 1, 1, tzinfo=UTC)
    got = _encode(lambda s: s.write_timestamp(TIMESTAMP, ts))
    assert got == b"\xc1\xfb\x00\x00\x00\x00\x00\x00\x00\x00"


def test_list_vector() -> None:
    schema = Schema.collection(
        id=ShapeID("smithy.example#IntList"),
        shape_type=ShapeType.LIST,
        members={"member": {"target": INTEGER}},
    )

    def write(s: Any) -> None:
        with s.begin_list(schema, 3) as ls:
            ls.write_integer(INTEGER, 1)
            ls.write_integer(INTEGER, 2)
            ls.write_integer(INTEGER, 3)

    assert _encode(write) == b"\x9f\x01\x02\x03\xff"


def test_struct_vector() -> None:
    schema = Schema.collection(
        id=ShapeID("smithy.example#Point"),
        members={"x": {"target": INTEGER}, "y": {"target": INTEGER}},
    )

    def write(s: Any) -> None:
        with s.begin_struct(schema) as st:
            st.write_integer(schema.members["x"], 1)
            st.write_integer(schema.members["y"], 2)

    assert _encode(write) == b"\xbf\x61\x78\x01\x61\x79\x02\xff"
