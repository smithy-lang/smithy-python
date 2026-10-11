#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import dataclasses

from smithy_test import deep_equal, xml_equal


@dataclasses.dataclass
class Point:
    x: float
    y: float


def test_nan_equal() -> None:
    assert deep_equal(float("nan"), float("nan"))
    assert deep_equal(Point(1.0, float("nan")), Point(1.0, float("nan")))


def test_scalars() -> None:
    assert deep_equal(1, 1)
    assert deep_equal("a", "a")
    assert deep_equal(1.5, 1.5)
    assert not deep_equal(1, 2)
    assert not deep_equal(float("nan"), 1.0)


def test_scalar_type_mismatch() -> None:
    # bool is an int subclass and 1.0 == 1, but distinct wire types must not compare equal.
    assert not deep_equal(1, True)
    assert not deep_equal(0, False)
    assert not deep_equal(1.0, 1)


def test_nested_containers() -> None:
    assert deep_equal([1, [2, 3]], [1, [2, 3]])
    assert deep_equal({"a": [1.0]}, {"a": [1.0]})
    assert deep_equal((1, 2), [1, 2])
    assert not deep_equal([1, 2], [1, 2, 3])
    assert not deep_equal({"a": 1}, {"b": 1})


def test_dataclass_type_mismatch() -> None:
    @dataclasses.dataclass
    class Other:
        x: float
        y: float

    assert not deep_equal(Point(1.0, 2.0), Other(1.0, 2.0))


def test_xml_equal_ignores_formatting_and_member_order() -> None:
    assert xml_equal(
        b'<A xmlns="urn:x" b="2" a="1"><y>2</y><x> 1 </x></A>',
        b'<A a="1" b="2" xmlns="urn:x">\n  <x>1</x>\n  <y>2</y>\n</A>',
    )


def test_xml_equal_keeps_same_named_sibling_order() -> None:
    assert not xml_equal(
        b"<L><member>1</member><member>2</member></L>",
        b"<L><member>2</member><member>1</member></L>",
    )


def test_xml_equal_compares_namespace_declarations() -> None:
    assert not xml_equal(b'<A xmlns:p="urn:x"/>', b"<A/>")
    assert not xml_equal(b"<A>1</A>", b"<A>2</A>")
