#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest
from smithy_cbor import CBORCodec
from smithy_core.deserializers import ShapeDeserializer
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


def _decoder(data: bytes) -> ShapeDeserializer:
    return CBORCodec().create_deserializer(data)


@pytest.mark.parametrize("value", [0, 1, 23, 24, 1000, -1, -24, -1000, 2**53])
def test_integer_roundtrip(value: int) -> None:
    sink_bytes = _encode(lambda s: s.write_integer(INTEGER, value))
    assert _decoder(sink_bytes).read_integer(INTEGER) == value


@pytest.mark.parametrize("value", [True, False])
def test_boolean_roundtrip(value: bool) -> None:
    data = _encode(lambda s: s.write_boolean(BOOLEAN, value))
    assert _decoder(data).read_boolean(BOOLEAN) is value


def test_null_roundtrip() -> None:
    data = _encode(lambda s: s.write_null(STRING))
    d = _decoder(data)
    assert d.is_null() is True
    d.read_null()


def test_string_roundtrip() -> None:
    data = _encode(lambda s: s.write_string(STRING, "héllo"))
    assert _decoder(data).read_string(STRING) == "héllo"


def test_blob_roundtrip() -> None:
    data = _encode(lambda s: s.write_blob(BLOB, b"\x00\xff\x10"))
    assert _decoder(data).read_blob(BLOB) == b"\x00\xff\x10"


@pytest.mark.parametrize("value", [0.0, 1.5, -2.25, 3.141592653589793])
def test_double_roundtrip(value: float) -> None:
    data = _encode(lambda s: s.write_float(DOUBLE, value))
    assert _decoder(data).read_float(DOUBLE) == value


@pytest.mark.parametrize("value", [2**64, -(2**70), 12345678901234567890])
def test_big_integer_roundtrip(value: int) -> None:
    data = _encode(lambda s: s.write_big_integer(BIG_INTEGER, value))
    assert _decoder(data).read_big_integer(BIG_INTEGER) == value


@pytest.mark.parametrize("value", ["273.15", "-0.001", "12345.6789"])
def test_big_decimal_roundtrip(value: str) -> None:
    dec = Decimal(value)
    data = _encode(lambda s: s.write_big_decimal(BIG_DECIMAL, dec))
    assert _decoder(data).read_big_decimal(BIG_DECIMAL) == dec


def test_timestamp_roundtrip() -> None:
    ts = datetime(2026, 9, 21, 20, 0, 0, tzinfo=UTC)
    data = _encode(lambda s: s.write_timestamp(TIMESTAMP, ts))
    assert _decoder(data).read_timestamp(TIMESTAMP) == ts


def test_list_roundtrip() -> None:
    schema = Schema.collection(
        id=ShapeID("smithy.example#IntList"),
        shape_type=ShapeType.LIST,
        members={"member": {"target": INTEGER}},
    )

    def write(s: Any) -> None:
        with s.begin_list(schema, 3) as ls:
            for v in (1, 2, 3):
                ls.write_integer(INTEGER, v)

    data = _encode(write)
    out: list[int] = []
    _decoder(data).read_list(schema, lambda d: out.append(d.read_integer(INTEGER)))
    assert out == [1, 2, 3]


def test_map_roundtrip() -> None:
    schema = Schema.collection(
        id=ShapeID("smithy.example#IntMap"),
        shape_type=ShapeType.MAP,
        members={"key": {"target": STRING}, "value": {"target": INTEGER}},
    )

    def write(s: ShapeSerializer) -> None:
        with s.begin_map(schema, 2) as ms:
            ms.entry("a", lambda vs: vs.write_integer(INTEGER, 1))
            ms.entry("b", lambda vs: vs.write_integer(INTEGER, 2))

    data = _encode(write)
    out: dict[str, int] = {}
    _decoder(data).read_map(
        schema, lambda k, d: out.__setitem__(k, d.read_integer(INTEGER))
    )
    assert out == {"a": 1, "b": 2}


def test_struct_roundtrip() -> None:
    schema = Schema.collection(
        id=ShapeID("smithy.example#Point"),
        members={"x": {"target": INTEGER}, "y": {"target": INTEGER}},
    )

    def write(s: Any) -> None:
        with s.begin_struct(schema) as st:
            st.write_integer(schema.members["x"], 10)
            st.write_integer(schema.members["y"], 20)

    data = _encode(write)
    out: dict[str, int] = {}
    _decoder(data).read_struct(
        schema, lambda m, d: out.__setitem__(m.expect_member_name(), d.read_integer(m))
    )
    assert out == {"x": 10, "y": 20}


def test_struct_skips_unknown_member() -> None:
    # Encode a 2-member map, but decode against a schema that only knows "x".
    schema = Schema.collection(
        id=ShapeID("smithy.example#Point"),
        members={"x": {"target": INTEGER}, "y": {"target": INTEGER}},
    )
    partial = Schema.collection(
        id=ShapeID("smithy.example#Point"),
        members={"x": {"target": INTEGER}},
    )

    def write(s: Any) -> None:
        with s.begin_struct(schema) as st:
            st.write_integer(schema.members["x"], 10)
            st.write_integer(schema.members["y"], 20)

    data = _encode(write)
    out: dict[str, int] = {}
    _decoder(data).read_struct(
        partial, lambda m, d: out.__setitem__(m.expect_member_name(), d.read_integer(m))
    )
    assert out == {"x": 10}


# Local import to avoid a circular helper module; mirrors the serializer test helper.
def _encode(writer: Callable[[ShapeSerializer], object]) -> bytes:
    from io import BytesIO

    sink = BytesIO()
    serializer = CBORCodec().create_serializer(sink)
    writer(serializer)
    serializer.flush()
    return sink.getvalue()
