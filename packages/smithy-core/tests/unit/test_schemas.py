from dataclasses import replace
from typing import Any

import pytest
from smithy_core.exceptions import ExpectationNotMetError
from smithy_core.schemas import Schema
from smithy_core.shapes import ShapeID, ShapeType
from smithy_core.traits import (
    DynamicTrait,
    InternalTrait,
    SensitiveTrait,
)

ID: ShapeID = ShapeID("ns.foo#bar")
STRING = Schema(id=ShapeID("smithy.api#String"), shape_type=ShapeType.STRING)


def test_traits_list():
    trait = InternalTrait()
    schema = Schema(id=ID, shape_type=ShapeType.STRUCTURE, traits=[trait])
    assert schema.traits == {InternalTrait.id: trait}


def test_get_trait_by_class():
    trait = InternalTrait()
    schema = Schema(id=ID, shape_type=ShapeType.STRUCTURE, traits=[trait])
    assert schema.get_trait(InternalTrait) is trait


def test_get_unknown_trait_by_class():
    trait = InternalTrait()
    schema = Schema(id=ID, shape_type=ShapeType.STRUCTURE, traits=[trait])
    assert schema.get_trait(SensitiveTrait) is None


def test_get_trait_by_id():
    trait = InternalTrait()
    schema = Schema(id=ID, shape_type=ShapeType.STRUCTURE, traits=[trait])
    assert schema.get_trait(InternalTrait.id) is trait


def test_get_unknown_trait_by_id():
    trait = InternalTrait()
    schema = Schema(id=ID, shape_type=ShapeType.STRUCTURE, traits=[trait])
    assert schema.get_trait(SensitiveTrait.id) is None


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
    with pytest.raises(ExpectationNotMetError):
        STRING.expect_member_name()

    with pytest.raises(ExpectationNotMetError):
        STRING.expect_member_target()

    with pytest.raises(ExpectationNotMetError):
        STRING.expect_member_index()


def test_collection_constructor():
    trait_value = DynamicTrait(id=ShapeID("smithy.example#trait"), document_value="foo")
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
        members={member_name: {"target": STRING, "traits": [trait_value]}},
    )
    assert schema.members == {member_name: member}


def test_member_constructor():
    target = Schema.collection(
        id=ShapeID("smithy.example#target"),
        traits=[
            SensitiveTrait(),
            DynamicTrait(id=ShapeID("smithy.example#foo"), document_value="bar"),
        ],
        members={"spam": {"target": STRING}},
    )

    member_id = ShapeID("smithy.example#Spam$eggs")
    expected = replace(
        target,
        id=member_id,
        member_target=target,
        member_index=1,
        traits=[
            SensitiveTrait(),
            DynamicTrait(id=ShapeID("smithy.example#foo"), document_value="baz"),
        ],
    )

    actual = Schema.member(
        id=member_id,
        target=target,
        index=1,
        member_traits=[
            DynamicTrait(id=ShapeID("smithy.example#foo"), document_value="baz")
        ],
    )

    assert actual == expected


def test_member_constructor_asserts_id():
    with pytest.raises(ExpectationNotMetError):
        Schema.member(id=ShapeID("smithy.example#foo"), target=STRING, index=0)


def test_member_constructor_asserts_target_is_not_member():
    target = Schema.member(
        id=ShapeID("smithy.example#Spam$eggs"), target=STRING, index=0
    )
    with pytest.raises(ExpectationNotMetError):
        Schema.member(id=ShapeID("smithy.example#Foo$bar"), target=target, index=0)


@pytest.mark.parametrize(
    "item, contains",
    [
        (SensitiveTrait, True),
        (SensitiveTrait.id, True),
        (InternalTrait, False),
        (InternalTrait.id, False),
        ("baz", True),
        (ID.with_member("baz"), True),
        (ID, False),
    ],
)
def test_contains(item: Any, contains: bool):
    schema = Schema.collection(
        id=ID,
        members={"baz": {"target": STRING}},
        traits=[SensitiveTrait()],
    )

    assert (item in schema) == contains
