# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Ordered, immutable objects for Smithy's JSON AST representation."""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Iterable, Iterator, Mapping
from dataclasses import dataclass, field, replace
from enum import StrEnum
from types import MappingProxyType
from typing import Self, cast

from .exceptions import ModelError

type JSONValue = (
    None | bool | int | float | str | list[JSONValue] | dict[str, JSONValue]
)

PRELUDE_NAMESPACE = "smithy.api"
MIXIN_TRAIT = "smithy.api#mixin"


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


@dataclass(frozen=True, slots=True, order=True)
class ShapeID:
    """An absolute Smithy shape ID, optionally identifying a member."""

    namespace: str
    name: str
    member: str | None = None

    def __post_init__(self) -> None:
        if not _NAMESPACE.fullmatch(self.namespace) or not _IDENTIFIER.fullmatch(
            self.name
        ):
            raise ModelError(f"Invalid shape ID: {self}")
        if self.member is not None and not _IDENTIFIER.fullmatch(self.member):
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
        return type(self)(namespace=self.namespace, name=self.name)

    @property
    def is_prelude(self) -> bool:
        return self.namespace == PRELUDE_NAMESPACE

    def __str__(self) -> str:
        value = f"{self.namespace}#{self.name}"
        return f"{value}${self.member}" if self.member is not None else value


def _mapping(
    value: Mapping[str, JSONValue] | None = None,
) -> Mapping[str, JSONValue]:
    # A fresh dict preserves JSON insertion order while MappingProxyType prevents
    # accidental mutation through a frozen dataclass.
    return MappingProxyType(dict(value or {}))


@dataclass(frozen=True, slots=True)
class Member:
    """A member of an aggregate shape, in modeled order."""

    name: str
    target: ShapeID
    traits: Mapping[str, JSONValue] = field(default_factory=_mapping)

    def has_trait(self, trait: str) -> bool:
        return trait in self.traits

    def trait(self, trait: str, default: JSONValue = None) -> JSONValue:
        return self.traits.get(trait, default)


@dataclass(frozen=True, slots=True)
class Shape:
    """A Smithy shape with ordered members and lossless shape-specific fields."""

    id: ShapeID
    type: ShapeType
    traits: Mapping[str, JSONValue] = field(default_factory=_mapping)
    mixins: tuple[ShapeID, ...] = ()
    members: tuple[Member, ...] = ()
    attributes: Mapping[str, JSONValue] = field(default_factory=_mapping)

    def has_trait(self, trait: str) -> bool:
        return trait in self.traits

    def trait(self, trait: str, default: JSONValue = None) -> JSONValue:
        return self.traits.get(trait, default)

    def member(self, name: str) -> Member:
        for member in self.members:
            if member.name == name:
                return member
        raise ModelError(f"Member not found: {self.id}${name}")

    def references(self) -> tuple[ShapeID, ...]:
        """Return all structural references in stable modeled order."""
        result = [*self.mixins, *(member.target for member in self.members)]
        for key in (
            "operations",
            "resources",
            "errors",
            "collectionOperations",
        ):
            result.extend(_reference_list(self.attributes.get(key), f"{self.id}.{key}"))
        for key in (
            "input",
            "output",
            "create",
            "put",
            "read",
            "update",
            "delete",
            "list",
        ):
            value = self.attributes.get(key)
            if value is not None:
                result.append(_reference(value, f"{self.id}.{key}"))
        for key in ("identifiers", "properties"):
            values = self.attributes.get(key)
            if isinstance(values, dict):
                result.extend(
                    _reference(value, f"{self.id}.{key}.{name}")
                    for name, value in values.items()
                )
        return tuple(dict.fromkeys(result))


# Prelude shapes are omitted from the JSON AST unless the build opts in, so they
# are resolved on demand when a member targets one.
_PRELUDE_TYPES: dict[str, tuple[ShapeType, dict[str, JSONValue]]] = {
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
    "Unit": (ShapeType.STRUCTURE, {"smithy.api#unitType": {}}),
}


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
        object.__setattr__(self, "_index", MappingProxyType(index))

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
                traits = _expect_traits(node.get("traits", {}), parsed_id)
                applies.setdefault(parsed_id.without_member(), []).append(
                    (parsed_id, traits)
                )
                continue
            shapes.append(_parse_shape(parsed_id, node))

        # Serialized models omit everything a shape inherits from its mixins, and
        # traits added to inherited members arrive as apply statements. Both are
        # resolved together so that shapes using a mixin see its applied traits.
        shapes = _resolve_shapes(shapes, applies)
        return cls(smithy=version, metadata=_mapping(metadata), shapes=tuple(shapes))

    def __iter__(self) -> Iterator[Shape]:
        return iter(self.shapes)

    def __len__(self) -> int:
        return len(self.shapes)

    def get(self, shape_id: ShapeID | str) -> Shape | None:
        """Return a shape by ID, resolving prelude shapes even when omitted."""
        shape_id = ShapeID.parse(shape_id) if isinstance(shape_id, str) else shape_id
        if shape_id.member is not None:
            return self._index.get(shape_id.without_member())
        if (shape := self._index.get(shape_id)) is not None:
            return shape
        if shape_id.is_prelude and shape_id.name in _PRELUDE_TYPES:
            shape_type, traits = _PRELUDE_TYPES[shape_id.name]
            return Shape(id=shape_id, type=shape_type, traits=_mapping(traits))
        return None

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
        return type(self)(
            smithy=self.smithy, metadata=self.metadata, shapes=tuple(shapes)
        )


def _parse_shape(shape_id: ShapeID, node: Mapping[str, object]) -> Shape:
    type_value = node.get("type")
    try:
        shape_type = ShapeType(type_value)
    except (TypeError, ValueError) as error:
        raise ModelError(
            f"Unsupported shape type {type_value!r} on {shape_id}"
        ) from error
    traits = _expect_traits(node.get("traits", {}), shape_id)
    mixins = tuple(
        _reference(value, f"{shape_id}.mixins")
        for value in _expect_list(node.get("mixins", []), f"{shape_id}.mixins")
    )

    members: list[Member] = []
    consumed = {"type", "traits", "mixins"}
    if shape_type is ShapeType.LIST:
        members.append(_parse_member("member", node.get("member"), shape_id))
        consumed.add("member")
    elif shape_type is ShapeType.MAP:
        members.extend(
            (
                _parse_member("key", node.get("key"), shape_id),
                _parse_member("value", node.get("value"), shape_id),
            )
        )
        consumed.update(("key", "value"))
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
        attributes=_mapping(attributes),
    )


def _parse_member(name: str, unparsed_node: object, container: ShapeID) -> Member:
    node = _object_mapping(unparsed_node, f"member {container}${name}")
    return Member(
        name=name,
        target=_target(node.get("target"), f"{container}${name}"),
        traits=_expect_traits(node.get("traits", {}), container.with_member(name)),
    )


def _expect_traits(value: object, target: ShapeID) -> Mapping[str, JSONValue]:
    return _mapping(_json_object(value, f"traits on {target}"))


def _expect_list(value: object, location: str) -> list[object]:
    if not isinstance(value, list):
        raise ModelError(f"Expected a list at {location}")
    return cast(list[object], value)


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


def _reference_list(value: object, location: str) -> tuple[ShapeID, ...]:
    if value is None:
        return ()
    return tuple(_reference(item, location) for item in _expect_list(value, location))


def _object_mapping(value: object, location: str) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise ModelError(f"Expected an object at {location}")
    result: dict[str, object] = {}
    for key, item in cast(Mapping[object, object], value).items():
        if not isinstance(key, str):
            raise ModelError(f"Expected string object keys at {location}")
        result[key] = item
    return result


def _json_object(value: object, location: str) -> dict[str, JSONValue]:
    return {
        key: _json_value(item, f"{location}.{key}")
        for key, item in _object_mapping(value, location).items()
    }


def _json_value(value: object, location: str) -> JSONValue:
    if value is None or isinstance(value, bool | int | float | str):
        return value
    if isinstance(value, list):
        return [_json_value(item, location) for item in cast(list[object], value)]
    if isinstance(value, Mapping):
        return _json_object(cast(object, value), location)
    raise ModelError(f"Unsupported JSON value at {location}: {type(value).__name__}")


type _Apply = tuple[ShapeID, Mapping[str, JSONValue]]


def _resolve_shapes(
    shapes: list[Shape], applies: Mapping[ShapeID, list[_Apply]]
) -> list[Shape]:
    """Copy inherited definitions onto shapes using mixins and merge applies.

    Follows the resolution rules of the Smithy mixins specification: inherited
    members precede local members in a depth-first traversal of the mixins,
    later mixins take precedence over earlier ones, local definitions take
    precedence over anything inherited, and the ``mixin`` trait itself and any
    ``localTraits`` are not inherited. Apply statements targeting a shape are
    merged as part of resolving that shape, so shapes that use it as a mixin
    inherit the applied traits.
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
        traits=_mapping(traits),
        members=tuple(members.values()),
        attributes=_mapping(attributes),
    )


def _apply_traits(shape: Shape, applies: list[_Apply]) -> Shape:
    """Merge apply statements targeting a shape or its members."""
    members = {member.name: member for member in shape.members}
    traits = dict(shape.traits)
    for target, applied in applies:
        if target.member is None:
            traits.update(applied)
            continue
        member = members.get(target.member)
        if member is None:
            raise ModelError(f"Apply target member not found: {target}")
        members[target.member] = replace(
            member, traits=_mapping({**member.traits, **applied})
        )
    return replace(shape, traits=_mapping(traits), members=tuple(members.values()))


def _inherited_traits(mixin: Shape) -> dict[str, JSONValue]:
    excluded = {MIXIN_TRAIT}
    mixin_trait = mixin.trait(MIXIN_TRAIT)
    if isinstance(mixin_trait, dict):
        local_traits = mixin_trait.get("localTraits", [])
        if isinstance(local_traits, list):
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
    return replace(member, traits=_mapping({**inherited.traits, **member.traits}))


def _merge_attributes(
    target: dict[str, JSONValue], source: Mapping[str, JSONValue]
) -> None:
    """Merge shape properties, giving ``source`` precedence.

    Lists are concatenated without duplicates, objects are merged key by key,
    and scalars from ``source`` replace existing values.
    """
    for key, value in source.items():
        existing = target.get(key)
        if isinstance(existing, list) and isinstance(value, list):
            target[key] = [
                *existing,
                *(item for item in value if item not in existing),
            ]
        elif isinstance(existing, dict) and isinstance(value, dict):
            target[key] = {**existing, **value}
        else:
            target[key] = value
