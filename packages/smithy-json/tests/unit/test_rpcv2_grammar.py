# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Grammar edge cases for string-encoded big numbers under rpcv2Json."""

import json
from decimal import Decimal
from io import BytesIO

import pytest
from smithy_core.exceptions import SerializationError
from smithy_core.prelude import BIG_DECIMAL, BIG_INTEGER
from smithy_json._private.deserializers import JSONValueError

from . import rpcv2_json_codec


def _source(value: str) -> bytes:
    """Encode a Python string as a JSON string literal."""
    return json.dumps(value).encode("utf-8")


# Strings accepted by both the bigInteger and the bigDecimal grammar.
_VALID_BIG_INTEGER_STRINGS = ["0", "-0", "-123"]

# Strings accepted only by the bigDecimal grammar.
_VALID_BIG_DECIMAL_ONLY_STRINGS = ["1.5", "0.001", "1e10", "1E+10", "1.5e-3"]

# Strings rejected by both grammars.
_INVALID_STRINGS = ["01", "1.", ".5", "+1", " 1", "NaN", "Infinity", ""]

# Bare (non-string) JSON values, rejected for both types when the setting is on.
_BARE_JSON_VALUES = [b"0", b"123", b"-1", b"1.5", b"1e10", b"null", b"true"]


@pytest.mark.parametrize("value", _VALID_BIG_INTEGER_STRINGS)
def test_big_integer_accepts_valid_strings(value: str) -> None:
    deserializer = rpcv2_json_codec().create_deserializer(_source(value))
    assert deserializer.read_big_integer(BIG_INTEGER) == int(value)


@pytest.mark.parametrize("value", _INVALID_STRINGS + _VALID_BIG_DECIMAL_ONLY_STRINGS)
def test_big_integer_rejects_invalid_strings(value: str) -> None:
    deserializer = rpcv2_json_codec().create_deserializer(_source(value))
    with pytest.raises(JSONValueError):
        deserializer.read_big_integer(BIG_INTEGER)


@pytest.mark.parametrize(
    "value", _VALID_BIG_INTEGER_STRINGS + _VALID_BIG_DECIMAL_ONLY_STRINGS
)
def test_big_decimal_accepts_valid_strings(value: str) -> None:
    deserializer = rpcv2_json_codec().create_deserializer(_source(value))
    result = deserializer.read_big_decimal(BIG_DECIMAL)
    assert isinstance(result, Decimal)
    # Compare the tuple so digits and exponent are preserved exactly.
    assert result.as_tuple() == Decimal(value).as_tuple()


@pytest.mark.parametrize("value", _INVALID_STRINGS)
def test_big_decimal_rejects_invalid_strings(value: str) -> None:
    deserializer = rpcv2_json_codec().create_deserializer(_source(value))
    with pytest.raises(JSONValueError):
        deserializer.read_big_decimal(BIG_DECIMAL)


@pytest.mark.parametrize("source", _BARE_JSON_VALUES)
def test_big_integer_rejects_bare_json_values(source: bytes) -> None:
    deserializer = rpcv2_json_codec().create_deserializer(source)
    with pytest.raises(JSONValueError):
        deserializer.read_big_integer(BIG_INTEGER)


@pytest.mark.parametrize("source", _BARE_JSON_VALUES)
def test_big_decimal_rejects_bare_json_values(source: bytes) -> None:
    deserializer = rpcv2_json_codec().create_deserializer(source)
    with pytest.raises(JSONValueError):
        deserializer.read_big_decimal(BIG_DECIMAL)


@pytest.mark.parametrize(
    "value", [Decimal("NaN"), Decimal("Infinity"), Decimal("-Infinity")]
)
def test_big_decimal_non_finite_write_raises(value: Decimal) -> None:
    serializer = rpcv2_json_codec().create_serializer(BytesIO())
    with pytest.raises(SerializationError):
        serializer.write_big_decimal(BIG_DECIMAL, value)
