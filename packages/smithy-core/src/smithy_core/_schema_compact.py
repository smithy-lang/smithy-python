#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""On-demand hydration of compact, tuple-encoded schemas.

Generated ``_private/schemas.py`` files are pure data: each shape is bound to a
module global holding a positional tuple led by its :py:class:`ShapeType` integer.
No :py:class:`Schema` objects are built at import. :py:func:`hydrate` turns a tuple
into a cached :py:class:`Schema` on first use; the cache is keyed by the tuple's
identity (``id()``), which is stable because the tuples are module-level constants
that live for the process. Generated serialize/deserialize code calls
:py:func:`hydrate` once per shape per operation and reaches members positionally
via :py:meth:`Schema.member_at`.

Encoding (mirrors smithy-typescript StaticSchema / StringStore / numeric traits):

- Simple shape:      ``(type_int, namespace, name, traits)``
- Collection shape:  ``(type_int, namespace, name, traits, member_names, member_targets)``
- Operation/service: ``(type_int, namespace, name, traits)``

``member_targets`` is a tuple of ``(target, member_traits)`` pairs where ``target``
is a prelude integer (see ``_PRELUDE``), a sibling shape's tuple, or a
``lambda: SIBLING`` thunk for a forward/recursive reference.

``traits`` is an ``int`` bit-vector over the valueless two-state traits in
``_TRAIT_BITS`` (OR together for any combination), or a ``dict`` of interned trait
id -> value for valued/unknown traits (also carrying any valueless ones present).
"""

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, cast

from . import prelude
from .schemas import Schema
from .shapes import ShapeID, ShapeType
from .traits import DynamicTrait, Trait

if TYPE_CHECKING:
    from .documents import DocumentValue

# A compact schema is a positional tuple led by its ShapeType int.
type StaticSchema = tuple[Any, ...]
# A member target: a prelude int, a sibling tuple, or a lambda returning one. A built
# Schema is also accepted so an operation can be hand-initialized with real schemas.
type StaticSchemaRef = int | StaticSchema | Schema | Callable[[], "StaticSchemaRef"]
type StaticSchemaTraits = int | dict[str, "DocumentValue"]
# An operation's compact schema. The leading four slots are its own shape definition
# (type int, namespace, name, traits); the trailing three carry references to the
# input, output, and error schemas, so one value describes the whole operation. A ref
# may be a compact tuple, a built Schema, a prelude int, or a lambda returning one.
# Kept permissive (not a fixed-arity tuple) so a generated literal -- whose nested
# refs and valued-trait dicts have precise, partially-inferred element types -- still
# assigns under strict type checking.
type StaticOperationSchema = tuple[Any, ...]

# Prelude integer substitutes. Index == the prelude shape's ShapeType value, so a
# bare simple-shape type int doubles as its prelude reference.
_PRELUDE: dict[int, Schema] = {
    ShapeType.BLOB.value: prelude.BLOB,
    ShapeType.BOOLEAN.value: prelude.BOOLEAN,
    ShapeType.STRING.value: prelude.STRING,
    ShapeType.TIMESTAMP.value: prelude.TIMESTAMP,
    ShapeType.BYTE.value: prelude.BYTE,
    ShapeType.SHORT.value: prelude.SHORT,
    ShapeType.INTEGER.value: prelude.INTEGER,
    ShapeType.LONG.value: prelude.LONG,
    ShapeType.FLOAT.value: prelude.FLOAT,
    ShapeType.DOUBLE.value: prelude.DOUBLE,
    ShapeType.BIG_INTEGER.value: prelude.BIG_INTEGER,
    ShapeType.BIG_DECIMAL.value: prelude.BIG_DECIMAL,
    ShapeType.DOCUMENT.value: prelude.DOCUMENT,
}

# The UNIT prelude schema, referenced by enum members. Given its own sentinel so it
# does not collide with a simple-type substitute.
UNIT = -1
_PRELUDE[UNIT] = prelude.UNIT

# Bit index -> trait id for valueless two-state traits. OR of bits encodes any
# combination; the width here allows well over 255 distinct combinations.
_TRAIT_BITS: tuple[str, ...] = (
    "smithy.api#required",
    "smithy.api#idempotencyToken",
    "smithy.api#sensitive",
    "smithy.api#httpLabel",
    "smithy.api#httpPayload",
    "smithy.api#idempotent",
    "smithy.api#sparse",
    "smithy.api#httpResponseCode",
    "smithy.api#hostLabel",
    "smithy.api#requiresLength",
    "smithy.api#httpQueryParams",
    "smithy.api#notProperty",
)

_TRAIT_BIT_IDS: tuple[ShapeID, ...] = tuple(ShapeID(t) for t in _TRAIT_BITS)

_traits_cache: dict[int, dict[ShapeID, "Trait | DynamicTrait"]] = {}


def _expand_traits(
    indicator: StaticSchemaTraits,
) -> dict[ShapeID, "Trait | DynamicTrait"]:
    if isinstance(indicator, int):
        cached = _traits_cache.get(indicator)
        if cached is not None:
            return cached
        traits: dict[ShapeID, Trait | DynamicTrait] = {}
        bit = indicator
        i = 0
        while bit:
            if bit & 1:
                tid = _TRAIT_BIT_IDS[i]
                traits[tid] = Trait.new(tid)
            bit >>= 1
            i += 1
        _traits_cache[indicator] = traits
        return traits

    out: dict[ShapeID, Trait | DynamicTrait] = {}
    for raw_id, value in indicator.items():
        tid = ShapeID(raw_id)
        out[tid] = Trait.new(tid, value)
    return out


def _resolve(ref: "StaticSchemaRef") -> Schema:
    """Resolve a member target or operation ref to a concrete Schema."""
    if isinstance(ref, Schema):
        return ref
    if isinstance(ref, int):
        return _PRELUDE[ref]
    if isinstance(ref, tuple):
        return hydrate(cast(StaticSchema, ref))
    # a lambda: SIBLING forward/recursive reference
    return _resolve(ref())


# id(tuple) -> (tuple, hydrated Schema). The value keeps a reference to the keyed
# tuple so its id() can never be recycled onto a different tuple while cached -- which
# would otherwise let a transient hand-built tuple collide with a stale entry.
_cache: dict[int, tuple["StaticSchema", Schema]] = {}

# ShapeType ints whose tuples carry a trailing (member_names, member_targets) pair.
# An operation's trailing slots are schema refs, not members, so it is excluded.
_MEMBER_SHAPE_TYPES: frozenset[int] = frozenset(
    {
        ShapeType.ENUM.value,
        ShapeType.INT_ENUM.value,
        ShapeType.LIST.value,
        ShapeType.MAP.value,
        ShapeType.STRUCTURE.value,
        ShapeType.UNION.value,
    }
)


def hydrate(data: "StaticSchema | Schema") -> Schema:
    """Return the cached Schema for a compact schema tuple, building it on first use.

    A prelude shape's schema symbol is already a built :py:class:`Schema` (not a
    tuple), so it passes through unchanged.
    """
    if isinstance(data, Schema):
        return data

    key = id(data)
    cached = _cache.get(key)
    if cached is not None:
        return cached[1]

    type_int = cast(int, data[0])
    namespace = cast(str, data[1])
    shape_name = cast(str, data[2])
    traits = cast(StaticSchemaTraits, data[3])
    shape_type = ShapeType(type_int)
    id_ = ShapeID.from_parts(namespace=namespace, name=shape_name)

    # Publish the empty container to the cache BEFORE resolving members, so a
    # recursive member target that resolves back to this tuple sees the in-progress
    # object instead of recursing forever.
    schema = Schema(id=id_, shape_type=shape_type, traits=_expand_traits(traits))
    _cache[key] = (data, schema)

    if type_int in _MEMBER_SHAPE_TYPES and len(data) > 4:
        member_names = cast(tuple[str, ...], data[4])
        member_targets = cast(
            tuple[tuple[StaticSchemaRef, StaticSchemaTraits], ...], data[5]
        )
        # Mutate the published members dict in place so a recursive target that
        # captured it by reference during the cycle break observes the full map.
        members = schema.members
        for index, mname in enumerate(member_names):
            target_ref, member_traits = member_targets[index]
            target = _resolve(target_ref)
            resolved = target.traits.copy()
            resolved.update(_expand_traits(member_traits))
            members[mname] = Schema(
                id=id_.with_member(mname),
                shape_type=target.shape_type,
                traits=resolved,
                members=target.members,
                member_target=target,
                member_index=index,
            )

    return schema


# An operation tuple embeds its referenced schemas after its own schema definition:
# (type, ns, name, traits, input_ref, output_ref, error_refs). The op's own schema is
# built from slots 0-3 (operations have no members, so hydrate ignores the rest); the
# input, output, and error refs follow. Each ref is a shape tuple, a built Schema, a
# prelude int, or a lambda returning one.
_OP_INPUT = 4
_OP_OUTPUT = 5
_OP_ERRORS = 6


def operation_input_schema(op: "StaticOperationSchema") -> Schema:
    """Hydrate the input schema referenced by an operation tuple."""
    return _resolve(op[_OP_INPUT])


def operation_output_schema(op: "StaticOperationSchema") -> Schema:
    """Hydrate the output schema referenced by an operation tuple."""
    return _resolve(op[_OP_OUTPUT])


def operation_error_schemas(op: "StaticOperationSchema") -> list[Schema]:
    """Hydrate the error schemas referenced by an operation tuple."""
    return [_resolve(ref) for ref in op[_OP_ERRORS]]
