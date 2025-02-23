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
