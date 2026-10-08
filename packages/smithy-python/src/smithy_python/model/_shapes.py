# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Shape types and the flattened, immutable shape classes."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType
from typing import Final

from ._shape_id import PRELUDE_NAMESPACE, ShapeId, as_shape_id

type Node = None | bool | int | float | str | tuple[Node, ...] | Mapping[str, Node]
"""A deeply immutable JSON value: arrays are tuples, objects read-only mappings."""

type JsonValue = (
    None | bool | int | float | str | list[JsonValue] | dict[str, JsonValue]
)
"""A mutable JSON value, as produced by :func:`to_json`."""


def to_json(node: Node) -> JsonValue:
    """Return a mutable copy of a node, e.g. for ``json.dumps`` or editing."""
    if isinstance(node, Mapping):
        return {k: to_json(v) for k, v in node.items()}
    if isinstance(node, tuple):
        return [to_json(v) for v in node]
    return node


class ShapeType(StrEnum):
    """Every shape type in the Smithy 2.0 semantic model, including members."""

    BLOB = "blob"
    BOOLEAN = "boolean"
    STRING = "string"
    BYTE = "byte"
    SHORT = "short"
    INTEGER = "integer"
    LONG = "long"
    FLOAT = "float"
    DOUBLE = "double"
    BIG_INTEGER = "bigInteger"
    BIG_DECIMAL = "bigDecimal"
    TIMESTAMP = "timestamp"
    DOCUMENT = "document"
    ENUM = "enum"
    INT_ENUM = "intEnum"
    LIST = "list"
    MAP = "map"
    STRUCTURE = "structure"
    UNION = "union"
    MEMBER = "member"
    SERVICE = "service"
    RESOURCE = "resource"
    OPERATION = "operation"


SIMPLE_TYPES: Final = frozenset(
    {
        ShapeType.BLOB,
        ShapeType.BOOLEAN,
        ShapeType.STRING,
        ShapeType.BYTE,
        ShapeType.SHORT,
        ShapeType.INTEGER,
        ShapeType.LONG,
        ShapeType.FLOAT,
        ShapeType.DOUBLE,
        ShapeType.BIG_INTEGER,
        ShapeType.BIG_DECIMAL,
        ShapeType.TIMESTAMP,
        ShapeType.DOCUMENT,
    }
)

MIXIN_TRAIT: Final = ShapeId(PRELUDE_NAMESPACE, "mixin")
UNIT: Final = ShapeId(PRELUDE_NAMESPACE, "Unit")

_EMPTY_TRAITS: Final[Mapping[ShapeId, Node]] = MappingProxyType({})
_EMPTY_MEMBERS: Final[Mapping[str, MemberShape]] = MappingProxyType({})


@dataclass(frozen=True, slots=True, kw_only=True, eq=False)
class Shape:
    """Base class of every shape.

    Shapes are already mixin-flattened: ``members`` and ``traits`` include
    everything inherited from mixins, in a deterministic order. Instances are
    immutable; trait values are deeply frozen :data:`Node` values (use
    :func:`to_json` for a mutable copy). Equality is identity.
    """

    id: ShapeId
    type: ShapeType
    traits: Mapping[ShapeId, Node] = _EMPTY_TRAITS
    """Trait ID to JSON node value, in merge order (see the loader docs)."""
    mixins: tuple[ShapeId, ...] = ()
    """The mixins this shape declared, in declaration order.

    Informational only: members, traits, and properties already include
    everything inherited from these mixins.
    """
    members: Mapping[str, MemberShape] = _EMPTY_MEMBERS
    """Members by name, in order: inherited mixin members, then local ones."""

    def has_trait(self, trait: ShapeId | str) -> bool:
        """Whether the shape has a trait; relative names resolve to smithy.api."""
        return _trait_id(trait) in self.traits

    def get_trait(self, trait: ShapeId | str) -> Node:
        """Return a trait value or None if absent (use has_trait for presence)."""
        return self.traits.get(_trait_id(trait))

    @property
    def is_mixin(self) -> bool:
        """Whether the shape is marked with ``@mixin``."""
        return MIXIN_TRAIT in self.traits


def _trait_id(trait: ShapeId | str) -> ShapeId:
    return as_shape_id(trait, default_namespace=PRELUDE_NAMESPACE)


@dataclass(frozen=True, slots=True, kw_only=True, eq=False)
class SimpleShape(Shape):
    """A blob, boolean, string, numeric, timestamp, or document shape."""


@dataclass(frozen=True, slots=True, kw_only=True, eq=False)
class MemberShape(Shape):
    """A member of an aggregate shape; its ID is rooted at its container."""

    type: ShapeType = ShapeType.MEMBER
    target: ShapeId

    @property
    def container(self) -> ShapeId:
        """ID of the shape that contains this member."""
        return self.id.root

    @property
    def name(self) -> str:
        """The member name."""
        assert self.id.member is not None  # noqa: S101 - invariant
        return self.id.member


@dataclass(frozen=True, slots=True, kw_only=True, eq=False)
class ListShape(Shape):
    """A list shape; ``members`` contains exactly ``member``."""

    @property
    def member(self) -> MemberShape:
        return self.members["member"]


@dataclass(frozen=True, slots=True, kw_only=True, eq=False)
class MapShape(Shape):
    """A map shape; ``members`` contains ``key`` then ``value``."""

    @property
    def key(self) -> MemberShape:
        return self.members["key"]

    @property
    def value(self) -> MemberShape:
        return self.members["value"]


@dataclass(frozen=True, slots=True, kw_only=True, eq=False)
class StructureShape(Shape):
    """A structure shape."""


@dataclass(frozen=True, slots=True, kw_only=True, eq=False)
class UnionShape(Shape):
    """A union shape."""


@dataclass(frozen=True, slots=True, kw_only=True, eq=False)
class EnumShape(Shape):
    """A string enum; member values live in ``smithy.api#enumValue``."""


@dataclass(frozen=True, slots=True, kw_only=True, eq=False)
class IntEnumShape(Shape):
    """An integer enum; member values live in ``smithy.api#enumValue``."""


@dataclass(frozen=True, slots=True, kw_only=True, eq=False)
class ServiceShape(Shape):
    """A service shape."""

    version: str | None = None
    operations: tuple[ShapeId, ...] = ()
    resources: tuple[ShapeId, ...] = ()
    errors: tuple[ShapeId, ...] = ()
    rename: Mapping[ShapeId, str] = field(default_factory=lambda: MappingProxyType({}))


@dataclass(frozen=True, slots=True, kw_only=True, eq=False)
class ResourceShape(Shape):
    """A resource shape."""

    identifiers: Mapping[str, ShapeId] = field(
        default_factory=lambda: MappingProxyType({})
    )
    properties: Mapping[str, ShapeId] = field(
        default_factory=lambda: MappingProxyType({})
    )
    create: ShapeId | None = None
    put: ShapeId | None = None
    read: ShapeId | None = None
    update: ShapeId | None = None
    delete: ShapeId | None = None
    list: ShapeId | None = None
    operations: tuple[ShapeId, ...] = ()
    collection_operations: tuple[ShapeId, ...] = ()
    resources: tuple[ShapeId, ...] = ()


@dataclass(frozen=True, slots=True, kw_only=True, eq=False)
class OperationShape(Shape):
    """An operation shape.

    An absent ``input`` or ``output`` is ``smithy.api#Unit``, matching Smithy's
    semantic model; explicit and implicit Unit are indistinguishable.
    """

    input: ShapeId = UNIT
    output: ShapeId = UNIT
    errors: tuple[ShapeId, ...] = ()


SHAPE_CLASSES: Final[Mapping[ShapeType, type[Shape]]] = MappingProxyType(
    {
        **dict.fromkeys(SIMPLE_TYPES, SimpleShape),
        ShapeType.LIST: ListShape,
        ShapeType.MAP: MapShape,
        ShapeType.STRUCTURE: StructureShape,
        ShapeType.UNION: UnionShape,
        ShapeType.ENUM: EnumShape,
        ShapeType.INT_ENUM: IntEnumShape,
        ShapeType.SERVICE: ServiceShape,
        ShapeType.RESOURCE: ResourceShape,
        ShapeType.OPERATION: OperationShape,
    }
)
