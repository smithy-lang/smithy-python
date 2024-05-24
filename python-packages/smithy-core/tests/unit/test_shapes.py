import pytest

from smithy_core.exceptions import ExpectationNotMetException, SmithyException
from smithy_core.shapes import ShapeID


@pytest.mark.parametrize(
    "id,namespace,name,member",
    [
        ("ns.foo#bar", "ns.foo", "bar", None),
        ("ns.foo#bar$baz", "ns.foo", "bar", "baz"),
    ],
)
def test_valid_shape_id(id: str, namespace: str, name: str, member: str | None):
    shape_id = ShapeID(id)

    assert str(shape_id) == id
    assert shape_id.namespace == namespace
    assert shape_id.name == name
    assert shape_id.member == member


@pytest.mark.parametrize(
    "id", ["foo", "#", "ns.foo#", "#foo", "ns.foo#bar$", "ns.foo#$baz", "#$"]
)
def test_invalid_shape_id(id: str):
    with pytest.raises(SmithyException):
        ShapeID(id)


def test_expect_member():
    assert ShapeID("ns.foo#bar$baz").expect_member() == "baz"
    with pytest.raises(ExpectationNotMetException):
        assert ShapeID("ns.foo#bar").expect_member()


def test_from_parts():
    assert ShapeID("ns.foo#bar") == ShapeID.from_parts(namespace="ns.foo", name="bar")
    assert ShapeID("ns.foo#bar$baz") == ShapeID.from_parts(
        namespace="ns.foo", name="bar", member="baz"
    )


def test_with_member():
    assert ShapeID("ns.foo#bar").with_member("baz") == ShapeID("ns.foo#bar$baz")
    assert ShapeID("ns.foo#bar$cleared").with_member("baz") == ShapeID("ns.foo#bar$baz")
