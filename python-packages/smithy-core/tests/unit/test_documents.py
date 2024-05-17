from datetime import datetime
from decimal import Decimal

import pytest

from smithy_core.documents import Document, DocumentValue
from smithy_core.exceptions import ExpectationNotMetException
from smithy_core.schemas import Schema
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
    expected = Schema(
        id=id.with_member("member"),
        type=ShapeType.MEMBER,
        member_target=target_schema,
        member_index=0,
    )

    list_schema = Schema.collection(
        id=id,
        type=ShapeType.LIST,
        members={"member": {"target": target_schema}},
    )
    document = Document(["foo"], schema=list_schema)
    actual = document[0]._schema  # pyright: ignore[reportPrivateUsage]
    assert actual == expected


def test_setitem_on_list_passes_schema_to_member_documents() -> None:
    id = ShapeID("smithy.example#List")
    target_schema = Schema(id=ShapeID("smithy.api#String"), type=ShapeType.STRING)
    expected = Schema(
        id=id.with_member("member"),
        type=ShapeType.MEMBER,
        member_target=target_schema,
        member_index=0,
    )

    list_schema = Schema.collection(
        id=id,
        type=ShapeType.LIST,
        members={"member": {"target": target_schema}},
    )
    document = Document(["foo"], schema=list_schema)
    document[0] = "bar"
    actual = document[0]._schema  # pyright: ignore[reportPrivateUsage]
    assert actual == expected


def test_wrap_map_passes_schema_to_member_documents() -> None:
    id = ShapeID("smithy.example#Structure")
    target_schema = Schema(id=ShapeID("smithy.api#String"), type=ShapeType.STRING)
    expected = Schema(
        id=id.with_member("stringMember"),
        type=ShapeType.MEMBER,
        member_target=target_schema,
        member_index=0,
    )

    struct_schema = Schema.collection(
        id=id,
        members={"stringMember": {"target": target_schema}},
    )
    document = Document({"stringMember": "foo"}, schema=struct_schema)
    actual = document["stringMember"]._schema  # pyright: ignore[reportPrivateUsage]
    assert actual == expected


def test_setitem_on_map_passes_schema_to_member_documents() -> None:
    id = ShapeID("smithy.example#Structure")
    target_schema = Schema(id=ShapeID("smithy.api#String"), type=ShapeType.STRING)
    expected = Schema(
        id=id.with_member("stringMember"),
        type=ShapeType.MEMBER,
        member_target=target_schema,
        member_index=0,
    )

    struct_schema = Schema.collection(
        id=id,
        members={"stringMember": {"target": target_schema}},
    )
    document = Document({"stringMember": "foo"}, schema=struct_schema)
    document["stringMember"] = "spam"
    actual = document["stringMember"]._schema  # pyright: ignore[reportPrivateUsage]
    assert actual == expected
