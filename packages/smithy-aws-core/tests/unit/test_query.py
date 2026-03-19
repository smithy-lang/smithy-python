#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass
from io import BytesIO

from smithy_aws_core._private.query.serializers import QueryShapeSerializer
from smithy_core.prelude import STRING
from smithy_core.schemas import Schema
from smithy_core.serializers import ShapeSerializer
from smithy_core.shapes import ShapeID, ShapeType
from smithy_core.traits import XmlFlattenedTrait, XmlNameTrait


def test_query_list_serialization() -> None:
    list_schema = Schema.collection(
        id=ShapeID("com.test#StringList"),
        shape_type=ShapeType.LIST,
        members={"member": {"target": STRING}},
    )
    params: list[tuple[str, str]] = []
    serializer = QueryShapeSerializer(
        sink=BytesIO(),
        action="TestOperation",
        version="2020-01-08",
        path=("Items",),
        params=params,
    )
    with serializer.begin_list(list_schema, 2) as list_serializer:
        member_schema = list_schema.members["member"]
        list_serializer.write_string(member_schema, "a")
        list_serializer.write_string(member_schema, "b")

    assert params == [
        ("Items.member.1", "a"),
        ("Items.member.2", "b"),
    ]


def test_query_flattened_list_serialization() -> None:
    list_schema = Schema.collection(
        id=ShapeID("com.test#StringList"),
        shape_type=ShapeType.LIST,
        traits=[XmlFlattenedTrait()],
        members={"member": {"target": STRING}},
    )
    params: list[tuple[str, str]] = []
    serializer = QueryShapeSerializer(
        sink=BytesIO(),
        action="TestOperation",
        version="2020-01-08",
        path=("Items",),
        params=params,
    )
    with serializer.begin_list(list_schema, 2) as list_serializer:
        member_schema = list_schema.members["member"]
        list_serializer.write_string(member_schema, "a")
        list_serializer.write_string(member_schema, "b")

    assert params == [("Items.1", "a"), ("Items.2", "b")]


def test_query_empty_list_serialization() -> None:
    list_schema = Schema.collection(
        id=ShapeID("com.test#StringList"),
        shape_type=ShapeType.LIST,
        members={"member": {"target": STRING}},
    )
    params: list[tuple[str, str]] = []
    serializer = QueryShapeSerializer(
        sink=BytesIO(),
        action="TestOperation",
        version="2020-01-08",
        path=("Items",),
        params=params,
    )
    with serializer.begin_list(list_schema, 0):
        pass

    assert params == [("Items", "")]


def test_query_flattened_list_uses_member_xml_name() -> None:
    list_schema = Schema.collection(
        id=ShapeID("com.test#StringList"),
        shape_type=ShapeType.LIST,
        members={"member": {"target": STRING, "traits": [XmlNameTrait("item")]}},
    )
    input_schema = Schema.collection(
        id=ShapeID("com.test#Input"),
        members={
            "values": {
                "target": list_schema,
                "traits": [XmlFlattenedTrait(), XmlNameTrait("Hi")],
            }
        },
    )

    @dataclass
    class Input:
        values: list[str]

        def serialize(self, serializer: ShapeSerializer) -> None:
            with serializer.begin_struct(input_schema) as struct_serializer:
                self.serialize_members(struct_serializer)

        def serialize_members(self, serializer: ShapeSerializer) -> None:
            schema = input_schema.members["values"]
            member_schema = schema.expect_member_target().members["member"]
            with serializer.begin_list(schema, len(self.values)) as list_serializer:
                for value in self.values:
                    list_serializer.write_string(member_schema, value)

    params: list[tuple[str, str]] = []
    serializer = QueryShapeSerializer(
        sink=BytesIO(), action="TestOperation", version="2020-01-08", params=params
    )
    Input(values=["a", "b"]).serialize(serializer)

    assert params == [("Hi.1", "a"), ("Hi.2", "b")]


def test_query_map_serialization_uses_xml_name_traits() -> None:
    map_schema = Schema.collection(
        id=ShapeID("com.test#StringMap"),
        shape_type=ShapeType.MAP,
        members={
            "key": {"target": STRING, "traits": [XmlNameTrait("K")]},
            "value": {"target": STRING, "traits": [XmlNameTrait("V")]},
        },
    )
    params: list[tuple[str, str]] = []
    serializer = QueryShapeSerializer(
        sink=BytesIO(),
        action="TestOperation",
        version="2020-01-08",
        path=("Attributes",),
        params=params,
    )
    with serializer.begin_map(map_schema, 1) as map_serializer:
        map_serializer.entry(
            "one", lambda value_serializer: value_serializer.write_string(STRING, "1")
        )

    assert params == [
        ("Attributes.entry.1.K", "one"),
        ("Attributes.entry.1.V", "1"),
    ]


def test_query_flattened_map_serialization() -> None:
    map_schema = Schema.collection(
        id=ShapeID("com.test#StringMap"),
        shape_type=ShapeType.MAP,
        traits=[XmlFlattenedTrait()],
        members={
            "key": {"target": STRING},
            "value": {"target": STRING},
        },
    )
    params: list[tuple[str, str]] = []
    serializer = QueryShapeSerializer(
        sink=BytesIO(),
        action="TestOperation",
        version="2020-01-08",
        path=("Attributes",),
        params=params,
    )
    with serializer.begin_map(map_schema, 2) as map_serializer:
        map_serializer.entry(
            "one", lambda value_serializer: value_serializer.write_string(STRING, "1")
        )
        map_serializer.entry(
            "two", lambda value_serializer: value_serializer.write_string(STRING, "2")
        )

    assert params == [
        ("Attributes.1.key", "one"),
        ("Attributes.1.value", "1"),
        ("Attributes.2.key", "two"),
        ("Attributes.2.value", "2"),
    ]


def test_query_empty_map_is_omitted() -> None:
    map_schema = Schema.collection(
        id=ShapeID("com.test#StringMap"),
        shape_type=ShapeType.MAP,
        members={
            "key": {"target": STRING},
            "value": {"target": STRING},
        },
    )
    params: list[tuple[str, str]] = []
    serializer = QueryShapeSerializer(
        sink=BytesIO(),
        action="TestOperation",
        version="2020-01-08",
        path=("Attributes",),
        params=params,
    )
    with serializer.begin_map(map_schema, 0):
        pass

    assert params == []


def test_query_null_member_is_omitted() -> None:
    params: list[tuple[str, str]] = []
    serializer = QueryShapeSerializer(
        sink=BytesIO(),
        action="TestOperation",
        version="2020-01-08",
        path=("Nullable",),
        params=params,
    )

    serializer.write_null(STRING)

    assert params == []


def test_query_serializer_flush_writes_body_to_sink() -> None:
    sink = BytesIO()
    serializer = QueryShapeSerializer(
        sink=sink,
        action="TestOperation",
        version="2020-01-08",
        path=("Member Name",),
    )
    serializer.write_string(STRING, "hello world")
    serializer.flush()

    expected = b"Action=TestOperation&Version=2020-01-08&Member%20Name=hello%20world"
    assert sink.getvalue() == expected


def test_query_serializer_flush_omits_action_and_version_when_unset() -> None:
    sink = BytesIO()
    serializer = QueryShapeSerializer(sink=sink, path=("MemberName",))
    serializer.write_string(STRING, "hello world")
    serializer.flush()

    assert sink.getvalue() == b"MemberName=hello%20world"


def test_query_nested_struct_serialization() -> None:
    inner_schema = Schema.collection(
        id=ShapeID("com.test#Inner"),
        members={"value": {"target": STRING}},
    )
    outer_schema = Schema.collection(
        id=ShapeID("com.test#Outer"),
        members={"inner": {"target": inner_schema}},
    )

    @dataclass
    class Inner:
        value: str

        def serialize(self, serializer: ShapeSerializer) -> None:
            serializer.write_struct(inner_schema, self)

        def serialize_members(self, serializer: ShapeSerializer) -> None:
            serializer.write_string(inner_schema.members["value"], self.value)

    @dataclass
    class Outer:
        inner: Inner

        def serialize(self, serializer: ShapeSerializer) -> None:
            serializer.write_struct(outer_schema, self)

        def serialize_members(self, serializer: ShapeSerializer) -> None:
            serializer.write_struct(outer_schema.members["inner"], self.inner)

    params: list[tuple[str, str]] = []
    serializer = QueryShapeSerializer(
        sink=BytesIO(), action="TestOperation", version="2020-01-08", params=params
    )
    Outer(inner=Inner("x")).serialize(serializer)

    assert params == [("inner.value", "x")]
