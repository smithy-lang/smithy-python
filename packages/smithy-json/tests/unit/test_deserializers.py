# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import math
from datetime import datetime
from decimal import Decimal
from io import BytesIO
from typing import Any

import pytest
from ijson.common import IncompleteJSONError  # type: ignore
from smithy_core.deserializers import ShapeDeserializer
from smithy_core.documents import Document
from smithy_core.prelude import (
    BIG_DECIMAL,
    BLOB,
    BOOLEAN,
    DOCUMENT,
    FLOAT,
    INTEGER,
    STRING,
    TIMESTAMP,
)
from smithy_json import JSONCodec, JSONDeserializationMode, JSONDocument
from smithy_json._private.deserializers import JSONShapeDeserializer
from smithy_json._private.value_deserializer import JSONValueDeserializer

from . import (
    JSON_SERDE_CASES,
    SPARSE_STRING_LIST_SCHEMA,
    SPARSE_STRING_MAP_SCHEMA,
    SerdeShape,
)


@pytest.mark.parametrize(
    "mode",
    [JSONDeserializationMode.STREAMING, JSONDeserializationMode.EAGER],
)
@pytest.mark.parametrize("expected, given", JSON_SERDE_CASES)
def test_json_deserializer(
    expected: Any,
    given: bytes,
    mode: JSONDeserializationMode,
) -> None:
    codec = JSONCodec(deserialization_mode=mode)
    deserializer = codec.create_deserializer(given)
    match expected:
        case None:
            actual = deserializer.read_null()
        case bool():
            actual = deserializer.read_boolean(BOOLEAN)
        case int():
            actual = deserializer.read_integer(INTEGER)
        case float():
            actual = deserializer.read_float(FLOAT)
        case Decimal():
            actual = deserializer.read_big_decimal(BIG_DECIMAL)
        case bytes():
            actual = deserializer.read_blob(BLOB)
        case str():
            actual = deserializer.read_string(STRING)
        case datetime():
            actual = deserializer.read_timestamp(TIMESTAMP)
        case Document():
            actual = deserializer.read_document(expected._schema)  # type: ignore
        case list():
            actual_list: list[str | None] = []

            def _read_optional_list(d: ShapeDeserializer):
                if d.is_null():
                    d.read_null()
                    actual_list.append(None)
                else:
                    actual_list.append(d.read_string(STRING))

            deserializer.read_list(
                SPARSE_STRING_LIST_SCHEMA,
                _read_optional_list,
            )
            actual = actual_list
        case dict():
            actual_map: dict[str, str | None] = {}

            def _read_optional_map(k: str, d: ShapeDeserializer):
                if d.is_null():
                    d.read_null()
                    actual_map[k] = None
                else:
                    actual_map[k] = d.read_string(STRING)

            deserializer.read_map(
                SPARSE_STRING_MAP_SCHEMA,
                _read_optional_map,
            )
            actual = actual_map
        case SerdeShape():
            actual = codec.deserialize(given, SerdeShape)
        case _:
            raise Exception(f"Unexpected type: {type(given)}")

    if isinstance(actual, Document) and isinstance(expected, Document):
        actual_value = actual.as_value()
        expected_value = expected.as_value()
        assert actual_value == expected_value
    elif isinstance(expected, float) and math.isnan(expected):
        assert isinstance(actual, float)
        assert math.isnan(actual)
    elif isinstance(expected, Decimal) and expected.is_nan():
        assert isinstance(actual, Decimal)
        assert actual.is_nan()
    else:
        assert actual == expected


class CustomDocument(JSONDocument):
    pass


def test_uses_custom_document() -> None:
    codec = JSONCodec(document_class=CustomDocument)
    actual = codec.create_deserializer(b'{"foo": "bar"}').read_document(DOCUMENT)
    assert isinstance(actual, CustomDocument)


@pytest.mark.parametrize(
    "mode, source, expected_type",
    [
        (JSONDeserializationMode.AUTO, b"{}", JSONValueDeserializer),
        (JSONDeserializationMode.AUTO, BytesIO(b"{}"), JSONShapeDeserializer),
        (JSONDeserializationMode.EAGER, BytesIO(b"{}"), JSONValueDeserializer),
        (JSONDeserializationMode.STREAMING, b"{}", JSONShapeDeserializer),
    ],
)
def test_deserialization_mode_selects_parser(
    mode: JSONDeserializationMode,
    source: bytes | BytesIO,
    expected_type: type[ShapeDeserializer],
) -> None:
    deserializer = JSONCodec(deserialization_mode=mode).create_deserializer(source)
    assert isinstance(deserializer, expected_type)


@pytest.mark.parametrize(
    "mode",
    [JSONDeserializationMode.STREAMING, JSONDeserializationMode.EAGER],
)
def test_ignores_unknown_structure_members(mode: JSONDeserializationMode) -> None:
    actual = JSONCodec(deserialization_mode=mode).deserialize(
        b'{"unknown":{"nested":[1,2,3]},"stringMember":"value"}',
        SerdeShape,
    )

    assert actual.string_member == "value"


@pytest.mark.parametrize(
    "mode",
    [JSONDeserializationMode.STREAMING, JSONDeserializationMode.EAGER],
)
def test_invalid_json_uses_existing_error_type(mode: JSONDeserializationMode) -> None:
    with pytest.raises(IncompleteJSONError):
        deserializer = JSONCodec(deserialization_mode=mode).create_deserializer(
            b'{"incomplete":'
        )
        deserializer.read_document(DOCUMENT)
