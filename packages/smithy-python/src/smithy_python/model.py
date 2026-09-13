# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Ordered, immutable objects for Smithy's JSON AST representation.

Shapes, members, and models are frozen dataclasses. Trait, metadata, and
attribute values are deeply immutable: JSON objects are exposed as read-only
mappings and JSON arrays as tuples, so values inherited through mixins can be
shared between shapes without one shape's consumer affecting another.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field, replace
from enum import StrEnum
from functools import total_ordering
from types import MappingProxyType
from typing import Final, Self, cast

from .exceptions import ModelError

type JSONValue = (
    None | bool | int | float | str | tuple[JSONValue, ...] | Mapping[str, JSONValue]
)

PRELUDE_NAMESPACE = "smithy.api"
MIXIN_TRAIT = "smithy.api#mixin"
TRAIT_DEFINITION = "smithy.api#trait"


class ShapeType(StrEnum):
    """Shape types supported by the Smithy JSON AST."""

    BLOB = "blob"
    BOOLEAN = "boolean"
    STRING = "string"
    TIMESTAMP = "timestamp"
    BYTE = "byte"
    SHORT = "short"
    INTEGER = "integer"
    LONG = "long"
    FLOAT = "float"
    DOUBLE = "double"
    BIG_INTEGER = "bigInteger"
    BIG_DECIMAL = "bigDecimal"
    DOCUMENT = "document"
    ENUM = "enum"
    INT_ENUM = "intEnum"
    LIST = "list"
    MAP = "map"
    STRUCTURE = "structure"
    UNION = "union"
    SERVICE = "service"
    RESOURCE = "resource"
    OPERATION = "operation"

    @property
    def is_service_category(self) -> bool:
        """Whether the type describes an API rather than data."""
        return self in {ShapeType.SERVICE, ShapeType.RESOURCE, ShapeType.OPERATION}


_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_NAMESPACE = re.compile(rf"{_IDENTIFIER.pattern}(?:\.{_IDENTIFIER.pattern})*")


@total_ordering
@dataclass(frozen=True, slots=True)
class ShapeID:
    """An absolute Smithy shape ID, optionally identifying a member."""

    namespace: str
    name: str
    member: str | None = None

    def __post_init__(self) -> None:
        if not (
            _NAMESPACE.fullmatch(self.namespace)
            and _IDENTIFIER.fullmatch(self.name)
            and (self.member is None or _IDENTIFIER.fullmatch(self.member))
        ):
            raise ModelError(f"Invalid shape ID: {self}")

    @classmethod
    def parse(cls, value: str) -> Self:
        """Parse an absolute Smithy shape ID."""
        if "#" not in value:
            raise ModelError(f"Expected an absolute shape ID, found: {value!r}")
        namespace, shape_name = value.split("#", 1)
        name, separator, member = shape_name.partition("$")
        return cls(namespace=namespace, name=name, member=member if separator else None)

    def with_member(self, member: str) -> Self:
        return type(self)(namespace=self.namespace, name=self.name, member=member)

    def without_member(self) -> Self:
        if self.member is None:
            return self
        return type(self)(namespace=self.namespace, name=self.name)

    @property
    def is_prelude(self) -> bool:
        return self.namespace == PRELUDE_NAMESPACE

    def __lt__(self, other: ShapeID) -> bool:
        """Order by namespace, then shape name, then member name."""
        return (self.namespace, self.name, self.member or "") < (
            other.namespace,
            other.name,
            other.member or "",
        )

    def __str__(self) -> str:
        value = f"{self.namespace}#{self.name}"
        return f"{value}${self.member}" if self.member is not None else value


# Frozen values are shared rather than copied, so every empty mapping in the
# model can be the same object.
_EMPTY_MAPPING: Final[Mapping[str, JSONValue]] = MappingProxyType({})


def _freeze(value: dict[str, JSONValue]) -> Mapping[str, JSONValue]:
    """Expose a dict this module owns as a read-only mapping."""
    return MappingProxyType(value) if value else _EMPTY_MAPPING


def _mapping(
    value: Mapping[str, JSONValue] | None = None,
) -> Mapping[str, JSONValue]:
    # A fresh dict preserves JSON insertion order while MappingProxyType prevents
    # mutation. Nested values are already frozen by _json_value.
    return _freeze(dict(value)) if value else _EMPTY_MAPPING


def _merged(
    base: Mapping[str, JSONValue], overrides: Mapping[str, JSONValue]
) -> Mapping[str, JSONValue]:
    """Freeze the union of two frozen mappings, ``overrides`` taking precedence."""
    return _freeze({**base, **overrides})


class _Traited:
    """Trait lookups shared by the AST nodes that carry traits."""

    __slots__ = ()

    traits: Mapping[str, JSONValue]

    def has_trait(self, trait: str) -> bool:
        return trait in self.traits

    def trait(self, trait: str, default: JSONValue = None) -> JSONValue:
        return self.traits.get(trait, default)


@dataclass(frozen=True, slots=True)
class Member(_Traited):
    """A member of an aggregate shape, in modeled order."""

    name: str
    target: ShapeID
    traits: Mapping[str, JSONValue] = field(default_factory=_mapping)


@dataclass(frozen=True, slots=True)
class Shape(_Traited):
    """A Smithy shape with ordered members and lossless shape-specific fields."""

    id: ShapeID
    type: ShapeType
    traits: Mapping[str, JSONValue] = field(default_factory=_mapping)
    mixins: tuple[ShapeID, ...] = ()
    members: tuple[Member, ...] = ()
    attributes: Mapping[str, JSONValue] = field(default_factory=_mapping)

    def get_member(self, name: str) -> Member | None:
        """Return a member by name, or ``None`` when the shape lacks it."""
        for member in self.members:
            if member.name == name:
                return member
        return None

    def member(self, name: str) -> Member:
        """Return a member by name or raise :class:`ModelError` if it is absent."""
        if (member := self.get_member(name)) is None:
            raise ModelError(f"Member not found: {self.id}${name}")
        return member

    def references(self) -> tuple[ShapeID, ...]:
        """Return all structural references in stable modeled order."""
        result = [*self.mixins, *(member.target for member in self.members)]
        # Only shapes in the service category carry reference attributes, so most
        # shapes skip the table entirely.
        if self.attributes:
            for key, extract in _REFERENCE_ATTRIBUTES.items():
                if (value := self.attributes.get(key)) is not None:
                    result.extend(extract(value, f"{self.id}.{key}"))
        return tuple(dict.fromkeys(result))


# Prelude shapes are omitted from the JSON AST unless the build opts in, so they
# are layered underneath every model's shapes to resolve on lookup.
_PRELUDE_TYPES: dict[str, tuple[ShapeType, Mapping[str, JSONValue]]] = {
    "Blob": (ShapeType.BLOB, {}),
    "Boolean": (ShapeType.BOOLEAN, {}),
    "String": (ShapeType.STRING, {}),
    "Timestamp": (ShapeType.TIMESTAMP, {}),
    "Byte": (ShapeType.BYTE, {}),
    "Short": (ShapeType.SHORT, {}),
    "Integer": (ShapeType.INTEGER, {}),
    "Long": (ShapeType.LONG, {}),
    "Float": (ShapeType.FLOAT, {}),
    "Double": (ShapeType.DOUBLE, {}),
    "BigInteger": (ShapeType.BIG_INTEGER, {}),
    "BigDecimal": (ShapeType.BIG_DECIMAL, {}),
    "Document": (ShapeType.DOCUMENT, {}),
    "PrimitiveBoolean": (ShapeType.BOOLEAN, {"smithy.api#default": False}),
    "PrimitiveByte": (ShapeType.BYTE, {"smithy.api#default": 0}),
    "PrimitiveShort": (ShapeType.SHORT, {"smithy.api#default": 0}),
    "PrimitiveInteger": (ShapeType.INTEGER, {"smithy.api#default": 0}),
    "PrimitiveLong": (ShapeType.LONG, {"smithy.api#default": 0}),
    "PrimitiveFloat": (ShapeType.FLOAT, {"smithy.api#default": 0}),
    "PrimitiveDouble": (ShapeType.DOUBLE, {"smithy.api#default": 0}),
    "Unit": (ShapeType.STRUCTURE, {"smithy.api#unitType": _EMPTY_MAPPING}),
}


def _prelude_shapes() -> Mapping[ShapeID, Shape]:
    shapes: dict[ShapeID, Shape] = {}
    for name, (shape_type, traits) in _PRELUDE_TYPES.items():
        shape_id = ShapeID(namespace=PRELUDE_NAMESPACE, name=name)
        shapes[shape_id] = Shape(id=shape_id, type=shape_type, traits=_mapping(traits))
    return MappingProxyType(shapes)


# Built once so that every reference to a prelude shape resolves to one object.
_PRELUDE_SHAPES: Final = _prelude_shapes()


@dataclass(frozen=True, slots=True)
class Model:
    """An ordered Smithy model parsed from a JSON AST document."""

    smithy: str
    metadata: Mapping[str, JSONValue]
    shapes: tuple[Shape, ...]
    _index: Mapping[ShapeID, Shape] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        index: dict[ShapeID, Shape] = {}
        for shape in self.shapes:
            if shape.id in index:
                raise ModelError(f"Duplicate shape: {shape.id}")
            index[shape.id] = shape
        # Layering the prelude underneath keeps lookups total over it without
        # adding shapes the model did not declare to `shapes`.
        object.__setattr__(
            self, "_index", MappingProxyType({**_PRELUDE_SHAPES, **index})
        )

    @classmethod
    def from_json(cls, source: str | bytes | bytearray) -> Self:
        """Parse a Smithy JSON AST document."""
        try:
            document = cast(object, json.loads(source))
        except (TypeError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ModelError(f"Invalid Smithy JSON AST: {error}") from error
        return cls.from_dict(_object_mapping(document, "Smithy JSON AST"))

    @classmethod
    def from_dict(cls, document: Mapping[str, object]) -> Self:
        """Build a model from a decoded Smithy JSON AST document."""
        version = document.get("smithy")
        if not isinstance(version, str):
            raise ModelError("The Smithy JSON AST is missing a string 'smithy' version")
        shapes_node = _object_mapping(document.get("shapes", {}), "Smithy model shapes")
        metadata = _json_object(document.get("metadata", {}), "Smithy model metadata")

        shapes: list[Shape] = []
        applies: dict[ShapeID, list[_Apply]] = {}
        for shape_id, unparsed_node in shapes_node.items():
            node = _object_mapping(unparsed_node, f"shape {shape_id}")
            parsed_id = ShapeID.parse(shape_id)
            if node.get("type") == "apply":
                applies.setdefault(parsed_id.without_member(), []).append(
                    _parse_apply(parsed_id, node)
                )
                continue
            shapes.append(_parse_shape(parsed_id, node))

        # Serialized models omit everything a shape inherits from its mixins, and
        # traits added to inherited members arrive as apply statements. Both are
        # resolved together so that shapes using a mixin see its applied traits.
        shapes = _resolve_shapes(shapes, applies)
        return cls(smithy=version, metadata=metadata, shapes=tuple(shapes))

    def __iter__(self) -> Iterator[Shape]:
        return iter(self.shapes)

    def __len__(self) -> int:
        return len(self.shapes)

    def get(self, shape_id: ShapeID | str) -> Shape | None:
        """Return a shape by ID, resolving prelude shapes even when omitted.

        A member ID resolves to the shape containing it, or ``None`` when that
        shape does not define the member.
        """
        shape_id = ShapeID.parse(shape_id) if isinstance(shape_id, str) else shape_id
        shape = self._index.get(shape_id.without_member())
        if shape is None or shape_id.member is None:
            return shape
        return shape if shape.get_member(shape_id.member) is not None else None

    def expect(self, shape_id: ShapeID | str) -> Shape:
        """Return a shape by ID or raise :class:`ModelError` if it is absent."""
        if (shape := self.get(shape_id)) is None:
            raise ModelError(f"Shape not found: {shape_id}")
        return shape

    def services(self) -> tuple[Shape, ...]:
        """Return every service shape in modeled order."""
        return tuple(shape for shape in self if shape.type is ShapeType.SERVICE)

    def replace_shapes(self, shapes: Iterable[Shape]) -> Self:
        """Return a copy of the model with a different set of shapes."""
        return replace(self, shapes=tuple(shapes))


def _parse_shape(shape_id: ShapeID, node: Mapping[str, object]) -> Shape:
    type_value = node.get("type")
    try:
        shape_type = ShapeType(type_value)
    except (TypeError, ValueError) as error:
        raise ModelError(
            f"Unsupported shape type {type_value!r} on {shape_id}"
        ) from error
    traits = _json_object(node.get("traits", {}), f"traits on {shape_id}")
    mixins = _reference_list(node.get("mixins", []), f"{shape_id}.mixins")

    members: list[Member] = []
    consumed = {"type", "traits", "mixins"}
    if shape_type is ShapeType.LIST or shape_type is ShapeType.MAP:
        names = ("member",) if shape_type is ShapeType.LIST else ("key", "value")
        consumed.update(names)
        for name in names:
            # A shape using mixins is serialized without the members it inherits.
            if name in node or not mixins:
                members.append(_parse_member(name, node.get(name), shape_id))
    elif shape_type in {
        ShapeType.STRUCTURE,
        ShapeType.UNION,
        ShapeType.ENUM,
        ShapeType.INT_ENUM,
    }:
        members_node = _object_mapping(
            node.get("members", {}), f"members of {shape_id}"
        )
        members.extend(
            _parse_member(name, member_node, shape_id)
            for name, member_node in members_node.items()
        )
        consumed.add("members")

    attributes = {
        key: _json_value(value, f"{shape_id}.{key}")
        for key, value in node.items()
        if key not in consumed
    }
    return Shape(
        id=shape_id,
        type=shape_type,
        traits=traits,
        mixins=mixins,
        members=tuple(members),
        attributes=_freeze(attributes),
    )


def _parse_member(name: str, unparsed_node: object, container: ShapeID) -> Member:
    location = f"{container}${name}"
    node = _object_mapping(unparsed_node, f"member {location}")
    return Member(
        name=name,
        target=_target(node.get("target"), location),
        traits=_json_object(node.get("traits", {}), f"traits on {location}"),
    )


def _expect_list(value: object, location: str) -> Sequence[object]:
    if not isinstance(value, list | tuple):
        raise ModelError(f"Expected a list at {location}")
    return cast(Sequence[object], value)


def _reference(value: object, location: str) -> ShapeID:
    reference = _object_mapping(value, location)
    target = reference.get("target")
    if not isinstance(target, str):
        raise ModelError(f"Expected a shape reference at {location}")
    return ShapeID.parse(target)


def _target(value: object, location: str) -> ShapeID:
    if not isinstance(value, str):
        raise ModelError(f"Expected a shape target at {location}")
    return ShapeID.parse(value)


def _reference_one(value: object, location: str) -> tuple[ShapeID, ...]:
    return (_reference(value, location),)


def _reference_list(value: object, location: str) -> tuple[ShapeID, ...]:
    return tuple(_reference(item, location) for item in _expect_list(value, location))


def _reference_map(value: object, location: str) -> tuple[ShapeID, ...]:
    return tuple(
        _reference(item, f"{location}.{name}")
        for name, item in _object_mapping(value, location).items()
    )


type _ReferenceExtractor = Callable[[object, str], tuple[ShapeID, ...]]

# The shape attributes that hold structural references, and how each spells
# them. Every other attribute holds plain data. Iteration order fixes the order
# references are reported in.
_REFERENCE_ATTRIBUTES: Final[Mapping[str, _ReferenceExtractor]] = MappingProxyType(
    {
        "operations": _reference_list,
        "resources": _reference_list,
        "errors": _reference_list,
        "collectionOperations": _reference_list,
        "input": _reference_one,
        "output": _reference_one,
        "create": _reference_one,
        "put": _reference_one,
        "read": _reference_one,
        "update": _reference_one,
        "delete": _reference_one,
        "list": _reference_one,
        "identifiers": _reference_map,
        "properties": _reference_map,
    }
)


def _object_items(value: object, location: str) -> Iterator[tuple[str, object]]:
    """Validate that a decoded JSON value is an object keyed by strings."""
    if not isinstance(value, Mapping):
        raise ModelError(f"Expected an object at {location}")
    for key, item in cast(Mapping[object, object], value).items():
        if not isinstance(key, str):
            raise ModelError(f"Expected string object keys at {location}")
        yield (key, item)


def _object_mapping(value: object, location: str) -> dict[str, object]:
    return dict(_object_items(value, location))


def _json_object(value: object, location: str) -> Mapping[str, JSONValue]:
    return _freeze(
        {
            key: _json_value(item, f"{location}.{key}")
            for key, item in _object_items(value, location)
        }
    )


def _json_value(value: object, location: str) -> JSONValue:
    """Convert a decoded JSON value into its deeply immutable form."""
    if value is None or isinstance(value, bool | int | float | str):
        return value
    if isinstance(value, list | tuple):
        return tuple(
            _json_value(item, location) for item in cast(Sequence[object], value)
        )
    if isinstance(value, Mapping):
        return _json_object(cast(object, value), location)
    raise ModelError(f"Unsupported JSON value at {location}: {type(value).__name__}")


type _Apply = tuple[str, Mapping[str, JSONValue]]


def _parse_apply(target: ShapeID, node: Mapping[str, object]) -> _Apply:
    """Parse an apply statement, which adds traits to a member of a shape.

    A shape's own traits are serialized with its definition, so an apply keyed by
    a shape ID would need the key that definition already occupies.
    """
    if target.member is None:
        raise ModelError(f"Expected an apply statement to target a member: {target}")
    return (target.member, _json_object(node.get("traits", {}), f"traits on {target}"))


def _resolve_shapes(
    shapes: list[Shape], applies: Mapping[ShapeID, list[_Apply]]
) -> list[Shape]:
    """Copy inherited definitions onto shapes using mixins and merge applies.

    Follows the resolution rules of the Smithy mixins specification: inherited
    members precede local members in a depth-first traversal of the mixins,
    later mixins take precedence over earlier ones, local definitions take
    precedence over anything inherited, and the ``mixin`` trait itself and any
    ``localTraits`` are not inherited. Apply statements targeting the members of
    a shape are merged as part of resolving that shape, so shapes that use it as
    a mixin inherit the applied traits.
    """
    by_id = {shape.id: shape for shape in shapes}
    for container in applies:
        if container not in by_id:
            raise ModelError(f"Apply target not found: {container}")
    resolved: dict[ShapeID, Shape] = {}
    resolving: set[ShapeID] = set()

    def resolve(shape: Shape) -> Shape:
        if (done := resolved.get(shape.id)) is not None:
            return done
        if shape.id in resolving:
            raise ModelError(f"Mixin cycle detected at {shape.id}")
        resolving.add(shape.id)

        if shape.mixins:
            shape = _merge_mixins(shape, by_id, resolve)
        if shape.id in applies:
            shape = _apply_traits(shape, applies[shape.id])

        resolving.discard(shape.id)
        resolved[shape.id] = shape
        return shape

    return [resolve(shape) for shape in shapes]


def _merge_mixins(
    shape: Shape, by_id: Mapping[ShapeID, Shape], resolve: Callable[[Shape], Shape]
) -> Shape:
    traits: dict[str, JSONValue] = {}
    members: dict[str, Member] = {}
    attributes: dict[str, JSONValue] = {}
    for mixin_id in shape.mixins:
        mixin = by_id.get(mixin_id)
        if mixin is None:
            raise ModelError(f"Mixin not found: {mixin_id} (used by {shape.id})")
        if not mixin.has_trait(MIXIN_TRAIT):
            raise ModelError(
                f"{shape.id} uses {mixin_id} as a mixin, but it lacks the "
                f"{MIXIN_TRAIT} trait"
            )
        if mixin.type is not shape.type:
            raise ModelError(
                f"{shape.id} is a {shape.type} but uses the {mixin.type} shape "
                f"{mixin_id} as a mixin"
            )
        mixin = resolve(mixin)
        traits.update(_inherited_traits(mixin))
        for member in mixin.members:
            members[member.name] = _merge_members(members.get(member.name), member)
        _merge_attributes(attributes, mixin.attributes)

    traits.update(shape.traits)
    for member in shape.members:
        members[member.name] = _merge_members(members.get(member.name), member)
    _merge_attributes(attributes, shape.attributes)

    return replace(
        shape,
        traits=_freeze(traits),
        members=tuple(members.values()),
        attributes=_freeze(attributes),
    )


def _apply_traits(shape: Shape, applies: list[_Apply]) -> Shape:
    """Merge apply statements onto the members of a shape."""
    members = {member.name: member for member in shape.members}
    for name, applied in applies:
        member = members.get(name)
        if member is None:
            raise ModelError(
                f"Apply target member not found: {shape.id.with_member(name)}"
            )
        members[name] = replace(member, traits=_merged(member.traits, applied))
    return replace(shape, members=tuple(members.values()))


def _inherited_traits(mixin: Shape) -> dict[str, JSONValue]:
    mixin_trait = mixin.trait(MIXIN_TRAIT)
    local_traits = (
        mixin_trait.get("localTraits", ()) if isinstance(mixin_trait, Mapping) else ()
    )
    excluded = {MIXIN_TRAIT}
    if isinstance(local_traits, tuple):
        excluded.update(name for name in local_traits if isinstance(name, str))
    return {name: value for name, value in mixin.traits.items() if name not in excluded}


def _merge_members(inherited: Member | None, member: Member) -> Member:
    """Merge a redefined member onto the one it inherits, keeping its position."""
    if inherited is None:
        return member
    if inherited.target != member.target:
        raise ModelError(
            f"Member {member.name} redefines an inherited member with a different "
            f"target: {inherited.target} != {member.target}"
        )
    return replace(member, traits=_merged(inherited.traits, member.traits))


def _merge_attributes(
    target: dict[str, JSONValue], source: Mapping[str, JSONValue]
) -> None:
    """Merge shape properties, giving ``source`` precedence.

    Arrays are concatenated without duplicates, objects are merged key by key,
    and scalars from ``source`` replace existing values.
    """
    for key, value in source.items():
        existing = target.get(key)
        if isinstance(existing, tuple) and isinstance(value, tuple):
            target[key] = (
                *existing,
                *(item for item in value if item not in existing),
            )
        elif isinstance(existing, Mapping) and isinstance(value, Mapping):
            target[key] = _merged(existing, value)
        else:
            target[key] = value
