# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Document tests for string-encoded big numbers (smithy.protocols#rpcv2Json)."""

from decimal import Decimal
from io import BytesIO
from typing import Any

import pytest
from smithy_core.documents import Document
from smithy_core.exceptions import ExpectationNotMetError
from smithy_core.prelude import BIG_DECIMAL, BIG_INTEGER, DOCUMENT
from smithy_core.schemas import Schema
from smithy_core.shapes import ShapeID, ShapeType
from smithy_json import JSONCodec, JSONDocument, JSONSettings
from smithy_json._private import JSONValueError

from . import rpcv2_json_codec

BIG_NUMBERS_SCHEMA = Schema.collection(
    id=ShapeID("smithy.example#BigNumbers"),
    members={
        "bigIntegerMember": {"target": BIG_INTEGER},
        "bigDecimalMember": {"target": BIG_DECIMAL},
    },
)

BIG_DECIMAL_LIST_SCHEMA = Schema.collection(
    id=ShapeID("smithy.example#BigDecimalList"),
    shape_type=ShapeType.LIST,
    members={"member": {"target": BIG_DECIMAL}},
)

SETTINGS = JSONSettings(document_class=JSONDocument, arbitrary_precision_as_string=True)


def _serialize_document(codec: JSONCodec, document: Document) -> bytes:
    sink = BytesIO()
    serializer = codec.create_serializer(sink)
    serializer.write_document(document._schema, document)  # type: ignore
    serializer.flush()
    return sink.getvalue()


@pytest.mark.parametrize(
    "given, expected",
    [
        # Typed big numbers are written as JSON strings.
        (Document(Decimal("1.1"), schema=BIG_DECIMAL), b'"1.1"'),
        (
            Document(Decimal("0.100000000000000000000001"), schema=BIG_DECIMAL),
            b'"0.100000000000000000000001"',
        ),
        (Document(Decimal("-1.50"), schema=BIG_DECIMAL), b'"-1.50"'),
        (Document(123, schema=BIG_INTEGER), b'"123"'),
        (
            Document(-123456789012345678901234567890, schema=BIG_INTEGER),
            b'"-123456789012345678901234567890"',
        ),
        # Property 4: untyped documents keep numbers as JSON numbers.
        (Document(Decimal("1.1"), schema=DOCUMENT), b"1.1"),
        (Document(123, schema=DOCUMENT), b"123"),
        (Document({"x": Decimal("1.5")}, schema=DOCUMENT), b'{"x":1.5}'),
        (Document([Decimal("1.5"), 2], schema=DOCUMENT), b"[1.5,2]"),
        # Typed members nested in structures and lists are strings.
        (
            Document(
                {"bigIntegerMember": 1, "bigDecimalMember": Decimal("2.5")},
                schema=BIG_NUMBERS_SCHEMA,
            ),
            b'{"bigIntegerMember":"1","bigDecimalMember":"2.5"}',
        ),
        (
            Document([Decimal("1.5"), Decimal("-0")], schema=BIG_DECIMAL_LIST_SCHEMA),
            b'["1.5","-0"]',
        ),
    ],
)
def test_serialize_documents_with_setting(given: Document, expected: bytes) -> None:
    """**Validates: Requirements 2.4, 4.4**"""
    assert _serialize_document(rpcv2_json_codec(), given) == expected


@pytest.mark.parametrize(
    "given, expected",
    [
        (Document(Decimal("1.1"), schema=BIG_DECIMAL), b"1.1"),
        (Document(123, schema=BIG_INTEGER), b"123"),
        (Document(Decimal("1.1"), schema=DOCUMENT), b"1.1"),
    ],
)
def test_serialize_documents_default_settings(given: Document, expected: bytes) -> None:
    assert _serialize_document(JSONCodec(), given) == expected


@pytest.mark.parametrize(
    "value, schema, expected",
    [
        ("123", BIG_INTEGER, 123),
        ("-0", BIG_INTEGER, 0),
        (
            "123456789012345678901234567890",
            BIG_INTEGER,
            123456789012345678901234567890,
        ),
        ("1.5", BIG_DECIMAL, Decimal("1.5")),
        ("-1.5e-3", BIG_DECIMAL, Decimal("-1.5e-3")),
        (
            "0.100000000000000000000001",
            BIG_DECIMAL,
            Decimal("0.100000000000000000000001"),
        ),
        ("123", BIG_DECIMAL, Decimal(123)),
    ],
)
def test_typed_document_parses_strings(
    value: str, schema: Schema, expected: int | Decimal
) -> None:
    document = JSONDocument(value, settings=SETTINGS, schema=schema)
    if schema.shape_type is ShapeType.BIG_INTEGER:
        assert document.as_integer() == expected
    else:
        actual = document.as_decimal()
        assert isinstance(actual, Decimal)
        assert actual == expected
        assert actual.as_tuple() == Decimal(value).as_tuple()

    as_value = document.as_value()
    assert as_value == expected
    assert type(as_value) is type(expected)


@pytest.mark.parametrize(
    "value, schema",
    [
        ("01", BIG_INTEGER),
        ("+1", BIG_INTEGER),
        (" 1", BIG_INTEGER),
        ("1.5", BIG_INTEGER),
        ("", BIG_INTEGER),
        ("NaN", BIG_INTEGER),
        ("1.", BIG_DECIMAL),
        (".5", BIG_DECIMAL),
        ("NaN", BIG_DECIMAL),
        ("Infinity", BIG_DECIMAL),
        ("", BIG_DECIMAL),
        ("1.5 ", BIG_DECIMAL),
    ],
)
def test_typed_document_rejects_invalid_strings(value: str, schema: Schema) -> None:
    document = JSONDocument(value, settings=SETTINGS, schema=schema)
    with pytest.raises(JSONValueError):
        if schema.shape_type is ShapeType.BIG_INTEGER:
            document.as_integer()
        else:
            document.as_decimal()
    with pytest.raises(JSONValueError):
        document.as_value()


@pytest.mark.parametrize(
    "source, schema, expected",
    [
        (b'"123"', BIG_INTEGER, 123),
        (b'"1.5"', BIG_DECIMAL, Decimal("1.5")),
        (
            b'{"bigIntegerMember":"123","bigDecimalMember":"1.5"}',
            BIG_NUMBERS_SCHEMA,
            {"bigIntegerMember": 123, "bigDecimalMember": Decimal("1.5")},
        ),
        (b'["1.5","-2"]', BIG_DECIMAL_LIST_SCHEMA, [Decimal("1.5"), Decimal(-2)]),
    ],
)
def test_deserialized_typed_document_as_value(
    source: bytes, schema: Schema, expected: Any
) -> None:
    document = rpcv2_json_codec().create_deserializer(source).read_document(schema)
    assert isinstance(document, JSONDocument)
    assert document.as_value() == expected


def test_deserialized_struct_document_member_accessors() -> None:
    document = (
        rpcv2_json_codec()
        .create_deserializer(b'{"bigIntegerMember":"123","bigDecimalMember":"1.5"}')
        .read_document(BIG_NUMBERS_SCHEMA)
    )
    assert document["bigIntegerMember"].as_integer() == 123
    assert document["bigDecimalMember"].as_decimal() == Decimal("1.5")


def test_deserialized_struct_document_invalid_member_raises() -> None:
    document = (
        rpcv2_json_codec()
        .create_deserializer(b'{"bigDecimalMember":"1."}')
        .read_document(BIG_NUMBERS_SCHEMA)
    )
    with pytest.raises(JSONValueError):
        document["bigDecimalMember"].as_decimal()


def test_untyped_document_keeps_numbers() -> None:
    """**Validates: Requirements 4.4**"""
    document = (
        rpcv2_json_codec()
        .create_deserializer(b'{"x":1.5,"y":"1.5"}')
        .read_document(DOCUMENT)
    )
    assert document.as_value() == {"x": Decimal("1.5"), "y": "1.5"}


@pytest.mark.parametrize(
    "value, schema",
    [("123", BIG_INTEGER), ("1.5", BIG_DECIMAL)],
)
def test_setting_off_does_not_parse_strings(value: str, schema: Schema) -> None:
    document = JSONDocument(value, schema=schema)
    with pytest.raises(ExpectationNotMetError):
        if schema.shape_type is ShapeType.BIG_INTEGER:
            document.as_integer()
        else:
            document.as_decimal()
