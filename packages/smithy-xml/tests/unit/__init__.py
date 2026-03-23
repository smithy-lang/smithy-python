# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Self

from smithy_core.deserializers import ShapeDeserializer
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
from smithy_core.shapes import ShapeID, ShapeType
from smithy_core.traits import (
    TimestampFormatTrait,
    XMLAttributeTrait,
    XMLFlattenedTrait,
    XMLNamespaceTrait,
    XMLNameTrait,
)

STRING_LIST_SCHEMA = Schema.collection(
    id=ShapeID("smithy.example#StringList"),
    shape_type=ShapeType.LIST,
    members={
        "member": {
            "target": STRING,
        }
    },
)

STRING_MAP_SCHEMA = Schema.collection(
    id=ShapeID("smithy.example#StringMap"),
    shape_type=ShapeType.MAP,
    members={
        "key": {
            "target": STRING,
        },
        "value": {
            "target": STRING,
        },
    },
)

# List with @xmlName on the member element
RENAMED_LIST_SCHEMA = Schema.collection(
    id=ShapeID("smithy.example#RenamedList"),
    shape_type=ShapeType.LIST,
    members={
        "member": {
            "target": STRING,
            "traits": [XMLNameTrait("item")],
        }
    },
)

# Map with @xmlName on key/value members
RENAMED_MAP_SCHEMA = Schema.collection(
    id=ShapeID("smithy.example#RenamedMap"),
    shape_type=ShapeType.MAP,
    members={
        "key": {
            "target": STRING,
            "traits": [XMLNameTrait("Attribute")],
        },
        "value": {
            "target": STRING,
            "traits": [XMLNameTrait("Setting")],
        },
    },
)

# Map with @xmlName and @xmlNamespace on key/value members
RENAMED_NS_MAP_SCHEMA = Schema.collection(
    id=ShapeID("smithy.example#RenamedNsMap"),
    shape_type=ShapeType.MAP,
    members={
        "key": {
            "target": STRING,
            "traits": [
                XMLNameTrait("K"),
                XMLNamespaceTrait({"uri": "https://the-key.example.com"}),
            ],
        },
        "value": {
            "target": STRING,
            "traits": [
                XMLNameTrait("V"),
                XMLNamespaceTrait({"uri": "https://the-value.example.com"}),
            ],
        },
    },
)

# List with @xmlNamespace on member
NAMESPACED_LIST_SCHEMA = Schema.collection(
    id=ShapeID("smithy.example#NamespacedList"),
    shape_type=ShapeType.LIST,
    members={
        "member": {
            "target": STRING,
            "traits": [XMLNamespaceTrait({"uri": "http://bux.com"})],
        }
    },
)

# Struct with @xmlNamespace (default xmlns)
NAMESPACED_STRUCT_SCHEMA = Schema.collection(
    id=ShapeID("smithy.example#NsStruct"),
    traits=[XMLNamespaceTrait({"uri": "https://example.com"})],
    members={
        "value": {"target": STRING},
    },
)

# Struct with @xmlNamespace (prefixed xmlns)
PREFIXED_NS_STRUCT_SCHEMA = Schema.collection(
    id=ShapeID("smithy.example#PrefixedNsStruct"),
    traits=[XMLNamespaceTrait({"uri": "https://example.com", "prefix": "baz"})],
    members={
        "value": {"target": STRING},
    },
)

SCHEMA: Schema = Schema.collection(
    id=ShapeID("smithy.example#SerdeShape"),
    members={
        "booleanMember": {
            "target": BOOLEAN,
        },
        "integerMember": {
            "target": INTEGER,
        },
        "floatMember": {
            "target": FLOAT,
        },
        "bigDecimalMember": {
            "target": BIG_DECIMAL,
        },
        "stringMember": {
            "target": STRING,
        },
        "xmlNameMember": {
            "target": STRING,
            "traits": [XMLNameTrait("CustomName")],
        },
        "blobMember": {
            "target": BLOB,
        },
        "timestampMember": {
            "target": TIMESTAMP,
        },
        "dateTimeMember": {
            "target": TIMESTAMP,
            "traits": [TimestampFormatTrait("date-time")],
        },
        "httpDateMember": {
            "target": TIMESTAMP,
            "traits": [TimestampFormatTrait("http-date")],
        },
        "epochSecondsMember": {
            "target": TIMESTAMP,
            "traits": [TimestampFormatTrait("epoch-seconds")],
        },
        "listMember": {
            "target": STRING_LIST_SCHEMA,
        },
        "mapMember": {
            "target": STRING_MAP_SCHEMA,
        },
        "structMember": None,
        "xmlAttributeMember": {
            "target": STRING,
            "traits": [XMLAttributeTrait()],
        },
        "renamedListMember": {
            "target": RENAMED_LIST_SCHEMA,
        },
        "flattenedListMember": {
            "target": STRING_LIST_SCHEMA,
            "traits": [XMLFlattenedTrait()],
        },
        "flattenedMapMember": {
            "target": STRING_MAP_SCHEMA,
            "traits": [XMLFlattenedTrait()],
        },
        "flattenedRenamedListMember": {
            "target": STRING_LIST_SCHEMA,
            "traits": [XMLFlattenedTrait(), XMLNameTrait("customItem")],
        },
        "flattenedRenamedMapMember": {
            "target": RENAMED_MAP_SCHEMA,
            "traits": [XMLFlattenedTrait(), XMLNameTrait("KVP")],
        },
        "xmlAttributeNamedMember": {
            "target": STRING,
            "traits": [XMLAttributeTrait(), XMLNameTrait("test")],
        },
    },
)
SCHEMA.members["structMember"] = Schema.member(
    id=SCHEMA.id.with_member("structMember"),
    target=SCHEMA,
    index=13,
)


@dataclass
class SerdeShape:
    boolean_member: bool | None = None
    integer_member: int | None = None
    float_member: float | None = None
    big_decimal_member: Decimal | None = None
    string_member: str | None = None
    xml_name_member: str | None = None
    blob_member: bytes | None = None
    timestamp_member: datetime | None = None
    date_time_member: datetime | None = None
    http_date_member: datetime | None = None
    epoch_seconds_member: datetime | None = None
    list_member: list[str] | None = None
    map_member: dict[str, str] | None = None
    struct_member: "SerdeShape | None" = None
    xml_attribute_member: str | None = None
    renamed_list_member: list[str] | None = None
    flattened_list_member: list[str] | None = None
    flattened_map_member: dict[str, str] | None = None
    flattened_renamed_list_member: list[str] | None = None
    flattened_renamed_map_member: dict[str, str] | None = None
    xml_attribute_named_member: str | None = None

    def serialize(self, serializer: ShapeSerializer):
        serializer.write_struct(SCHEMA, self)

    def serialize_members(self, serializer: ShapeSerializer) -> None:
        if self.boolean_member is not None:
            serializer.write_boolean(
                SCHEMA.members["booleanMember"], self.boolean_member
            )
        if self.integer_member is not None:
            serializer.write_integer(
                SCHEMA.members["integerMember"], self.integer_member
            )
        if self.float_member is not None:
            serializer.write_float(SCHEMA.members["floatMember"], self.float_member)
        if self.big_decimal_member is not None:
            serializer.write_big_decimal(
                SCHEMA.members["bigDecimalMember"], self.big_decimal_member
            )
        if self.string_member is not None:
            serializer.write_string(SCHEMA.members["stringMember"], self.string_member)
        if self.xml_name_member is not None:
            serializer.write_string(
                SCHEMA.members["xmlNameMember"], self.xml_name_member
            )
        if self.blob_member is not None:
            serializer.write_blob(SCHEMA.members["blobMember"], self.blob_member)
        if self.timestamp_member is not None:
            serializer.write_timestamp(
                SCHEMA.members["timestampMember"], self.timestamp_member
            )
        if self.date_time_member is not None:
            serializer.write_timestamp(
                SCHEMA.members["dateTimeMember"], self.date_time_member
            )
        if self.http_date_member is not None:
            serializer.write_timestamp(
                SCHEMA.members["httpDateMember"], self.http_date_member
            )
        if self.epoch_seconds_member is not None:
            serializer.write_timestamp(
                SCHEMA.members["epochSecondsMember"], self.epoch_seconds_member
            )
        if self.list_member is not None:
            schema = SCHEMA.members["listMember"]
            target_schema = schema.expect_member_target().members["member"]
            with serializer.begin_list(schema, len(self.list_member)) as ls:
                for element in self.list_member:
                    ls.write_string(target_schema, element)
        if self.map_member is not None:
            schema = SCHEMA.members["mapMember"]
            target_schema = schema.expect_member_target().members["value"]
            with serializer.begin_map(schema, len(self.map_member)) as ms:
                for key, value in self.map_member.items():
                    ms.entry(key, lambda vs: vs.write_string(target_schema, value))  # type: ignore
        if self.struct_member is not None:
            serializer.write_struct(SCHEMA.members["structMember"], self.struct_member)
        if self.xml_attribute_member is not None:
            serializer.write_string(
                SCHEMA.members["xmlAttributeMember"], self.xml_attribute_member
            )
        if self.renamed_list_member is not None:
            schema = SCHEMA.members["renamedListMember"]
            target_schema = schema.expect_member_target().members["member"]
            with serializer.begin_list(schema, len(self.renamed_list_member)) as ls:
                for element in self.renamed_list_member:
                    ls.write_string(target_schema, element)
        if self.flattened_list_member is not None:
            schema = SCHEMA.members["flattenedListMember"]
            target_schema = schema.expect_member_target().members["member"]
            with serializer.begin_list(schema, len(self.flattened_list_member)) as ls:
                for element in self.flattened_list_member:
                    ls.write_string(target_schema, element)
        if self.flattened_map_member is not None:
            schema = SCHEMA.members["flattenedMapMember"]
            target_schema = schema.expect_member_target().members["value"]
            with serializer.begin_map(schema, len(self.flattened_map_member)) as ms:
                for key, value in self.flattened_map_member.items():
                    ms.entry(key, lambda vs: vs.write_string(target_schema, value))  # type: ignore
        if self.flattened_renamed_list_member is not None:
            schema = SCHEMA.members["flattenedRenamedListMember"]
            target_schema = schema.expect_member_target().members["member"]
            with serializer.begin_list(
                schema, len(self.flattened_renamed_list_member)
            ) as ls:
                for element in self.flattened_renamed_list_member:
                    ls.write_string(target_schema, element)
        if self.flattened_renamed_map_member is not None:
            schema = SCHEMA.members["flattenedRenamedMapMember"]
            target_schema = schema.expect_member_target().members["value"]
            with serializer.begin_map(
                schema, len(self.flattened_renamed_map_member)
            ) as ms:
                for key, value in self.flattened_renamed_map_member.items():
                    ms.entry(key, lambda vs: vs.write_string(target_schema, value))  # type: ignore
        if self.xml_attribute_named_member is not None:
            serializer.write_string(
                SCHEMA.members["xmlAttributeNamedMember"],
                self.xml_attribute_named_member,
            )

    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> Self:
        kwargs: dict[str, Any] = {}

        def _consumer(schema: Schema, de: ShapeDeserializer) -> None:
            match schema.expect_member_index():
                case 0:
                    kwargs["boolean_member"] = de.read_boolean(
                        SCHEMA.members["booleanMember"]
                    )
                case 1:
                    kwargs["integer_member"] = de.read_integer(
                        SCHEMA.members["integerMember"]
                    )
                case 2:
                    kwargs["float_member"] = de.read_float(
                        SCHEMA.members["floatMember"]
                    )
                case 3:
                    kwargs["big_decimal_member"] = de.read_big_decimal(
                        SCHEMA.members["bigDecimalMember"]
                    )
                case 4:
                    kwargs["string_member"] = de.read_string(
                        SCHEMA.members["stringMember"]
                    )
                case 5:
                    kwargs["xml_name_member"] = de.read_string(
                        SCHEMA.members["xmlNameMember"]
                    )
                case 6:
                    kwargs["blob_member"] = de.read_blob(SCHEMA.members["blobMember"])
                case 7:
                    kwargs["timestamp_member"] = de.read_timestamp(
                        SCHEMA.members["timestampMember"]
                    )
                case 8:
                    kwargs["date_time_member"] = de.read_timestamp(
                        SCHEMA.members["dateTimeMember"]
                    )
                case 9:
                    kwargs["http_date_member"] = de.read_timestamp(
                        SCHEMA.members["httpDateMember"]
                    )
                case 10:
                    kwargs["epoch_seconds_member"] = de.read_timestamp(
                        SCHEMA.members["epochSecondsMember"]
                    )
                case 11:
                    list_value: list[str] = []
                    de.read_list(
                        SCHEMA.members["listMember"],
                        lambda d: list_value.append(d.read_string(STRING)),
                    )
                    kwargs["list_member"] = list_value
                case 12:
                    map_value: dict[str, str] = {}
                    de.read_map(
                        SCHEMA.members["mapMember"],
                        lambda k, d: map_value.__setitem__(k, d.read_string(STRING)),
                    )
                    kwargs["map_member"] = map_value
                case 13:
                    kwargs["struct_member"] = SerdeShape.deserialize(de)
                case 14:
                    kwargs["xml_attribute_member"] = de.read_string(
                        SCHEMA.members["xmlAttributeMember"]
                    )
                case 15:
                    renamed_list_value: list[str] = []
                    de.read_list(
                        SCHEMA.members["renamedListMember"],
                        lambda d: renamed_list_value.append(d.read_string(STRING)),
                    )
                    kwargs["renamed_list_member"] = renamed_list_value
                case 16:
                    flat_list_value: list[str] = []
                    de.read_list(
                        SCHEMA.members["flattenedListMember"],
                        lambda d: flat_list_value.append(d.read_string(STRING)),
                    )
                    kwargs["flattened_list_member"] = flat_list_value
                case 17:
                    flat_map_value: dict[str, str] = {}
                    de.read_map(
                        SCHEMA.members["flattenedMapMember"],
                        lambda k, d: flat_map_value.__setitem__(
                            k, d.read_string(STRING)
                        ),
                    )
                    kwargs["flattened_map_member"] = flat_map_value
                case 18:
                    flat_renamed_list: list[str] = []
                    de.read_list(
                        SCHEMA.members["flattenedRenamedListMember"],
                        lambda d: flat_renamed_list.append(d.read_string(STRING)),
                    )
                    kwargs["flattened_renamed_list_member"] = flat_renamed_list
                case 19:
                    flat_renamed_map: dict[str, str] = {}
                    de.read_map(
                        SCHEMA.members["flattenedRenamedMapMember"],
                        lambda k, d: flat_renamed_map.__setitem__(
                            k, d.read_string(STRING)
                        ),
                    )
                    kwargs["flattened_renamed_map_member"] = flat_renamed_map
                case 20:
                    kwargs["xml_attribute_named_member"] = de.read_string(
                        SCHEMA.members["xmlAttributeNamedMember"]
                    )
                case _:
                    raise Exception(f"Unexpected schema: {schema}")

        deserializer.read_struct(schema=SCHEMA, consumer=_consumer)
        return cls(**kwargs)


# ---- Serde test cases ----
# Each entry is (value, xml_bytes) for round-trip testing.
# Inspired by the awsQuery/restXml protocol compliance tests

XML_SERDE_CASES: list[tuple[Any, bytes]] = [
    # Scalars
    (True, b"<Boolean>true</Boolean>"),
    (False, b"<Boolean>false</Boolean>"),
    (1, b"<Integer>1</Integer>"),
    (1.5, b"<Float>1.5</Float>"),
    (float("inf"), b"<Float>Infinity</Float>"),
    (float("-inf"), b"<Float>-Infinity</Float>"),
    (Decimal("1.1"), b"<BigDecimal>1.1</BigDecimal>"),
    (b"value", b"<Blob>dmFsdWU=</Blob>"),
    ("foo", b"<String>foo</String>"),
    (
        datetime(2014, 4, 29, 18, 30, 38, tzinfo=UTC),
        b"<Timestamp>2014-04-29T18:30:38Z</Timestamp>",
    ),
    # Wrapped list — <member> elements
    (
        ["foo", "bar"],
        b"<StringList><member>foo</member><member>bar</member></StringList>",
    ),
    # Wrapped map — <entry><key>…</key><value>…</value></entry>
    (
        {"foo": "bar"},
        b"<StringMap><entry><key>foo</key><value>bar</value></entry></StringMap>",
    ),
    # Struct with single scalar
    (
        SerdeShape(string_member="foo"),
        b"<SerdeShape><stringMember>foo</stringMember></SerdeShape>",
    ),
    (
        SerdeShape(boolean_member=True),
        b"<SerdeShape><booleanMember>true</booleanMember></SerdeShape>",
    ),
    (
        SerdeShape(integer_member=3),
        b"<SerdeShape><integerMember>3</integerMember></SerdeShape>",
    ),
    (
        SerdeShape(float_member=5.5),
        b"<SerdeShape><floatMember>5.5</floatMember></SerdeShape>",
    ),
    (
        SerdeShape(big_decimal_member=Decimal("1.1")),
        b"<SerdeShape><bigDecimalMember>1.1</bigDecimalMember></SerdeShape>",
    ),
    (
        SerdeShape(blob_member=b"value"),
        b"<SerdeShape><blobMember>dmFsdWU=</blobMember></SerdeShape>",
    ),
    # @xmlName — member serialized under custom element name
    (
        SerdeShape(xml_name_member="bar"),
        b"<SerdeShape><CustomName>bar</CustomName></SerdeShape>",
    ),
    # Timestamps with different formats
    (
        SerdeShape(timestamp_member=datetime(2014, 4, 29, 18, 30, 38, tzinfo=UTC)),
        b"<SerdeShape><timestampMember>2014-04-29T18:30:38Z</timestampMember></SerdeShape>",
    ),
    (
        SerdeShape(date_time_member=datetime(2014, 4, 29, 18, 30, 38, tzinfo=UTC)),
        b"<SerdeShape><dateTimeMember>2014-04-29T18:30:38Z</dateTimeMember></SerdeShape>",
    ),
    (
        SerdeShape(http_date_member=datetime(2014, 4, 29, 18, 30, 38, tzinfo=UTC)),
        b"<SerdeShape><httpDateMember>Tue, 29 Apr 2014 18:30:38 GMT</httpDateMember></SerdeShape>",
    ),
    (
        SerdeShape(epoch_seconds_member=datetime(2014, 4, 29, 18, 30, 38, tzinfo=UTC)),
        b"<SerdeShape><epochSecondsMember>1398796238</epochSecondsMember></SerdeShape>",
    ),
    # List inside struct
    (
        SerdeShape(list_member=["foo", "bar"]),
        (
            b"<SerdeShape>"
            b"<listMember><member>foo</member><member>bar</member></listMember>"
            b"</SerdeShape>"
        ),
    ),
    # Map inside struct
    (
        SerdeShape(map_member={"foo": "bar"}),
        (
            b"<SerdeShape>"
            b"<mapMember><entry><key>foo</key><value>bar</value></entry></mapMember>"
            b"</SerdeShape>"
        ),
    ),
    # Nested struct
    (
        SerdeShape(struct_member=SerdeShape(string_member="nested")),
        (
            b"<SerdeShape>"
            b"<structMember><stringMember>nested</stringMember></structMember>"
            b"</SerdeShape>"
        ),
    ),
    # @xmlAttribute — member as attribute on parent element
    (
        SerdeShape(xml_attribute_member="attr_val"),
        b'<SerdeShape xmlAttributeMember="attr_val" />',
    ),
    # List with @xmlName("item") on member
    (
        SerdeShape(renamed_list_member=["foo", "bar"]),
        (
            b"<SerdeShape>"
            b"<renamedListMember><item>foo</item><item>bar</item></renamedListMember>"
            b"</SerdeShape>"
        ),
    ),
    # @xmlFlattened list
    (
        SerdeShape(flattened_list_member=["hi", "bye"]),
        (
            b"<SerdeShape>"
            b"<flattenedListMember>hi</flattenedListMember>"
            b"<flattenedListMember>bye</flattenedListMember>"
            b"</SerdeShape>"
        ),
    ),
    # @xmlFlattened map
    (
        SerdeShape(flattened_map_member={"foo": "Foo", "baz": "Baz"}),
        (
            b"<SerdeShape>"
            b"<flattenedMapMember><key>foo</key><value>Foo</value></flattenedMapMember>"
            b"<flattenedMapMember><key>baz</key><value>Baz</value></flattenedMapMember>"
            b"</SerdeShape>"
        ),
    ),
    # @xmlFlattened + @xmlName on list member
    (
        SerdeShape(flattened_renamed_list_member=["hi", "bye"]),
        (
            b"<SerdeShape>"
            b"<customItem>hi</customItem>"
            b"<customItem>bye</customItem>"
            b"</SerdeShape>"
        ),
    ),
    # @xmlFlattened + @xmlName on map member with renamed key/value
    (
        SerdeShape(flattened_renamed_map_member={"foo": "Foo"}),
        (
            b"<SerdeShape>"
            b"<KVP><Attribute>foo</Attribute><Setting>Foo</Setting></KVP>"
            b"</SerdeShape>"
        ),
    ),
    # @xmlAttribute + @xmlName
    (
        SerdeShape(xml_attribute_named_member="attr_val"),
        b'<SerdeShape test="attr_val" />',
    ),
    # Multiple members in one struct — realistic multi-member test
    (
        SerdeShape(
            boolean_member=True,
            integer_member=42,
            string_member="hello",
            list_member=["a", "b"],
        ),
        (
            b"<SerdeShape>"
            b"<booleanMember>true</booleanMember>"
            b"<integerMember>42</integerMember>"
            b"<stringMember>hello</stringMember>"
            b"<listMember><member>a</member><member>b</member></listMember>"
            b"</SerdeShape>"
        ),
    ),
    # Nested struct 3 levels deep
    (
        SerdeShape(
            struct_member=SerdeShape(struct_member=SerdeShape(string_member="deep"))
        ),
        (
            b"<SerdeShape>"
            b"<structMember><structMember>"
            b"<stringMember>deep</stringMember>"
            b"</structMember></structMember>"
            b"</SerdeShape>"
        ),
    ),
    # XML escaping in text content
    (
        SerdeShape(string_member="<foo&bar>"),
        b"<SerdeShape><stringMember>&lt;foo&amp;bar&gt;</stringMember></SerdeShape>",
    ),
    # Empty collections — wrapper element with no children
    (
        SerdeShape(list_member=[]),
        b"<SerdeShape><listMember /></SerdeShape>",
    ),
    (
        SerdeShape(map_member={}),
        b"<SerdeShape><mapMember /></SerdeShape>",
    ),
]
