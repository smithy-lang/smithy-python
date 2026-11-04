# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Round-trip and grammar-conformance tests for big numbers under rpcv2Json.

Property 1: Big-number round trip.
Property 2: Grammar conformance of output.

**Validates: Requirements 2.1, 2.2, 2.5, 3.1, 3.2, 3.3**
"""

import json
import re
from decimal import Decimal
from io import BytesIO

import pytest
from smithy_core.deserializers import ShapeDeserializer
from smithy_core.prelude import BIG_DECIMAL, BIG_INTEGER, STRING
from smithy_core.schemas import Schema
from smithy_core.shapes import ShapeID, ShapeType

from . import SerdeShape, rpcv2_json_codec

# Grammars from the rpcv2Json specification, written independently of the
# implementation's private patterns.
BIG_INTEGER_GRAMMAR = re.compile(r"-?(?:0|[1-9][0-9]*)")
BIG_DECIMAL_GRAMMAR = re.compile(
    r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?"
)

BIG_INTEGER_LIST_SCHEMA = Schema.collection(
    id=ShapeID("smithy.example#BigIntegerList"),
    shape_type=ShapeType.LIST,
    members={"member": {"target": BIG_INTEGER}},
)
BIG_DECIMAL_LIST_SCHEMA = Schema.collection(
    id=ShapeID("smithy.example#BigDecimalList"),
    shape_type=ShapeType.LIST,
    members={"member": {"target": BIG_DECIMAL}},
)
BIG_INTEGER_MAP_SCHEMA = Schema.collection(
    id=ShapeID("smithy.example#BigIntegerMap"),
    shape_type=ShapeType.MAP,
    members={"key": {"target": STRING}, "value": {"target": BIG_INTEGER}},
)
BIG_DECIMAL_MAP_SCHEMA = Schema.collection(
    id=ShapeID("smithy.example#BigDecimalMap"),
    shape_type=ShapeType.MAP,
    members={"key": {"target": STRING}, "value": {"target": BIG_DECIMAL}},
)

BIG_INTEGER_CASES: list[tuple[int, str]] = [
    (0, "0"),
    (1, "1"),
    (-1, "-1"),
    (-123, "-123"),
    (123456789012345678901234567890, "123456789012345678901234567890"),
    (-123456789012345678901234567890, "-123456789012345678901234567890"),
]

BIG_DECIMAL_CASES: list[tuple[Decimal, str]] = [
    (Decimal(0), "0"),
    (Decimal("-0"), "-0"),
    (Decimal("1.5"), "1.5"),
    (Decimal("-1.5"), "-1.5"),
    (Decimal("0.001"), "0.001"),
    (Decimal("1.50"), "1.50"),
    (Decimal("1E+3"), "1E+3"),
    (Decimal("1E-7"), "1E-7"),
    (Decimal("0.100000000000000000000001"), "0.100000000000000000000001"),
    (
        Decimal("-123456789012345678901234567890.123456789"),
        "-123456789012345678901234567890.123456789",
    ),
]


def _json_string(raw: str) -> bytes:
    return f'"{raw}"'.encode()


def _assert_same_decimal(actual: Decimal, expected: Decimal) -> None:
    # Equal digits and exponent, not just numeric equality.
    assert actual.as_tuple() == expected.as_tuple()


def _serialize_list(schema: Schema, values: list[int] | list[Decimal]) -> bytes:
    sink = BytesIO()
    serializer = rpcv2_json_codec().create_serializer(sink)
    member = schema.members["member"]
    with serializer.begin_list(schema, len(values)) as ls:
        for value in values:
            if isinstance(value, Decimal):
                ls.write_big_decimal(member, value)
            else:
                ls.write_big_integer(member, value)
    serializer.flush()
    return sink.getvalue()


def _serialize_map(
    schema: Schema, values: dict[str, int] | dict[str, Decimal]
) -> bytes:
    sink = BytesIO()
    serializer = rpcv2_json_codec().create_serializer(sink)
    member = schema.members["value"]
    with serializer.begin_map(schema, len(values)) as ms:
        for key, value in values.items():
            if isinstance(value, Decimal):
                ms.entry(key, lambda vs, v=value: vs.write_big_decimal(member, v))
            else:
                ms.entry(key, lambda vs, v=value: vs.write_big_integer(member, v))
    serializer.flush()
    return sink.getvalue()


# Top level


@pytest.mark.parametrize("value, raw", BIG_INTEGER_CASES)
def test_top_level_big_integer_round_trip(value: int, raw: str) -> None:
    codec = rpcv2_json_codec()
    sink = BytesIO()
    serializer = codec.create_serializer(sink)
    serializer.write_big_integer(BIG_INTEGER, value)
    serializer.flush()
    actual = sink.getvalue()

    assert actual == _json_string(raw)
    written = json.loads(actual)
    assert isinstance(written, str)
    assert BIG_INTEGER_GRAMMAR.fullmatch(written)

    assert codec.create_deserializer(actual).read_big_integer(BIG_INTEGER) == value


@pytest.mark.parametrize("value, raw", BIG_DECIMAL_CASES)
def test_top_level_big_decimal_round_trip(value: Decimal, raw: str) -> None:
    codec = rpcv2_json_codec()
    sink = BytesIO()
    serializer = codec.create_serializer(sink)
    serializer.write_big_decimal(BIG_DECIMAL, value)
    serializer.flush()
    actual = sink.getvalue()

    assert actual == _json_string(raw)
    written = json.loads(actual)
    assert isinstance(written, str)
    assert BIG_DECIMAL_GRAMMAR.fullmatch(written)

    result = codec.create_deserializer(actual).read_big_decimal(BIG_DECIMAL)
    _assert_same_decimal(result, value)


# Struct members


@pytest.mark.parametrize("value, raw", BIG_INTEGER_CASES)
def test_struct_member_big_integer_round_trip(value: int, raw: str) -> None:
    codec = rpcv2_json_codec()
    shape = SerdeShape(big_integer_member=value)
    actual = codec.serialize(shape)

    assert actual == b'{"bigIntegerMember":' + _json_string(raw) + b"}"
    assert BIG_INTEGER_GRAMMAR.fullmatch(json.loads(actual)["bigIntegerMember"])

    assert codec.deserialize(actual, SerdeShape) == shape


@pytest.mark.parametrize("value, raw", BIG_DECIMAL_CASES)
def test_struct_member_big_decimal_round_trip(value: Decimal, raw: str) -> None:
    codec = rpcv2_json_codec()
    actual = codec.serialize(SerdeShape(big_decimal_member=value))

    assert actual == b'{"bigDecimalMember":' + _json_string(raw) + b"}"
    assert BIG_DECIMAL_GRAMMAR.fullmatch(json.loads(actual)["bigDecimalMember"])

    result = codec.deserialize(actual, SerdeShape).big_decimal_member
    assert result is not None
    _assert_same_decimal(result, value)


def test_nested_struct_member_round_trip() -> None:
    codec = rpcv2_json_codec()
    shape = SerdeShape(
        struct_member=SerdeShape(
            big_integer_member=123456789012345678901234567890,
            big_decimal_member=Decimal("0.100000000000000000000001"),
        )
    )
    actual = codec.serialize(shape)

    assert actual == (
        b'{"structMember":{"bigDecimalMember":"0.100000000000000000000001",'
        b'"bigIntegerMember":"123456789012345678901234567890"}}'
    )
    nested = json.loads(actual)["structMember"]
    assert BIG_DECIMAL_GRAMMAR.fullmatch(nested["bigDecimalMember"])
    assert BIG_INTEGER_GRAMMAR.fullmatch(nested["bigIntegerMember"])

    result = codec.deserialize(actual, SerdeShape)
    assert result.struct_member is not None
    assert result.struct_member.big_integer_member == 123456789012345678901234567890
    assert result.struct_member.big_decimal_member is not None
    _assert_same_decimal(
        result.struct_member.big_decimal_member,
        Decimal("0.100000000000000000000001"),
    )


# List elements


def test_list_element_big_integer_round_trip() -> None:
    values = [value for value, _ in BIG_INTEGER_CASES]
    actual = _serialize_list(BIG_INTEGER_LIST_SCHEMA, values)

    expected = b"[" + b",".join(_json_string(raw) for _, raw in BIG_INTEGER_CASES)
    assert actual == expected + b"]"
    for written in json.loads(actual):
        assert BIG_INTEGER_GRAMMAR.fullmatch(written)

    result: list[int] = []
    member = BIG_INTEGER_LIST_SCHEMA.members["member"]
    rpcv2_json_codec().create_deserializer(actual).read_list(
        BIG_INTEGER_LIST_SCHEMA,
        lambda d: result.append(d.read_big_integer(member)),
    )
    assert result == values


def test_list_element_big_decimal_round_trip() -> None:
    values = [value for value, _ in BIG_DECIMAL_CASES]
    actual = _serialize_list(BIG_DECIMAL_LIST_SCHEMA, values)

    expected = b"[" + b",".join(_json_string(raw) for _, raw in BIG_DECIMAL_CASES)
    assert actual == expected + b"]"
    for written in json.loads(actual):
        assert BIG_DECIMAL_GRAMMAR.fullmatch(written)

    result: list[Decimal] = []
    member = BIG_DECIMAL_LIST_SCHEMA.members["member"]
    rpcv2_json_codec().create_deserializer(actual).read_list(
        BIG_DECIMAL_LIST_SCHEMA,
        lambda d: result.append(d.read_big_decimal(member)),
    )
    assert len(result) == len(values)
    for actual_value, expected_value in zip(result, values):
        _assert_same_decimal(actual_value, expected_value)


# Map values


def test_map_value_big_integer_round_trip() -> None:
    values = {f"k{i}": value for i, (value, _) in enumerate(BIG_INTEGER_CASES)}
    actual = _serialize_map(BIG_INTEGER_MAP_SCHEMA, values)

    expected = b",".join(
        f'"k{i}":"{raw}"'.encode() for i, (_, raw) in enumerate(BIG_INTEGER_CASES)
    )
    assert actual == b"{" + expected + b"}"
    for written in json.loads(actual).values():
        assert BIG_INTEGER_GRAMMAR.fullmatch(written)

    result: dict[str, int] = {}
    member = BIG_INTEGER_MAP_SCHEMA.members["value"]

    def _read(key: str, d: ShapeDeserializer) -> None:
        result[key] = d.read_big_integer(member)

    rpcv2_json_codec().create_deserializer(actual).read_map(
        BIG_INTEGER_MAP_SCHEMA, _read
    )
    assert result == values


def test_map_value_big_decimal_round_trip() -> None:
    values = {f"k{i}": value for i, (value, _) in enumerate(BIG_DECIMAL_CASES)}
    actual = _serialize_map(BIG_DECIMAL_MAP_SCHEMA, values)

    expected = b",".join(
        f'"k{i}":"{raw}"'.encode() for i, (_, raw) in enumerate(BIG_DECIMAL_CASES)
    )
    assert actual == b"{" + expected + b"}"
    for written in json.loads(actual).values():
        assert BIG_DECIMAL_GRAMMAR.fullmatch(written)

    result: dict[str, Decimal] = {}
    member = BIG_DECIMAL_MAP_SCHEMA.members["value"]

    def _read(key: str, d: ShapeDeserializer) -> None:
        result[key] = d.read_big_decimal(member)

    rpcv2_json_codec().create_deserializer(actual).read_map(
        BIG_DECIMAL_MAP_SCHEMA, _read
    )
    assert result.keys() == values.keys()
    for key, expected_value in values.items():
        _assert_same_decimal(result[key], expected_value)
