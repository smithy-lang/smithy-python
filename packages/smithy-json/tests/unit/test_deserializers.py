from datetime import datetime
from decimal import Decimal
from typing import Any

import pytest
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
from smithy_json import JSONCodec, JSONDocument

from . import (
    JSON_SERDE_CASES,
    SPARSE_STRING_LIST_SCHEMA,
    SPARSE_STRING_MAP_SCHEMA,
    SerdeShape,
)


@pytest.mark.parametrize("expected, given", JSON_SERDE_CASES)
def test_json_deserializer(expected: Any, given: bytes) -> None:
    codec = JSONCodec()
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
    else:
        assert actual == expected


class CustomDocument(JSONDocument):
    pass


def test_uses_custom_document() -> None:
    codec = JSONCodec(document_class=CustomDocument)
    actual = codec.create_deserializer(b'{"foo": "bar"}').read_document(DOCUMENT)
    assert isinstance(actual, CustomDocument)
