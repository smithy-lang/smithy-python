from dataclasses import replace

import pytest

from smithy_core.exceptions import ExpectationNotMetException
from smithy_core.schemas import Schema
from smithy_core.shapes import ShapeID, ShapeType
from smithy_core.traits import Trait

ID: ShapeID = ShapeID("ns.foo#bar")
STRING = Schema(id=ShapeID("smithy.api#String"), shape_type=ShapeType.STRING)


def test_traits_list():
    trait_id = ShapeID("smithy.api#internal")
    trait = Trait(id=trait_id, value=True)
    schema = Schema(id=ID, shape_type=ShapeType.STRUCTURE, traits=[trait])
    assert schema.traits == {trait_id: trait}


def test_members_list():
    member_name = "baz"
    member = Schema(
        id=ID.with_member(member_name),
        shape_type=ShapeType.STRING,
        member_target=STRING,
        member_index=0,
    )
    schema = Schema(id=ID, shape_type=ShapeType.STRUCTURE, members=[member])
    assert schema.members == {"baz": member}


def test_expect_member_schema():
    member_schema = Schema(
        id=ID.with_member("baz"),
        shape_type=ShapeType.STRING,
        member_target=STRING,
        member_index=0,
    )
    assert member_schema.expect_member_name() == "baz"
    assert member_schema.member_name == "baz"

    assert member_schema.expect_member_target() == STRING
    assert member_schema.member_target == STRING

    assert member_schema.expect_member_index() == 0
    assert member_schema.member_index == 0


def test_member_expectations_raise_on_non_members():
    with pytest.raises(ExpectationNotMetException):
        STRING.expect_member_name()

    with pytest.raises(ExpectationNotMetException):
        STRING.expect_member_target()

    with pytest.raises(ExpectationNotMetException):
        STRING.expect_member_index()


def test_collection_constructor():
    trait_value = Trait(id=ShapeID("smithy.example#trait"), value="foo")
    member_name = "baz"
    member = Schema(
        id=ID.with_member(member_name),
        shape_type=ShapeType.STRING,
        traits=[trait_value],
        member_target=STRING,
        member_index=0,
    )
    schema = Schema.collection(
        id=ID,
        members={member_name: {"target": STRING, "index": 0, "traits": [trait_value]}},
    )
    assert schema.members == {member_name: member}


def test_member_constructor():
    target = Schema.collection(
        id=ShapeID("smithy.example#target"),
        traits=[
            Trait(id=ShapeID("smithy.api#sensitive")),
            Trait(id=ShapeID("smithy.example#foo"), value="bar"),
        ],
        members={"spam": {"target": STRING, "index": 0}},
    )

    member_id = ShapeID("smithy.example#Spam$eggs")
    expected = replace(
        target,
        id=member_id,
        member_target=target,
        member_index=1,
        traits=[
            Trait(id=ShapeID("smithy.api#sensitive")),
            Trait(id=ShapeID("smithy.example#foo"), value="baz"),
        ],
    )

    actual = Schema.member(
        id=member_id,
        target=target,
        index=1,
        member_traits=[Trait(id=ShapeID("smithy.example#foo"), value="baz")],
    )

    assert actual == expected


def test_member_constructor_asserts_id():
    with pytest.raises(ExpectationNotMetException):
        Schema.member(id=ShapeID("smithy.example#foo"), target=STRING, index=0)


def test_member_constructor_asserts_target_is_not_member():
    target = Schema.member(
        id=ShapeID("smithy.example#Spam$eggs"), target=STRING, index=0
    )
    with pytest.raises(ExpectationNotMetException):
        Schema.member(id=ShapeID("smithy.example#Foo$bar"), target=target, index=0)
