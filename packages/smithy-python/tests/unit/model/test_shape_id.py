# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import pytest
from smithy_python.model import InvalidShapeIdError, ShapeId


def test_parse_absolute_shape_id() -> None:
    shape_id = ShapeId.from_string("com.example#Foo")
    assert shape_id.namespace == "com.example"
    assert shape_id.name == "Foo"
    assert shape_id.member is None
    assert str(shape_id) == "com.example#Foo"
    assert not shape_id.is_member


def test_parse_member_shape_id() -> None:
    shape_id = ShapeId.from_string("com.example#Foo$bar_1")
    assert shape_id.member == "bar_1"
    assert shape_id.is_member
    assert str(shape_id) == "com.example#Foo$bar_1"
    assert shape_id.root == ShapeId("com.example", "Foo")
    assert shape_id.with_member("baz") == ShapeId("com.example", "Foo", "baz")


def test_parse_relative_shape_id_uses_default_namespace() -> None:
    assert ShapeId.from_string("Foo", default_namespace="a.b") == ShapeId("a.b", "Foo")
    assert ShapeId.from_string("Foo$m", default_namespace="a.b") == ShapeId(
        "a.b", "Foo", "m"
    )


def test_relative_shape_id_without_namespace_fails() -> None:
    with pytest.raises(InvalidShapeIdError, match="Foo"):
        ShapeId.from_string("Foo")


@pytest.mark.parametrize(
    "value",
    [
        "",
        "#Foo",
        "a.b#",
        "a..b#Foo",
        "a.b#Foo$",
        "a.b#1Foo",
        "2example#Foo",
        "a.b#Foo$2bar",
        "a.b#___",
        "a.b#Foo$___",
        "a.b#Foo$m$n",
        "a#b#C",
        "a.b#Fo o",
        "_#Foo",
        ".a#Foo",
    ],
)
def test_invalid_shape_ids(value: str) -> None:
    with pytest.raises(InvalidShapeIdError):
        ShapeId.from_string(value)


def test_constructor_validates_parts() -> None:
    with pytest.raises(InvalidShapeIdError):
        ShapeId("a.b", "Foo", "")
    with pytest.raises(InvalidShapeIdError):
        ShapeId("", "Foo")


def test_shape_ids_are_hashable_and_ordered() -> None:
    ids = [
        ShapeId.from_string("b#A"),
        ShapeId.from_string("a#B$z"),
        ShapeId.from_string("a#B"),
        ShapeId.from_string("a#B$a"),
    ]
    assert sorted(ids) == [
        ShapeId.from_string("a#B"),
        ShapeId.from_string("a#B$a"),
        ShapeId.from_string("a#B$z"),
        ShapeId.from_string("b#A"),
    ]
    assert len({*ids, ShapeId.from_string("b#A")}) == 4
    assert ShapeId.from_string("a#B") == ShapeId("a", "B")


@pytest.mark.parametrize("name", ["_2HTTPServer", "__2", "_0"])
def test_digits_after_leading_underscores(name: str) -> None:
    value = f"{name}.example#{name}${name}"
    shape_id = ShapeId.from_string(value)
    assert shape_id == ShapeId(f"{name}.example", name, name)
    assert str(shape_id) == value


def test_underscore_identifiers_allowed() -> None:
    shape_id = ShapeId.from_string("a_b.c#_Foo$_x")
    assert shape_id.namespace == "a_b.c"
    assert shape_id.name == "_Foo"
