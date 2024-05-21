# pyright: reportPrivateUsage=false
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, cast

import pytest

from smithy_core.documents import Document, DocumentValue, _DocumentSerializer
from smithy_core.exceptions import ExpectationNotMetException
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


@pytest.mark.parametrize(
    "value, expected",
    [
        (True, ShapeType.BOOLEAN),
        ("foo", ShapeType.STRING),
        (1, ShapeType.LONG),
        (1.1, ShapeType.DOUBLE),
        (Decimal("1.1"), ShapeType.BIG_DECIMAL),
        (b"foo", ShapeType.BLOB),
        (datetime(2024, 5, 2), ShapeType.TIMESTAMP),
        (["foo"], ShapeType.LIST),
        ({"foo": "bar"}, ShapeType.DOCUMENT),
        ([Document("foo")], ShapeType.LIST),
        ({"foo": Document("bar")}, ShapeType.DOCUMENT),
    ],
)
def test_type_inference(
    value: DocumentValue | list[Document] | dict[str, Document],
    expected: ShapeType,
) -> None:
    assert Document(value).shape_type == expected


def test_type_inherited_from_schema():
    schema = Schema(id=ShapeID("smithy.api#Short"), type=ShapeType.SHORT)
    assert Document(1, schema=schema).shape_type == ShapeType.SHORT


def test_as_blob() -> None:
    assert Document(b"foo").as_blob() == b"foo"


@pytest.mark.parametrize(
    "value",
    [
        "foo",
        1,
        1.1,
        Decimal("1.1"),
        False,
        None,
        datetime(2024, 5, 2),
        [b"foo"],
        {"foo": b"bar"},
    ],
)
def test_as_blob_invalid(value: DocumentValue) -> None:
    with pytest.raises(ExpectationNotMetException):
        Document(value).as_blob()


def test_as_boolean() -> None:
    assert Document(True).as_boolean() is True


@pytest.mark.parametrize(
    "value",
    [
        "foo",
        1,
        1.1,
        Decimal("1.1"),
        b"foo",
        None,
        datetime(2024, 5, 2),
        [b"foo"],
        {"foo": b"bar"},
    ],
)
def test_as_boolean_invalid(value: DocumentValue) -> None:
    with pytest.raises(ExpectationNotMetException):
        Document(value).as_boolean()


def test_as_string() -> None:
    assert Document("foo").as_string() == "foo"


@pytest.mark.parametrize(
    "value",
    [
        b"foo",
        1,
        1.1,
        Decimal("1.1"),
        False,
        None,
        datetime(2024, 5, 2),
        [b"foo"],
        {"foo": b"bar"},
    ],
)
def test_as_string_invalid(value: DocumentValue) -> None:
    with pytest.raises(ExpectationNotMetException):
        Document(value).as_string()


def test_as_timestamp() -> None:
    assert Document(datetime(2024, 5, 2)).as_timestamp() == datetime(2024, 5, 2)


@pytest.mark.parametrize(
    "value",
    [
        "foo",
        1,
        1.1,
        Decimal("1.1"),
        False,
        None,
        b"foo",
        [b"foo"],
        {"foo": b"bar"},
    ],
)
def test_as_timestamp_invalid(value: DocumentValue) -> None:
    with pytest.raises(ExpectationNotMetException):
        Document(value).as_timestamp()


def test_as_integer() -> None:
    assert Document(1).as_integer() == 1


@pytest.mark.parametrize(
    "value",
    [
        "foo",
        b"foo",
        1.1,
        Decimal("1.1"),
        False,
        None,
        datetime(2024, 5, 2),
        [b"foo"],
        {"foo": b"bar"},
    ],
)
def test_as_integer_invalid(value: DocumentValue) -> None:
    with pytest.raises(ExpectationNotMetException):
        Document(value).as_integer()


def test_as_float() -> None:
    assert Document(1.1).as_float() == 1.1


@pytest.mark.parametrize(
    "value",
    [
        "foo",
        1,
        b"foo",
        Decimal("1.1"),
        False,
        None,
        datetime(2024, 5, 2),
        [b"foo"],
        {"foo": b"bar"},
    ],
)
def test_as_float_invalid(value: DocumentValue) -> None:
    with pytest.raises(ExpectationNotMetException):
        Document(value).as_float()


def test_as_decimal() -> None:
    assert Document(Decimal("1.1")).as_decimal() == Decimal("1.1")


@pytest.mark.parametrize(
    "value",
    [
        "foo",
        1,
        1.1,
        b"foo",
        False,
        None,
        datetime(2024, 5, 2),
        [b"foo"],
        {"foo": b"bar"},
    ],
)
def test_as_decimal_invalid(value: DocumentValue) -> None:
    with pytest.raises(ExpectationNotMetException):
        Document(value).as_decimal()


def test_as_list() -> None:
    assert Document(["foo"]).as_list() == [Document("foo")]
    assert Document([Document("foo")]).as_list() == [Document("foo")]


@pytest.mark.parametrize(
    "value",
    [
        "foo",
        1,
        1.1,
        Decimal("1.1"),
        False,
        None,
        datetime(2024, 5, 2),
        b"foo",
        {"foo": b"bar"},
    ],
)
def test_as_list_invalid(value: DocumentValue) -> None:
    with pytest.raises(ExpectationNotMetException):
        Document(value).as_list()


def test_as_map() -> None:
    assert Document({"foo": "bar"}).as_map() == {"foo": Document("bar")}
    assert Document({"foo": Document("bar")}).as_map() == {"foo": Document("bar")}


@pytest.mark.parametrize(
    "value",
    [
        "foo",
        1,
        1.1,
        Decimal("1.1"),
        False,
        None,
        datetime(2024, 5, 2),
        [b"foo"],
        b"foo",
    ],
)
def test_as_map_invalid(value: DocumentValue) -> None:
    with pytest.raises(ExpectationNotMetException):
        Document(value).as_map()


@pytest.mark.parametrize(
    "value, raw_value",
    [
        ("foo", "foo"),
        (1, 1),
        (1.1, 1.1),
        (Decimal("1.1"), Decimal("1.1")),
        (True, True),
        (None, None),
        (b"foo", b"foo"),
        (datetime(2024, 5, 2), datetime(2024, 5, 2)),
        (["foo"], ["foo"]),
        ([Document("foo")], ["foo"]),
        ({"foo": "bar"}, {"foo": "bar"}),
        ({"foo": Document("bar")}, {"foo": "bar"}),
    ],
)
def test_as_value(
    value: DocumentValue | dict[str, Document] | list[Document],
    raw_value: DocumentValue,
) -> None:
    assert Document(value).as_value() == raw_value


def test_get_from_map() -> None:
    document = Document({"foo": "bar"})
    assert document["foo"] == Document("bar")
    with pytest.raises(KeyError):
        document["baz"]

    with pytest.raises(ExpectationNotMetException):
        document[0]

    assert document.get("foo") == Document("bar")
    assert document.get("baz") is None
    assert document.get("baz", Document("spam")) == Document("spam")


def test_slice_map() -> None:
    document = Document({"foo": "bar"})
    assert document.as_value() == {"foo": "bar"}

    with pytest.raises(ExpectationNotMetException):
        document[1:]


def test_get_from_list() -> None:
    document = Document(["foo"])
    assert document[0] == Document("foo")
    with pytest.raises(IndexError):
        document[1]

    with pytest.raises(ExpectationNotMetException):
        document["foo"]

    with pytest.raises(ExpectationNotMetException):
        document.get(1)  # type: ignore


def test_slice_list() -> None:
    document = Document(["foo", "bar", "baz"])
    assert document.as_value() == ["foo", "bar", "baz"]

    sliced = document[1:]
    assert sliced.as_value() == ["bar", "baz"]


def test_insert_into_map() -> None:
    document = Document({"foo": "bar"})
    assert document.as_value() == {"foo": "bar"}

    document["spam"] = "eggs"
    assert document["spam"] == Document("eggs")

    document["eggs"] = Document("spam")
    assert document["eggs"] == Document("spam")

    assert document.as_value() == {
        "foo": "bar",
        "spam": "eggs",
        "eggs": "spam",
    }

    with pytest.raises(ExpectationNotMetException):
        document[0] = "foo"


def test_insert_into_list() -> None:
    document = Document(["foo", "bar", "baz"])
    assert document.as_value() == ["foo", "bar", "baz"]

    document[1] = "spam"
    assert document[1] == Document("spam")

    document[2] = Document("eggs")
    assert document[2] == Document("eggs")

    assert document.as_value() == ["foo", "spam", "eggs"]

    with pytest.raises(ExpectationNotMetException):
        document["foo"] = "bar"


def test_del_from_map() -> None:
    document = Document({"foo": "bar"})
    assert document.as_value() == {"foo": "bar"}

    del document["foo"]
    assert document.get("foo") is None
    assert document.as_value() == {}


def test_del_from_list() -> None:
    document = Document(["foo", "bar", "baz"])
    assert document.as_value() == ["foo", "bar", "baz"]

    del document[1]
    assert document[1] == Document("baz")
    assert document.as_value() == ["foo", "baz"]


def test_wrap_list_passes_schema_to_member_documents() -> None:
    id = ShapeID("smithy.example#List")
    target_schema = Schema(id=ShapeID("smithy.api#String"), type=ShapeType.STRING)
    list_schema = Schema.collection(
        id=id,
        type=ShapeType.LIST,
        members={"member": {"target": target_schema}},
    )
    document = Document(["foo"], schema=list_schema)
    actual = document[0]._schema  # pyright: ignore[reportPrivateUsage]
    assert actual == target_schema


def test_setitem_on_list_passes_schema_to_member_documents() -> None:
    id = ShapeID("smithy.example#List")
    target_schema = Schema(id=ShapeID("smithy.api#String"), type=ShapeType.STRING)
    list_schema = Schema.collection(
        id=id,
        type=ShapeType.LIST,
        members={"member": {"target": target_schema}},
    )
    document = Document(["foo"], schema=list_schema)
    document[0] = "bar"
    actual = document[0]._schema  # pyright: ignore[reportPrivateUsage]
    assert actual == target_schema


def test_wrap_structure_passes_schema_to_member_documents() -> None:
    id = ShapeID("smithy.example#Structure")
    target_schema = Schema(id=ShapeID("smithy.api#String"), type=ShapeType.STRING)
    struct_schema = Schema.collection(
        id=id,
        members={"stringMember": {"target": target_schema}},
    )
    document = Document({"stringMember": "foo"}, schema=struct_schema)
    actual = document["stringMember"]._schema  # pyright: ignore[reportPrivateUsage]
    assert actual == target_schema


def test_setitem_on_structure_passes_schema_to_member_documents() -> None:
    id = ShapeID("smithy.example#Structure")
    target_schema = Schema(id=ShapeID("smithy.api#String"), type=ShapeType.STRING)
    struct_schema = Schema.collection(
        id=id,
        members={"stringMember": {"target": target_schema}},
    )
    document = Document({"stringMember": "foo"}, schema=struct_schema)
    document["stringMember"] = "spam"
    actual = document["stringMember"]._schema  # pyright: ignore[reportPrivateUsage]
    assert actual == target_schema


def test_wrap_map_passes_schema_to_member_documents() -> None:
    id = ShapeID("smithy.example#Map")
    map_schema = Schema.collection(
        id=id,
        type=ShapeType.MAP,
        members={
            "key": {"target": STRING},
            "value": {"target": STRING},
        },
    )
    document = Document({"spam": "eggs"}, schema=map_schema)
    actual = document["spam"]._schema  # pyright: ignore[reportPrivateUsage]
    assert actual == STRING


def test_setitem_on_map_passes_schema_to_member_documents() -> None:
    id = ShapeID("smithy.example#Map")
    map_schema = Schema.collection(
        id=id,
        type=ShapeType.MAP,
        members={
            "key": {"target": STRING},
            "value": {"target": STRING},
        },
    )
    document = Document({"spam": "eggs"}, schema=map_schema)
    document["spam"] = "eggsandspam"
    actual = document["spam"]._schema  # pyright: ignore[reportPrivateUsage]
    assert actual == STRING


STRING_LIST_SCHEMA = Schema.collection(
    id=ShapeID("smithy.example#StringList"),
    type=ShapeType.LIST,
    members={"member": {"target": STRING}},
)
STRING_MAP_SCHEMA = Schema.collection(
    id=ShapeID("smithy.example#StringMap"),
    type=ShapeType.MAP,
    members={"key": {"target": STRING}, "value": {"target": STRING}},
)
SCHEMA: Schema = Schema.collection(
    id=ShapeID("smithy.example#DocumentSerdeShape"),
    members={
        "booleanMember": {"target": BOOLEAN},
        "integerMember": {"target": INTEGER},
        "floatMember": {"target": FLOAT},
        "bigDecimalMember": {"target": BIG_DECIMAL},
        "stringMember": {"target": STRING},
        "blobMember": {"target": BLOB},
        "timestampMember": {"target": TIMESTAMP},
        "documentMember": {"target": DOCUMENT},
        "listMember": {"target": STRING_LIST_SCHEMA},
        "mapMember": {"target": STRING_MAP_SCHEMA},
    },
)
SCHEMA.members["structMember"] = Schema(
    id=SCHEMA.id.with_member("structMember"),
    type=ShapeType.MEMBER,
    member_target=SCHEMA,
    member_index=len(SCHEMA.members),
)


@dataclass
class DocumentSerdeShape:
    boolean_member: bool | None = None
    integer_member: int | None = None
    float_member: float | None = None
    big_decimal_member: Decimal | None = None
    string_member: str | None = None
    blob_member: bytes | None = None
    timestamp_member: datetime | None = None
    document_member: Document | None = None
    list_member: list[str] | None = None
    map_member: dict[str, str] | None = None
    struct_member: "DocumentSerdeShape | None" = None

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
        if self.blob_member is not None:
            serializer.write_blob(SCHEMA.members["blobMember"], self.blob_member)
        if self.timestamp_member is not None:
            serializer.write_timestamp(
                SCHEMA.members["timestampMember"], self.timestamp_member
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


DOCUMENT_SERDE_CASES = [
    (True, Document(True, schema=BOOLEAN)),
    (1, Document(1, schema=INTEGER)),
    (1.1, Document(1.1, schema=FLOAT)),
    (Decimal("1.1"), Document(Decimal("1.1"), schema=BIG_DECIMAL)),
    (b"foo", Document(b"foo", schema=BLOB)),
    ("foo", Document("foo", schema=STRING)),
    (datetime(2024, 5, 15), Document(datetime(2024, 5, 15))),
    (Document(None), Document(None)),
    (
        ["foo"],
        Document([Document("foo", schema=STRING)], schema=SCHEMA.members["listMember"]),
    ),
    (
        {"foo": "bar"},
        Document(
            {"foo": Document("bar", schema=STRING)},
            schema=SCHEMA.members["mapMember"],
        ),
    ),
    (
        DocumentSerdeShape(boolean_member=True),
        Document({"booleanMember": Document(True, schema=BOOLEAN)}, schema=SCHEMA),
    ),
    (
        DocumentSerdeShape(integer_member=1),
        Document({"integerMember": Document(1, schema=INTEGER)}, schema=SCHEMA),
    ),
    (
        DocumentSerdeShape(float_member=1.1),
        Document({"floatMember": Document(1.1, schema=FLOAT)}, schema=SCHEMA),
    ),
    (
        DocumentSerdeShape(big_decimal_member=Decimal("1.1")),
        Document(
            {"bigDecimalMember": Document(Decimal("1.1"), schema=BIG_DECIMAL)},
            schema=SCHEMA,
        ),
    ),
    (
        DocumentSerdeShape(blob_member=b"foo"),
        Document({"blobMember": Document(b"foo", schema=BLOB)}, schema=SCHEMA),
    ),
    (
        DocumentSerdeShape(string_member="foo"),
        Document({"stringMember": Document("foo", schema=STRING)}, schema=SCHEMA),
    ),
    (
        DocumentSerdeShape(timestamp_member=datetime(2024, 5, 15)),
        Document(
            {"timestampMember": Document(datetime(2024, 5, 15), schema=TIMESTAMP)},
            schema=SCHEMA,
        ),
    ),
    (
        DocumentSerdeShape(document_member=Document(None)),
        Document({"documentMember": Document(None)}, schema=SCHEMA),
    ),
    (
        DocumentSerdeShape(list_member=["foo"]),
        Document(
            {
                "listMember": Document(
                    [Document("foo", schema=STRING)],
                    schema=SCHEMA.members["listMember"],
                )
            },
            schema=SCHEMA,
        ),
    ),
    (
        DocumentSerdeShape(map_member={"foo": "bar"}),
        Document(
            {
                "mapMember": Document(
                    {"foo": Document("bar", schema=STRING)},
                    schema=SCHEMA.members["mapMember"],
                )
            },
            schema=SCHEMA,
        ),
    ),
    (
        DocumentSerdeShape(struct_member=DocumentSerdeShape(string_member="foo")),
        Document(
            {
                "structMember": Document(
                    {"stringMember": Document("foo", schema=STRING)}, schema=SCHEMA
                )
            },
            schema=SCHEMA,
        ),
    ),
]


@pytest.mark.parametrize("given, expected", DOCUMENT_SERDE_CASES)
def test_document_serializer(given: Any, expected: Document):
    serializer = _DocumentSerializer()
    match given:
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
            serializer.write_document(DOCUMENT, given)
        case list():
            given = cast(list[str], given)
            with serializer.begin_list(STRING_LIST_SCHEMA) as list_serializer:
                member_schema = STRING_LIST_SCHEMA.members["member"]
                for e in given:
                    list_serializer.write_string(member_schema, e)
        case dict():
            given = cast(dict[str, str], given)
            with serializer.begin_map(STRING_MAP_SCHEMA) as map_serializer:
                member_schema = STRING_MAP_SCHEMA.members["value"]
                for k, v in given.items():
                    map_serializer.entry(
                        k, lambda vs: vs.write_string(member_schema, v)
                    )
        case DocumentSerdeShape():
            given.serialize(serializer)
        case _:
            raise Exception(f"Unexpected type: {type(given)}")

    actual = serializer.expect_result()
    assert actual.as_value() == expected.as_value()
    assert actual == expected


def test_from_shape() -> None:
    result = Document.from_shape(DocumentSerdeShape(string_member="foo"))
    assert result == Document(
        {"stringMember": Document("foo", schema=STRING)}, schema=SCHEMA
    )
