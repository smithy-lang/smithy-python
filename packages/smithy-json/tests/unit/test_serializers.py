# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import json
from datetime import datetime
from decimal import Decimal
from io import BytesIO
from typing import Any, cast

import pytest
from smithy_core.documents import Document
from smithy_core.prelude import (
    BIG_DECIMAL,
    BLOB,
    BOOLEAN,
    FLOAT,
    INTEGER,
    STRING,
    TIMESTAMP,
)
from smithy_json import JSONCodec

from . import (
    JSON_SERIALIZATION_CASES,
    SPARSE_STRING_LIST_SCHEMA,
    SPARSE_STRING_MAP_SCHEMA,
    SerdeShape,
)


@pytest.mark.parametrize("given, expected", JSON_SERIALIZATION_CASES)
def test_json_serializer(given: Any, expected: bytes) -> None:
    sink = BytesIO()
    serializer = JSONCodec().create_serializer(sink)
    match given:
        case None:
            serializer.write_null(STRING)
        case bool():
            serializer.write_boolean(BOOLEAN, given)
        case int():
            serializer.write_integer(INTEGER, given)
        case float():
            serializer.write_float(FLOAT, given)
        case Decimal():
            serializer.write_big_decimal(BIG_DECIMAL, given)
        case bytes():
            serializer.write_blob(BLOB, given)
        case str():
            serializer.write_string(STRING, given)
        case datetime():
            serializer.write_timestamp(TIMESTAMP, given)
        case Document():
            serializer.write_document(given._schema, given)  # type: ignore
        case list():
            given = cast(list[str], given)
            with serializer.begin_list(
                SPARSE_STRING_LIST_SCHEMA, len(given)
            ) as list_serializer:
                member_schema = SPARSE_STRING_LIST_SCHEMA.members["member"]
                for e in given:
                    if e is None:
                        list_serializer.write_null(member_schema)
                    else:
                        list_serializer.write_string(member_schema, e)
        case dict():
            given = cast(dict[str, str], given)
            with serializer.begin_map(
                SPARSE_STRING_MAP_SCHEMA, len(given)
            ) as map_serializer:
                member_schema = SPARSE_STRING_MAP_SCHEMA.members["value"]
                for k, v in given.items():
                    if v is None:
                        map_serializer.entry(k, lambda vs: vs.write_null(member_schema))
                    else:
                        map_serializer.entry(
                            k, lambda vs: vs.write_string(member_schema, v)
                        )  # type: ignore
        case SerdeShape():
            given.serialize(serializer)
        case _:
            raise Exception(f"Unexpected type: {type(given)}")

    serializer.flush()
    sink.seek(0)
    actual = sink.read()
    assert actual == expected


def _serialize_string(value: str) -> bytes:
    """Serialize a string value through the JSON codec and return raw bytes."""
    sink = BytesIO()
    serializer = JSONCodec().create_serializer(sink)
    serializer.write_string(STRING, value)
    serializer.flush()
    sink.seek(0)
    return sink.read()


class TestStringControlCharEscaping:
    """RFC 8259 §7: All control characters U+0000-U+001F must be escaped."""

    @pytest.mark.parametrize(
        "char, escaped",
        [
            ("\n", "\\n"),
            ("\r", "\\r"),
            ("\t", "\\t"),
            ("\b", "\\b"),
            ("\f", "\\f"),
        ],
    )
    def test_named_control_chars(self, char: str, escaped: str) -> None:
        result = _serialize_string(f"a{char}b")
        assert result == f'"a{escaped}b"'.encode()

    def test_all_control_chars_produce_valid_json(self) -> None:
        """Every U+0000-U+001F character must be escaped so output is valid JSON."""
        for cp in range(0x20):
            value = f"before{chr(cp)}after"
            raw = _serialize_string(value)
            # Must parse as valid JSON
            parsed = json.loads(raw)
            assert parsed == value, f"Round-trip failed for U+{cp:04X}"

    def test_null_byte(self) -> None:
        result = _serialize_string("a\x00b")
        assert result == b'"a\\u0000b"'

    def test_mixed_escapes(self) -> None:
        result = _serialize_string('line 1\nline 2\t"quoted"\r\n')
        assert result == b'"line 1\\nline 2\\t\\"quoted\\"\\r\\n"'

    def test_existing_backslash_and_quote_still_escaped(self) -> None:
        result = _serialize_string('a\\b"c')
        assert result == b'"a\\\\b\\"c"'

    def test_serialized_output_is_valid_json(self) -> None:
        """Realistic multi-line prompt string produces valid JSON."""
        value = "System: You are helpful.\nUser: Hello\nAssistant:"
        raw = _serialize_string(value)
        parsed = json.loads(raw)
        assert parsed == value
