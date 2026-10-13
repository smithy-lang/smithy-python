# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
# pyright: reportPrivateUsage=false, reportUnusedFunction=false
import threading
from collections.abc import Iterator

import pytest
from smithy_core import _schema_compact
from smithy_core._schema_compact import StaticSchema, hydrate
from smithy_core.shapes import ShapeID, ShapeType
from smithy_core.traits import SensitiveTrait

NS = "ns.example"

# Trait-bit index for a known valueless two-state trait, used to exercise the
# shared-cache path in _expand_traits.
_SENSITIVE_BIT = 1 << _schema_compact._TRAIT_BITS.index(SensitiveTrait.id)


@pytest.fixture(autouse=True)
def _isolate_caches() -> Iterator[None]:
    # The caches are module globals keyed by id(); isolate each test so a tuple
    # built here can't collide with another test's recycled id().
    _schema_compact._cache.clear()
    _schema_compact._traits_cache.clear()
    yield
    _schema_compact._cache.clear()
    _schema_compact._traits_cache.clear()


def _struct(name: str, members: tuple[tuple[str, object], ...]) -> StaticSchema:
    member_names = tuple(m[0] for m in members)
    member_targets = tuple((m[1], 0) for m in members)
    return (ShapeType.STRUCTURE.value, NS, name, 0, member_names, member_targets)


def test_simple_shape_hydrates_and_caches() -> None:
    tup: StaticSchema = (ShapeType.STRING.value, NS, "Str", 0)
    schema = hydrate(tup)
    assert schema.id == ShapeID.from_parts(namespace=NS, name="Str")
    assert schema.shape_type is ShapeType.STRING
    assert hydrate(tup) is schema


def test_prelude_schema_passes_through() -> None:
    from smithy_core import prelude

    assert hydrate(prelude.STRING) is prelude.STRING


def test_members_resolved_by_index() -> None:
    tup = _struct("S", (("a", ShapeType.STRING.value), ("b", ShapeType.INTEGER.value)))
    schema = hydrate(tup)
    by_index = schema.members_by_index
    assert by_index[0].expect_member_name() == "a"
    assert by_index[1].expect_member_name() == "b"


def test_direct_recursion() -> None:
    # A struct with a member targeting itself via a forward-ref thunk.
    tup: StaticSchema = (
        ShapeType.STRUCTURE.value,
        NS,
        "Node",
        0,
        ("next",),
        ((lambda: tup, 0),),
    )
    schema = hydrate(tup)
    assert schema.members["next"].member_target is schema


def test_mutual_recursion() -> None:
    a: StaticSchema = (
        ShapeType.STRUCTURE.value,
        NS,
        "A",
        0,
        ("b",),
        ((lambda: b, 0),),
    )
    b: StaticSchema = (
        ShapeType.STRUCTURE.value,
        NS,
        "B",
        0,
        ("a",),
        ((lambda: a, 0),),
    )
    schema_a = hydrate(a)
    schema_b = hydrate(b)
    assert schema_a.members["b"].member_target is schema_b
    assert schema_b.members["a"].member_target is schema_a


def test_shared_trait_dict_not_corrupted_across_schemas() -> None:
    # Two shapes carrying the same valueless trait bit share the cached trait dict;
    # a member built from either must not mutate the other's traits.
    first: StaticSchema = (ShapeType.STRING.value, NS, "First", _SENSITIVE_BIT)
    second: StaticSchema = (ShapeType.STRING.value, NS, "Second", _SENSITIVE_BIT)
    s1 = hydrate(first)
    s2 = hydrate(second)
    assert s1.get_trait(SensitiveTrait) is not None
    assert s2.get_trait(SensitiveTrait) is not None
    assert s1.traits == s2.traits


def test_failed_hydration_does_not_cache_partial_schema() -> None:
    def boom() -> object:
        raise ValueError("resolve failed")

    tup: StaticSchema = (
        ShapeType.STRUCTURE.value,
        NS,
        "Broken",
        0,
        ("bad",),
        ((boom, 0),),
    )
    with pytest.raises(ValueError):
        hydrate(tup)
    # A retry must re-attempt, not return a half-populated schema from the cache.
    with pytest.raises(ValueError):
        hydrate(tup)
    assert id(tup) not in _schema_compact._cache


def test_cache_pins_keyed_tuple_against_id_recycling() -> None:
    # A transient (non-module-global) tuple must stay referenced by the cache, else
    # its id() can be recycled onto a different tuple and return a stale schema.
    tup: StaticSchema = (ShapeType.STRING.value, NS, "Transient", 0)
    hydrate(tup)
    assert _schema_compact._cache[id(tup)][0] is tup


def test_concurrent_hydration_returns_fully_populated_schema() -> None:
    tup = _struct(
        "Concurrent",
        tuple((f"m{i}", ShapeType.STRING.value) for i in range(8)),
    )
    results: list[object] = []
    barrier = threading.Barrier(16)

    def worker() -> None:
        barrier.wait()
        schema = hydrate(tup)
        # Every thread must observe all members, never a cycle-break empty map.
        results.append(len(schema.members))

    threads = [threading.Thread(target=worker) for _ in range(16)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert results == [8] * 16
