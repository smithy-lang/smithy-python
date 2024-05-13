import pytest
from smithy_core.exceptions import ExpectationNotMetException
from smithy_core.schemas import Schema
from smithy_core.shapes import ShapeID, ShapeType
from smithy_core.traits import Trait

ID: ShapeID = ShapeID("ns.foo#bar")
STRING = Schema(id=ShapeID("smithy.api#String"), type=ShapeType.STRING)


def test_traits_list():
    trait_id = ShapeID("smithy.api#internal")
    trait = Trait(id=trait_id, value=True)
    schema = Schema(id=ID, type=ShapeType.STRUCTURE, traits=[trait])
    assert schema.traits == {trait_id: trait}


def test_members_list():
    member_name = "baz"
    member = Schema(
        id=ID.with_member(member_name),
        type=ShapeType.MEMBER,
        member_target=STRING,
        member_index=0,
    )
    schema = Schema(id=ID, type=ShapeType.STRUCTURE, members=[member])
    assert schema.members == {"baz": member}


def test_expect_member_schema():
    member_schema = Schema(
        id=ID.with_member("baz"),
        type=ShapeType.MEMBER,
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
    member_name = "baz"
    member = Schema(
        id=ID.with_member(member_name),
        type=ShapeType.MEMBER,
        member_target=STRING,
        member_index=0,
    )
    schema = Schema.collection(id=ID, members={member_name: {"target": STRING}})
    assert schema.members == {member_name: member}
