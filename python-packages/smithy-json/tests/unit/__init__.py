from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Self

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
from smithy_core.schemas import Schema
from smithy_core.serializers import ShapeSerializer
from smithy_core.shapes import ShapeID, ShapeType
from smithy_core.traits import Trait

from smithy_json._private.traits import JSON_NAME, TIMESTAMP_FORMAT

STRING_LIST_SCHEMA = Schema.collection(
    id=ShapeID("smithy.example#StringList"),
    shape_type=ShapeType.LIST,
    members={"member": {"target": STRING}},
)
STRING_MAP_SCHEMA = Schema.collection(
    id=ShapeID("smithy.example#StringMap"),
    shape_type=ShapeType.MAP,
    members={"key": {"target": STRING}, "value": {"target": STRING}},
)
SCHEMA: Schema = Schema.collection(
    id=ShapeID("smithy.example#SerdeShape"),
    members={
        "booleanMember": {"target": BOOLEAN},
        "integerMember": {"target": INTEGER},
        "floatMember": {"target": FLOAT},
        "bigDecimalMember": {"target": BIG_DECIMAL},
        "stringMember": {"target": STRING},
        "jsonNameMember": {
            "target": STRING,
            "traits": [Trait(id=JSON_NAME, value="jsonName")],
        },
        "blobMember": {"target": BLOB},
        "timestampMember": {"target": TIMESTAMP},
        "dateTimeMember": {
            "target": TIMESTAMP,
            "traits": [Trait(id=TIMESTAMP_FORMAT, value="date-time")],
        },
        "httpDateMember": {
            "target": TIMESTAMP,
            "traits": [Trait(id=TIMESTAMP_FORMAT, value="http-date")],
        },
        "epochSecondsMember": {
            "target": TIMESTAMP,
            "traits": [Trait(id=TIMESTAMP_FORMAT, value="epoch-seconds")],
        },
        "documentMember": {"target": DOCUMENT},
        "listMember": {"target": STRING_LIST_SCHEMA},
        "mapMember": {"target": STRING_MAP_SCHEMA},
    },
)
SCHEMA.members["structMember"] = Schema.member(
    id=SCHEMA.id.with_member("structMember"),
    target=SCHEMA,
    index=len(SCHEMA.members),
)


@dataclass
class SerdeShape:
    boolean_member: bool | None = None
    integer_member: int | None = None
    float_member: float | None = None
    big_decimal_member: Decimal | None = None
    string_member: str | None = None
    json_name_member: str | None = None
    blob_member: bytes | None = None
    timestamp_member: datetime | None = None
    date_time_member: datetime | None = None
    http_date_member: datetime | None = None
    epoch_seconds_member: datetime | None = None
    document_member: Document | None = None
    list_member: list[str] | None = None
    map_member: dict[str, str] | None = None
    struct_member: "SerdeShape | None" = None

    def serialize(self, serializer: ShapeSerializer):
        with serializer.begin_struct(SCHEMA) as s:
            self.serialize_members(s)

    def serialize_members(self, serializer: ShapeSerializer) -> None:
        """Serialize structure members using the given serializer.

        :param serializer: The serializer to write member data to.
        """
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
        if self.json_name_member is not None:
            serializer.write_string(
                SCHEMA.members["jsonNameMember"], self.json_name_member
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
        if self.document_member is not None:
            serializer.write_document(
                SCHEMA.members["documentMember"], self.document_member
            )
        if self.list_member is not None:
            schema = SCHEMA.members["listMember"]
            target_schema = schema.expect_member_target().members["member"]
            with serializer.begin_list(schema) as ls:
                for element in self.list_member:
                    ls.write_string(target_schema, element)
        if self.map_member is not None:
            schema = SCHEMA.members["mapMember"]
            target_schema = schema.expect_member_target().members["value"]
            with serializer.begin_map(schema) as ms:
                for key, value in self.map_member.items():
                    ms.entry(key, lambda vs: vs.write_string(target_schema, value))
        if self.struct_member is not None:
            serializer.write_struct(SCHEMA.members["structMember"], self.struct_member)

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
                    kwargs["json_name_member"] = de.read_string(
                        SCHEMA.members["jsonNameMember"]
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
                    kwargs["document_member"] = de.read_document(
                        SCHEMA.members["documentMember"]
                    )
                case 12:
                    list_value: list[str] = []
                    de.read_list(
                        SCHEMA.members["listMember"],
                        lambda d: list_value.append(d.read_string(STRING)),
                    )
                    kwargs["list_member"] = list_value
                case 13:
                    map_value: dict[str, str] = {}
                    de.read_map(
                        SCHEMA.members["mapMember"],
                        lambda k, d: map_value.__setitem__(k, d.read_string(STRING)),
                    )
                    kwargs["map_member"] = map_value
                case 14:
                    kwargs["struct_member"] = SerdeShape.deserialize(de)
                case _:
                    # In actual generated code, this will just log in order to ignore
                    # unknown members.
                    raise Exception(f"Unexpected schema: {schema}")

        deserializer.read_struct(schema=SCHEMA, consumer=_consumer)
        return cls(**kwargs)


JSON_SERDE_CASES = [
    (True, b"true"),
    (1, b"1"),
    (1.1, b"1.1"),
    (Decimal("1.1"), b"1.1"),
    (b"foo", b'"Zm9v"'),
    ("foo", b'"foo"'),
    (datetime(2024, 5, 15, tzinfo=timezone.utc), b'"2024-05-15T00:00:00Z"'),
    (None, b"null"),
    (["foo"], b'["foo"]'),
    ({"foo": "bar"}, b'{"foo":"bar"}'),
    (SerdeShape(boolean_member=True), b'{"booleanMember":true}'),
    (SerdeShape(integer_member=1), b'{"integerMember":1}'),
    (SerdeShape(float_member=1.1), b'{"floatMember":1.1}'),
    (SerdeShape(big_decimal_member=Decimal("1.1")), b'{"bigDecimalMember":1.1}'),
    (SerdeShape(blob_member=b"foo"), b'{"blobMember":"Zm9v"}'),
    (SerdeShape(string_member="foo"), b'{"stringMember":"foo"}'),
    (SerdeShape(json_name_member="foo"), b'{"jsonName":"foo"}'),
    (
        SerdeShape(timestamp_member=datetime(2024, 5, 15, tzinfo=timezone.utc)),
        b'{"timestampMember":"2024-05-15T00:00:00Z"}',
    ),
    (
        SerdeShape(date_time_member=datetime(2024, 5, 15, tzinfo=timezone.utc)),
        b'{"dateTimeMember":"2024-05-15T00:00:00Z"}',
    ),
    (
        SerdeShape(http_date_member=datetime(2024, 5, 15, tzinfo=timezone.utc)),
        b'{"httpDateMember":"Wed, 15 May 2024 00:00:00 GMT"}',
    ),
    (
        SerdeShape(epoch_seconds_member=datetime(2024, 5, 15, tzinfo=timezone.utc)),
        b'{"epochSecondsMember":1715731200}',
    ),
    (SerdeShape(document_member=Document(None)), b'{"documentMember":null}'),
    (SerdeShape(list_member=["foo"]), b'{"listMember":["foo"]}'),
    (SerdeShape(map_member={"foo": "bar"}), b'{"mapMember":{"foo":"bar"}}'),
    (
        SerdeShape(struct_member=SerdeShape(string_member="foo")),
        b'{"structMember":{"stringMember":"foo"}}',
    ),
    (Document(True, schema=BOOLEAN), b"true"),
    (Document(True, schema=DOCUMENT), b"true"),
    (Document(1, schema=INTEGER), b"1"),
    (Document(1, schema=DOCUMENT), b"1"),
    (Document(1.1, schema=FLOAT), b"1.1"),
    (Document(Decimal("1.1"), schema=BIG_DECIMAL), b"1.1"),
    (Document(Decimal("1.1"), schema=DOCUMENT), b"1.1"),
    (Document(b"foo", schema=BLOB), b'"Zm9v"'),
    (Document("foo", schema=STRING), b'"foo"'),
    (Document("foo", schema=DOCUMENT), b'"foo"'),
    (
        Document(datetime(2024, 5, 15, tzinfo=timezone.utc), schema=TIMESTAMP),
        b'"2024-05-15T00:00:00Z"',
    ),
    (
        Document(
            datetime(2024, 5, 15, tzinfo=timezone.utc),
            schema=SCHEMA.members["dateTimeMember"],
        ),
        b'"2024-05-15T00:00:00Z"',
    ),
    (
        Document(
            datetime(2024, 5, 15, tzinfo=timezone.utc),
            schema=SCHEMA.members["httpDateMember"],
        ),
        b'"Wed, 15 May 2024 00:00:00 GMT"',
    ),
    (
        Document(
            datetime(2024, 5, 15, tzinfo=timezone.utc),
            schema=SCHEMA.members["epochSecondsMember"],
        ),
        b"1715731200",
    ),
    (Document(None, schema=STRING), b"null"),
    (Document(None, schema=DOCUMENT), b"null"),
    (Document(["foo"], schema=SCHEMA.members["listMember"]), b'["foo"]'),
    (Document(["foo"], schema=DOCUMENT), b'["foo"]'),
    (Document({"foo": "bar"}, schema=SCHEMA.members["mapMember"]), b'{"foo":"bar"}'),
    (Document({"foo": "bar"}, schema=DOCUMENT), b'{"foo":"bar"}'),
    (Document({"jsonNameMember": "foo"}, schema=SCHEMA), b'{"jsonName":"foo"}'),
    (Document({"jsonNameMember": "foo"}, schema=DOCUMENT), b'{"jsonNameMember":"foo"}'),
]

JSON_SERIALIZATION_CASES = JSON_SERDE_CASES.copy()
JSON_SERIALIZATION_CASES.extend(
    [
        (Document(1.1, schema=DOCUMENT), b"1.1"),
        (Document(b"foo", schema=DOCUMENT), b'"Zm9v"'),
        (
            Document(datetime(2024, 5, 15, tzinfo=timezone.utc), schema=DOCUMENT),
            b'"2024-05-15T00:00:00Z"',
        ),
    ]
)
