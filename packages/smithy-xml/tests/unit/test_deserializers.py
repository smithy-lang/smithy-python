# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import math
from datetime import datetime
from decimal import Decimal
from io import BytesIO
from typing import Any
from xml.etree.ElementTree import ParseError

import pytest
from smithy_core.deserializers import ShapeDeserializer
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
from smithy_xml import XMLCodec, XMLDeserializationMode
from smithy_xml._private.deserializers import XMLShapeDeserializer
from smithy_xml._private.value_deserializer import XMLValueDeserializer

from . import (
    STRING_LIST_SCHEMA,
    STRING_MAP_SCHEMA,
    XML_SERDE_CASES,
    SerdeShape,
)


@pytest.mark.parametrize("mode", list(XMLDeserializationMode))
@pytest.mark.parametrize("expected, given", XML_SERDE_CASES)
def test_xml_deserializer(
    expected: Any,
    given: bytes,
    mode: XMLDeserializationMode,
) -> None:
    codec = XMLCodec(deserialization_mode=mode)
    deserializer = codec.create_deserializer(given)
    match expected:
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
        case list():
            actual_list: list[str] = []
            deserializer.read_list(
                STRING_LIST_SCHEMA,
                lambda d: actual_list.append(d.read_string(STRING)),
            )
            actual = actual_list
        case dict():
            actual_map: dict[str, str] = {}
            deserializer.read_map(
                STRING_MAP_SCHEMA,
                lambda k, d: actual_map.__setitem__(k, d.read_string(STRING)),
            )
            actual = actual_map
        case SerdeShape():
            actual = SerdeShape.deserialize(deserializer)
        case _:
            raise Exception(f"Unexpected type: {type(expected)}")

    assert actual == expected


@pytest.mark.parametrize(
    "mode, source, expected_type",
    [
        (XMLDeserializationMode.AUTO, b"<s/>", XMLValueDeserializer),
        (XMLDeserializationMode.AUTO, BytesIO(b"<s/>"), XMLShapeDeserializer),
        (XMLDeserializationMode.EAGER, BytesIO(b"<s/>"), XMLValueDeserializer),
        (XMLDeserializationMode.STREAMING, b"<s/>", XMLShapeDeserializer),
    ],
)
def test_deserialization_mode_selects_parser(
    mode: XMLDeserializationMode,
    source: bytes | BytesIO,
    expected_type: type[ShapeDeserializer],
) -> None:
    deserializer = XMLCodec(deserialization_mode=mode).create_deserializer(source)
    assert isinstance(deserializer, expected_type)


@pytest.mark.parametrize("mode", list(XMLDeserializationMode))
def test_invalid_xml_uses_existing_error_type(mode: XMLDeserializationMode) -> None:
    with pytest.raises(ParseError):
        deserializer = XMLCodec(deserialization_mode=mode).create_deserializer(
            b"<incomplete>"
        )
        deserializer.read_string(STRING)


def test_read_document_raises() -> None:
    """XML does not support document types."""
    deserializer = XMLCodec().create_deserializer(b"<doc>foo</doc>")
    with pytest.raises(
        NotImplementedError, match="XML does not support document types"
    ):
        deserializer.read_document(DOCUMENT)


def test_deserialize_nan() -> None:
    actual = XMLCodec().create_deserializer(b"<f>NaN</f>").read_float(FLOAT)
    assert math.isnan(actual)


def test_deserialize_empty_string_self_closed() -> None:
    assert XMLCodec().create_deserializer(b"<s/>").read_string(STRING) == ""


def test_deserialize_empty_string_open_close() -> None:
    assert XMLCodec().create_deserializer(b"<s></s>").read_string(STRING) == ""


def test_deserialize_empty_blob() -> None:
    assert XMLCodec().create_deserializer(b"<b></b>").read_blob(BLOB) == b""


def test_deserialize_empty_blob_self_closed() -> None:
    assert XMLCodec().create_deserializer(b"<b/>").read_blob(BLOB) == b""


@pytest.mark.parametrize("mode", list(XMLDeserializationMode))
def test_wrapper_elements(mode: XMLDeserializationMode) -> None:
    """Deserializer can unwrap awsQuery-style response wrappers."""
    xml = (
        b"<OpResponse><OpResult>"
        b"<stringMember>hello</stringMember>"
        b"</OpResult></OpResponse>"
    )
    deserializer = XMLCodec(deserialization_mode=mode).create_deserializer(
        xml, wrapper_elements=("OpResponse", "OpResult")
    )
    result = SerdeShape.deserialize(deserializer)
    assert result.string_member == "hello"


@pytest.mark.parametrize("mode", list(XMLDeserializationMode))
def test_wrapper_elements_scalar_read(mode: XMLDeserializationMode) -> None:
    xml = b"<OpResponse><OpResult>hello</OpResult></OpResponse>"
    deserializer = XMLCodec(deserialization_mode=mode).create_deserializer(
        xml, wrapper_elements=("OpResponse", "OpResult")
    )
    assert deserializer.read_string(STRING) == "hello"


@pytest.mark.parametrize("mode", list(XMLDeserializationMode))
def test_flattened_list_interleaved_with_other_members(
    mode: XMLDeserializationMode,
) -> None:
    """Flattened list elements can be interleaved with other struct members."""
    xml = (
        b"<SerdeShape>"
        b"<flattenedListMember>first</flattenedListMember>"
        b"<stringMember>middle</stringMember>"
        b"<flattenedListMember>second</flattenedListMember>"
        b"</SerdeShape>"
    )
    result = SerdeShape.deserialize(
        XMLCodec(deserialization_mode=mode).create_deserializer(xml)
    )
    assert result.flattened_list_member == ["first", "second"]
    assert result.string_member == "middle"


@pytest.mark.parametrize("mode", list(XMLDeserializationMode))
def test_unknown_members_skipped(mode: XMLDeserializationMode) -> None:
    xml = (
        b"<SerdeShape>"
        b"<stringMember>keep</stringMember>"
        b"<unknownMember>ignore</unknownMember>"
        b"<integerMember>5</integerMember>"
        b"</SerdeShape>"
    )
    result = SerdeShape.deserialize(
        XMLCodec(deserialization_mode=mode).create_deserializer(xml)
    )
    assert result == SerdeShape(string_member="keep", integer_member=5)
