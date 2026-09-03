# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from datetime import UTC, datetime
from decimal import Decimal
from io import BytesIO
from typing import Any
from xml.etree.ElementTree import Element, fromstring

import pytest
from smithy_core.documents import Document
from smithy_core.exceptions import SerializationError
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
from smithy_core.schemas import Schema
from smithy_core.serializers import ShapeSerializer
from smithy_core.shapes import ShapeID, ShapeType
from smithy_core.traits import (
    XMLAttributeTrait,
    XMLFlattenedTrait,
    XMLNamespaceTrait,
    XMLNameTrait,
)
from smithy_xml import XMLCodec

from . import (
    NAMESPACED_LIST_SCHEMA,
    NAMESPACED_STRUCT_SCHEMA,
    PREFIXED_NS_STRUCT_SCHEMA,
    RENAMED_NS_MAP_SCHEMA,
    SCHEMA,
    STRING_LIST_SCHEMA,
    STRING_MAP_SCHEMA,
    XML_SERDE_CASES,
    SerdeShape,
)


def _canonical(element: Element) -> tuple[Any, ...]:
    """Convert an element into a comparable structure.

    Whitespace around child elements is ignored, but text in leaf elements is
    compared exactly.
    """
    children = [_canonical(child) for child in element]
    text = element.text or ""
    if children:
        text = text.strip()
    return (element.tag, sorted(element.attrib.items()), text, children)


def assert_xml_equal(actual: bytes, expected: bytes) -> None:
    assert _canonical(fromstring(actual)) == _canonical(fromstring(expected)), (
        f"\nactual:   {actual!r}\nexpected: {expected!r}"
    )


def _serialize(value: Any, schema: Schema, codec: XMLCodec | None = None) -> bytes:
    codec = codec or XMLCodec()
    sink = BytesIO()
    serializer = codec.create_serializer(sink)
    match value:
        case bool():
            serializer.write_boolean(schema, value)
        case int():
            serializer.write_integer(schema, value)
        case float():
            serializer.write_float(schema, value)
        case Decimal():
            serializer.write_big_decimal(schema, value)
        case bytes():
            serializer.write_blob(schema, value)
        case str():
            serializer.write_string(schema, value)
        case datetime():
            serializer.write_timestamp(schema, value)
        case list():
            with serializer.begin_list(schema, len(value)) as ls:  # type: ignore
                for element in value:  # type: ignore
                    ls.write_string(schema.members["member"], element)  # type: ignore
        case dict():
            with serializer.begin_map(schema, len(value)) as ms:  # type: ignore
                for k, v in value.items():  # type: ignore
                    ms.entry(k, lambda vs: vs.write_string(schema.members["value"], v))  # type: ignore
        case SerdeShape():
            value.serialize(serializer)
        case _:
            raise Exception(f"Unexpected type: {type(value)}")
    serializer.flush()
    return sink.getvalue()


def _schema_for(value: Any) -> Schema:
    match value:
        case bool():
            return BOOLEAN
        case int():
            return INTEGER
        case float():
            return FLOAT
        case Decimal():
            return BIG_DECIMAL
        case bytes():
            return BLOB
        case str():
            return STRING
        case datetime():
            return TIMESTAMP
        case list():
            return STRING_LIST_SCHEMA
        case dict():
            return STRING_MAP_SCHEMA
        case SerdeShape():
            return SCHEMA
        case _:
            raise Exception(f"Unexpected type: {type(value)}")


@pytest.mark.parametrize("given, expected", XML_SERDE_CASES)
def test_xml_serializer(given: Any, expected: bytes) -> None:
    assert_xml_equal(_serialize(given, _schema_for(given)), expected)


@pytest.mark.parametrize("given, _expected", XML_SERDE_CASES)
def test_xml_round_trip(given: Any, _expected: bytes) -> None:
    """Serializing and then deserializing yields the original value."""
    serialized = _serialize(given, _schema_for(given))
    deserializer = XMLCodec().create_deserializer(serialized)
    match given:
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
            raise Exception(f"Unexpected type: {type(given)}")
    assert actual == given


def test_serialize_nan() -> None:
    assert _serialize(float("nan"), FLOAT) == b"<Float>NaN</Float>"


def test_serialize_null_is_omitted() -> None:
    sink = BytesIO()
    serializer = XMLCodec().create_serializer(sink)
    with serializer.begin_struct(SCHEMA) as s:
        s.write_null(SCHEMA.members["stringMember"])
    assert sink.getvalue() == b"<SerdeShape></SerdeShape>"


def test_write_document_raises() -> None:
    serializer = XMLCodec().create_serializer(BytesIO())
    with pytest.raises(SerializationError, match="does not support document"):
        serializer.write_document(DOCUMENT, Document("foo"))


def test_attribute_outside_struct_raises() -> None:
    serializer = XMLCodec().create_serializer(BytesIO())
    with pytest.raises(SerializationError, match="enclosing structure"):
        serializer.write_string(SCHEMA.members["xmlAttributeMember"], "foo")


def test_escapes_text_and_attributes() -> None:
    shape = SerdeShape(string_member='a<b>&"c\r\n', xml_attribute_member='x<y>&"z\n')
    serialized = _serialize(shape, SCHEMA)
    assert serialized == (
        b'<SerdeShape xmlAttributeMember="x&lt;y&gt;&amp;&quot;z&#10;">'
        b'<stringMember>a&lt;b&gt;&amp;"c&#13;\n</stringMember>'
        b"</SerdeShape>"
    )
    parsed = fromstring(serialized)
    assert parsed.attrib["xmlAttributeMember"] == 'x<y>&"z\n'
    assert parsed[0].text == 'a<b>&"c\r\n'


def test_attribute_written_after_children() -> None:
    """Attributes end up on the start tag regardless of member order."""
    shape = SerdeShape(string_member="foo", xml_attribute_member="bar")
    assert _serialize(shape, SCHEMA) == (
        b'<SerdeShape xmlAttributeMember="bar">'
        b"<stringMember>foo</stringMember></SerdeShape>"
    )


def test_default_namespace_applied_to_root_only() -> None:
    codec = XMLCodec(default_namespace="https://example.com")
    shape = SerdeShape(struct_member=SerdeShape(string_member="foo"))
    assert _serialize(shape, SCHEMA, codec) == (
        b'<SerdeShape xmlns="https://example.com">'
        b"<structMember><stringMember>foo</stringMember></structMember>"
        b"</SerdeShape>"
    )


def test_default_namespace_prefix_declares_prefixed_xmlns() -> None:
    codec = XMLCodec(
        default_namespace="https://example.com", default_namespace_prefix="ex"
    )
    shape = SerdeShape(string_member="foo")
    assert _serialize(shape, SCHEMA, codec) == (
        b'<SerdeShape xmlns:ex="https://example.com">'
        b"<stringMember>foo</stringMember></SerdeShape>"
    )


def test_root_namespace_trait_overrides_default() -> None:
    codec = XMLCodec(default_namespace="https://default.example.com")
    sink = BytesIO()
    serializer = codec.create_serializer(sink)
    with serializer.begin_struct(NAMESPACED_STRUCT_SCHEMA) as s:
        s.write_string(NAMESPACED_STRUCT_SCHEMA.members["value"], "foo")
    assert sink.getvalue() == (
        b'<NsStruct xmlns="https://example.com"><value>foo</value></NsStruct>'
    )


def test_root_namespace_with_prefix() -> None:
    sink = BytesIO()
    serializer = XMLCodec().create_serializer(sink)
    with serializer.begin_struct(PREFIXED_NS_STRUCT_SCHEMA) as s:
        s.write_string(PREFIXED_NS_STRUCT_SCHEMA.members["value"], "foo")
    assert sink.getvalue() == (
        b'<PrefixedNsStruct xmlns:baz="https://example.com">'
        b"<value>foo</value></PrefixedNsStruct>"
    )


# A structure that exercises naming and namespace rules for nested members.
_PAYLOAD_SCHEMA = Schema.collection(
    id=ShapeID("smithy.example#Payload"),
    traits=[XMLNameTrait("Hello"), XMLNamespaceTrait({"uri": "http://foo.com"})],
    members={"name": {"target": STRING}},
)

_CONTAINER_SCHEMA = Schema.collection(
    id=ShapeID("smithy.example#Container"),
    traits=[XMLNamespaceTrait({"uri": "http://root.com"})],
    members={
        # Target's @xmlName and @xmlNamespace must not apply to nested members.
        "nested": {"target": _PAYLOAD_SCHEMA},
        "renamedNested": {
            "target": _PAYLOAD_SCHEMA,
            "traits": [XMLNameTrait("Hola")],
        },
        "namespacedString": {
            "target": STRING,
            "traits": [XMLNamespaceTrait({"uri": "http://baz.com", "prefix": "baz"})],
        },
        "namespacedList": {
            "target": NAMESPACED_LIST_SCHEMA,
            "traits": [XMLNamespaceTrait({"uri": "http://qux.com"})],
        },
        "flattenedNamespacedList": {
            "target": NAMESPACED_LIST_SCHEMA,
            "traits": [XMLFlattenedTrait()],
        },
        "flattenedOverrideList": {
            "target": NAMESPACED_LIST_SCHEMA,
            "traits": [
                XMLFlattenedTrait(),
                XMLNamespaceTrait({"uri": "http://own.com"}),
            ],
        },
        "namespacedMap": {
            "target": RENAMED_NS_MAP_SCHEMA,
            "traits": [
                XMLNameTrait("KVP"),
                XMLNamespaceTrait({"uri": "http://member.com"}),
            ],
        },
        "flattenedNamespacedMap": {
            "target": RENAMED_NS_MAP_SCHEMA,
            "traits": [
                XMLFlattenedTrait(),
                XMLNameTrait("FlatKVP"),
                XMLNamespaceTrait({"uri": "http://member.com"}),
            ],
        },
        "prefixedAttribute": {
            "target": STRING,
            "traits": [XMLAttributeTrait(), XMLNameTrait("baz:attr")],
        },
    },
)


def _write_payload(serializer: Any, schema: Schema, name: str) -> None:
    with serializer.begin_struct(schema) as s:
        s.write_string(_PAYLOAD_SCHEMA.members["name"], name)


def test_nested_members_ignore_target_name_and_namespace() -> None:
    sink = BytesIO()
    serializer = XMLCodec().create_serializer(sink)
    with serializer.begin_struct(_CONTAINER_SCHEMA) as s:
        _write_payload(s, _CONTAINER_SCHEMA.members["nested"], "a")
        _write_payload(s, _CONTAINER_SCHEMA.members["renamedNested"], "b")
        s.write_string(_CONTAINER_SCHEMA.members["namespacedString"], "c")
        s.write_string(_CONTAINER_SCHEMA.members["prefixedAttribute"], "d")
    assert sink.getvalue() == (
        b'<Container xmlns="http://root.com" baz:attr="d">'
        b"<nested><name>a</name></nested>"
        b"<Hola><name>b</name></Hola>"
        b'<namespacedString xmlns:baz="http://baz.com">c</namespacedString>'
        b"</Container>"
    )


def test_payload_root_uses_member_name_then_target_name() -> None:
    # Member @xmlName wins over the target's.
    sink = BytesIO()
    _write_payload(
        XMLCodec().create_serializer(sink),
        _CONTAINER_SCHEMA.members["renamedNested"],
        "a",
    )
    assert sink.getvalue() == b'<Hola xmlns="http://foo.com"><name>a</name></Hola>'

    # Otherwise the target's @xmlName and @xmlNamespace apply.
    sink = BytesIO()
    _write_payload(
        XMLCodec().create_serializer(sink), _CONTAINER_SCHEMA.members["nested"], "a"
    )
    assert sink.getvalue() == b'<Hello xmlns="http://foo.com"><name>a</name></Hello>'

    # Without any @xmlName, the target shape's name is used.
    sink = BytesIO()
    _write_payload(
        XMLCodec().create_serializer(sink), SCHEMA.members["structMember"], "a"
    )
    assert sink.getvalue() == b"<SerdeShape><name>a</name></SerdeShape>"


def _write_string_list(serializer: Any, schema: Schema, values: list[str]) -> None:
    item_schema = schema.expect_member_target().members["member"]
    with serializer.begin_list(schema, len(values)) as ls:
        for value in values:
            ls.write_string(item_schema, value)


def test_list_namespaces() -> None:
    sink = BytesIO()
    serializer = XMLCodec().create_serializer(sink)
    with serializer.begin_struct(_CONTAINER_SCHEMA) as s:
        _write_string_list(s, _CONTAINER_SCHEMA.members["namespacedList"], ["a"])
        _write_string_list(
            s, _CONTAINER_SCHEMA.members["flattenedNamespacedList"], ["b"]
        )
        _write_string_list(s, _CONTAINER_SCHEMA.members["flattenedOverrideList"], ["c"])
    assert sink.getvalue() == (
        b'<Container xmlns="http://root.com">'
        # Wrapped: member namespace on the wrapper, list member namespace on items.
        b'<namespacedList xmlns="http://qux.com">'
        b'<member xmlns="http://bux.com">a</member>'
        b"</namespacedList>"
        # Flattened: list member namespace on items when the member has none.
        b'<flattenedNamespacedList xmlns="http://bux.com">b</flattenedNamespacedList>'
        # Flattened: the member's own namespace wins when present.
        b'<flattenedOverrideList xmlns="http://own.com">c</flattenedOverrideList>'
        b"</Container>"
    )


def _write_string_map(serializer: Any, schema: Schema, values: dict[str, str]) -> None:
    value_schema = schema.expect_member_target().members["value"]
    with serializer.begin_map(schema, len(values)) as ms:
        for k, v in values.items():

            def write_value(vs: ShapeSerializer, v: str = v) -> None:
                vs.write_string(value_schema, v)

            ms.entry(k, write_value)


def test_map_names_and_namespaces() -> None:
    sink = BytesIO()
    serializer = XMLCodec().create_serializer(sink)
    with serializer.begin_struct(_CONTAINER_SCHEMA) as s:
        _write_string_map(s, _CONTAINER_SCHEMA.members["namespacedMap"], {"a": "A"})
        _write_string_map(
            s, _CONTAINER_SCHEMA.members["flattenedNamespacedMap"], {"b": "B", "c": "C"}
        )
    assert sink.getvalue() == (
        b'<Container xmlns="http://root.com">'
        b'<KVP xmlns="http://member.com"><entry>'
        b'<K xmlns="https://the-key.example.com">a</K>'
        b'<V xmlns="https://the-value.example.com">A</V>'
        b"</entry></KVP>"
        b'<FlatKVP xmlns="http://member.com">'
        b'<K xmlns="https://the-key.example.com">b</K>'
        b'<V xmlns="https://the-value.example.com">B</V>'
        b"</FlatKVP>"
        b'<FlatKVP xmlns="http://member.com">'
        b'<K xmlns="https://the-key.example.com">c</K>'
        b'<V xmlns="https://the-value.example.com">C</V>'
        b"</FlatKVP>"
        b"</Container>"
    )


def test_nested_map_values() -> None:
    nested_map_schema = Schema.collection(
        id=ShapeID("smithy.example#NestedMap"),
        shape_type=ShapeType.MAP,
        members={
            "key": {"target": STRING},
            "value": {"target": STRING_MAP_SCHEMA},
        },
    )
    container = Schema.collection(
        id=ShapeID("smithy.example#NestedMapContainer"),
        members={"nestedMap": {"target": nested_map_schema}},
    )
    member_schema = container.members["nestedMap"]
    inner_value_schema = STRING_MAP_SCHEMA.members["value"]

    sink = BytesIO()
    serializer = XMLCodec().create_serializer(sink)
    with serializer.begin_struct(container) as s:
        with s.begin_map(member_schema, 1) as outer:

            def write_inner(vs: ShapeSerializer) -> None:
                with vs.begin_map(nested_map_schema.members["value"], 1) as inner:
                    inner.entry(
                        "k",
                        lambda ivs: ivs.write_string(inner_value_schema, "v"),
                    )

            outer.entry("outer", write_inner)
    assert sink.getvalue() == (
        b"<NestedMapContainer><nestedMap><entry><key>outer</key>"
        b"<value><entry><key>k</key><value>v</value></entry></value>"
        b"</entry></nestedMap></NestedMapContainer>"
    )


def test_timestamp_formats() -> None:
    when = datetime(2014, 4, 29, 18, 30, 38, tzinfo=UTC)
    shape = SerdeShape(
        timestamp_member=when,
        http_date_member=when,
        epoch_seconds_member=when,
    )
    assert _serialize(shape, SCHEMA) == (
        b"<SerdeShape>"
        b"<timestampMember>2014-04-29T18:30:38Z</timestampMember>"
        b"<httpDateMember>Tue, 29 Apr 2014 18:30:38 GMT</httpDateMember>"
        b"<epochSecondsMember>1398796238</epochSecondsMember>"
        b"</SerdeShape>"
    )


def test_timestamp_format_trait_disabled() -> None:
    when = datetime(2014, 4, 29, 18, 30, 38, tzinfo=UTC)
    codec = XMLCodec(use_timestamp_format=False)
    assert _serialize(SerdeShape(http_date_member=when), SCHEMA, codec) == (
        b"<SerdeShape><httpDateMember>2014-04-29T18:30:38Z</httpDateMember></SerdeShape>"
    )


def test_codec_serialize() -> None:
    assert XMLCodec().serialize(SerdeShape(integer_member=1)) == (
        b"<SerdeShape><integerMember>1</integerMember></SerdeShape>"
    )


def test_root_uses_original_shape_name_when_renamed() -> None:
    from smithy_core.traits import Trait

    schema = Schema.collection(
        id=ShapeID("smithy.example#FooInput"),
        traits=[
            Trait.new(
                id=ShapeID("smithy.synthetic#originalShapeId"),
                value="smithy.example#FooRequest",
            )
        ],
        members={"name": {"target": STRING}},
    )
    sink = BytesIO()
    serializer = XMLCodec().create_serializer(sink)
    with serializer.begin_struct(schema) as s:
        s.write_string(schema.members["name"], "a")
    assert sink.getvalue() == b"<FooRequest><name>a</name></FooRequest>"
