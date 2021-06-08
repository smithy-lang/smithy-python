import pytest

from smithy_python._private.collection import SmithyEntry, SmithyCollection


@pytest.fixture  # type: ignore
def one() -> SmithyEntry[int]:
    return SmithyEntry(1, "one")


@pytest.fixture  # type: ignore
def two() -> SmithyEntry[int]:
    return SmithyEntry(2, "two")


@pytest.fixture  # type: ignore
def three() -> SmithyEntry[int]:
    return SmithyEntry(3, "three")


@pytest.fixture  # type: ignore
def collection() -> SmithyCollection[int]:
    return SmithyCollection()


def test_entry_repr(one: SmithyEntry[int]) -> None:
    assert repr(one) == "SmithyEntry(one)"


def test_add_before(
    collection: SmithyCollection[int],
    one: SmithyEntry[int],
    two: SmithyEntry[int],
    three: SmithyEntry[int],
) -> None:
    collection.add_before(three)
    collection.add_before(two)
    collection.add_before(one)
    assert collection.entries == [one, two, three]


def test_add_after(
    collection: SmithyCollection[int],
    one: SmithyEntry[int],
    two: SmithyEntry[int],
    three: SmithyEntry[int],
) -> None:
    collection.add_after(one)
    collection.add_after(two)
    collection.add_after(three)
    assert collection.entries == [one, two, three]


def test_add_before_relative(
    collection: SmithyCollection[int],
    one: SmithyEntry[int],
    two: SmithyEntry[int],
    three: SmithyEntry[int],
) -> None:
    collection.add_before(three)
    collection.add_before(one, "three")
    collection.add_before(two, "three")
    assert collection.entries == [one, two, three]


def test_add_after_relative(
    collection: SmithyCollection[int],
    one: SmithyEntry[int],
    two: SmithyEntry[int],
    three: SmithyEntry[int],
) -> None:
    collection.add_after(one)
    collection.add_after(three, "one")
    collection.add_after(two, "one")
    assert collection.entries == [one, two, three]
