# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from datetime import datetime
from decimal import Decimal
from io import BytesIO
from typing import Any

import pytest
from smithy_core.prelude import (
    BIG_DECIMAL,
    BLOB,
    BOOLEAN,
    FLOAT,
    INTEGER,
    STRING,
    TIMESTAMP,
)
from smithy_core.schemas import Schema
from smithy_core.serializers import ShapeSerializer
from smithy_core.shapes import ShapeID
from smithy_core.traits import (
    ORIGINAL_SHAPE_ID,
    DynamicTrait,
    XMLAttributeTrait,
    XMLNamespaceTrait,
    XMLNameTrait,
)
from smithy_test import xml_equal
from smithy_xml import XMLCodec

from . import XML_SERDE_CASES, SerdeShape


def _serialize(value: Any, codec: XMLCodec | None = None) -> bytes:
    sink = BytesIO()
    serializer = (codec or XMLCodec()).create_serializer(sink)
    match value:
        case SerdeShape():
            value.serialize(serializer)
        case bool():
            serializer.write_boolean(BOOLEAN, value)
        case int():
            serializer.write_integer(INTEGER, value)
        case float():
            serializer.write_float(FLOAT, value)
        case Decimal():
            serializer.write_big_decimal(BIG_DECIMAL, value)
        case bytes():
            serializer.write_blob(BLOB, value)
        case str():
            serializer.write_string(STRING, value)
        case datetime():
            serializer.write_timestamp(TIMESTAMP, value)
        case _:
            raise Exception(f"Unexpected type: {type(value)}")
    serializer.flush()
    return sink.getvalue()


@pytest.mark.parametrize(
    "given, expected",
    [c for c in XML_SERDE_CASES if not isinstance(c[0], list | dict)],
)
def test_xml_serializer(given: Any, expected: bytes) -> None:
    actual = _serialize(given)
    assert xml_equal(actual, expected), actual


def test_round_trip_with_attributes_written_after_children() -> None:
    # The attribute member is serialized after element members, so it has to be
    # placed back into the already-written start tag.
    given = SerdeShape(
        string_member="a",
        struct_member=SerdeShape(xml_attribute_member="inner"),
        xml_attribute_member='"<&>"\n',
    )
    actual = _serialize(given)
    assert actual == (
        b'<SerdeShape xmlAttributeMember="&quot;&lt;&amp;&gt;&quot;&#xA;">'
        b"<stringMember>a</stringMember>"
        b'<structMember xmlAttributeMember="inner"></structMember>'
        b"</SerdeShape>"
    )
    assert SerdeShape.deserialize(XMLCodec().create_deserializer(actual)) == given


def test_text_escaping_preserves_carriage_returns() -> None:
    actual = _serialize(SerdeShape(string_member="a\r\nb"))
    assert actual == b"<SerdeShape><stringMember>a&#xD;\nb</stringMember></SerdeShape>"
    deserialized = SerdeShape.deserialize(XMLCodec().create_deserializer(actual))
    assert deserialized.string_member == "a\r\nb"


def test_default_namespace_applies_to_root_only() -> None:
    codec = XMLCodec(default_namespace="https://example.com")
    actual = _serialize(SerdeShape(struct_member=SerdeShape(string_member="x")), codec)
    assert actual == (
        b'<SerdeShape xmlns="https://example.com">'
        b"<structMember><stringMember>x</stringMember></structMember>"
        b"</SerdeShape>"
    )


_PAYLOAD = Schema.collection(
    id=ShapeID("smithy.example#Payload"),
    traits=[
        XMLNameTrait("Hello"),
        XMLNamespaceTrait({"uri": "https://payload.example.com"}),
    ],
    members={
        "name": {"target": STRING},
        "attr": {
            "target": STRING,
            "traits": [XMLAttributeTrait(), XMLNameTrait("xsi:attr")],
        },
    },
)

_CONTAINER = Schema.collection(
    id=ShapeID("smithy.example#OpInput"),
    traits=[DynamicTrait(id=ORIGINAL_SHAPE_ID, document_value="smithy.example#Op")],
    members={
        "nested": {"target": _PAYLOAD},
        "renamed": {"target": _PAYLOAD, "traits": [XMLNameTrait("Hola")]},
    },
)


def _write_payload(serializer: ShapeSerializer, schema: Schema) -> None:
    with serializer.begin_struct(schema) as s:
        s.write_string(_PAYLOAD.members["name"], "n")


@pytest.mark.parametrize(
    "schema, expected",
    [
        # A payload member peeks through to its target's name and namespace...
        (
            _CONTAINER.members["nested"],
            b'<Hello xmlns="https://payload.example.com"><name>n</name></Hello>',
        ),
        # ...unless it has its own @xmlName.
        (
            _CONTAINER.members["renamed"],
            b'<Hola xmlns="https://payload.example.com"><name>n</name></Hola>',
        ),
    ],
)
def test_root_member_names(schema: Schema, expected: bytes) -> None:
    sink = BytesIO()
    _write_payload(XMLCodec().create_serializer(sink), schema)
    assert sink.getvalue() == expected


def test_root_uses_original_shape_name() -> None:
    sink = BytesIO()
    serializer = XMLCodec().create_serializer(sink)
    with serializer.begin_struct(_CONTAINER) as s:
        _write_payload(s, _CONTAINER.members["nested"])
    # Nested members keep their member name; the target's @xmlName and
    # @xmlNamespace only apply at the root.
    assert sink.getvalue() == b"<Op><nested><name>n</name></nested></Op>"


def test_prefixed_attribute_round_trip() -> None:
    sink = BytesIO()
    serializer = XMLCodec().create_serializer(sink)
    with serializer.begin_struct(_PAYLOAD) as s:
        s.write_string(_PAYLOAD.members["attr"], "v")
    actual = sink.getvalue()
    assert actual == b'<Hello xmlns="https://payload.example.com" xsi:attr="v"></Hello>'

    # The prefix is declared by the enclosing document in practice.
    document = b'<Hello xmlns:xsi="https://x.example.com" xsi:attr="v"></Hello>'
    found: dict[str, str] = {}
    XMLCodec().create_deserializer(document).read_struct(
        _PAYLOAD,
        lambda member, de: found.__setitem__(
            member.expect_member_name(), de.read_string(member)
        ),
    )
    assert found == {"attr": "v"}
