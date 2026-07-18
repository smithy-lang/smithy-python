# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Ordered, immutable objects for Smithy's JSON AST representation."""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass, field, replace
from enum import StrEnum
from types import MappingProxyType
from typing import Self, cast

from .exceptions import ModelError

type JSONValue = (
    None | bool | int | float | str | list[JSONValue] | dict[str, JSONValue]
)


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


@dataclass(frozen=True, slots=True, order=True)
class ShapeID:
    """An absolute Smithy shape ID, optionally identifying a member."""

    namespace: str
    name: str
    member: str | None = None

    def __post_init__(self) -> None:
        if not self.namespace or not self.name or "#" in self.namespace:
            raise ModelError(f"Invalid shape ID: {self}")
        if "$" in self.name or self.member == "":
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


_PRELUDE_TYPES: dict[str, ShapeType] = {
    "Blob": ShapeType.BLOB,
    "Boolean": ShapeType.BOOLEAN,
    "String": ShapeType.STRING,
    "Timestamp": ShapeType.TIMESTAMP,
    "Byte": ShapeType.BYTE,
    "Short": ShapeType.SHORT,
    "Integer": ShapeType.INTEGER,
    "Long": ShapeType.LONG,
    "Float": ShapeType.FLOAT,
    "Double": ShapeType.DOUBLE,
    "BigInteger": ShapeType.BIG_INTEGER,
    "BigDecimal": ShapeType.BIG_DECIMAL,
    "Document": ShapeType.DOCUMENT,
    "PrimitiveBoolean": ShapeType.BOOLEAN,
    "PrimitiveByte": ShapeType.BYTE,
    "PrimitiveShort": ShapeType.SHORT,
    "PrimitiveInteger": ShapeType.INTEGER,
    "PrimitiveLong": ShapeType.LONG,
    "PrimitiveFloat": ShapeType.FLOAT,
    "PrimitiveDouble": ShapeType.DOUBLE,
    "Unit": ShapeType.STRUCTURE,
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
        try:
            document = cast(object, json.loads(source))
        except (TypeError, json.JSONDecodeError) as error:
            raise ModelError(f"Invalid Smithy JSON AST: {error}") from error
        return cls.from_dict(_object_mapping(document, "Smithy JSON AST"))

    @classmethod
    def from_dict(cls, document: Mapping[str, object]) -> Self:
        version = document.get("smithy")
        if not isinstance(version, str):
            raise ModelError("The Smithy JSON AST is missing a string 'smithy' version")
        shapes_node = _object_mapping(document.get("shapes"), "Smithy model shapes")
        metadata = _json_object(document.get("metadata", {}), "Smithy model metadata")

        shapes: list[Shape] = []
        applies: list[tuple[ShapeID, Mapping[str, JSONValue]]] = []
        for shape_id, unparsed_node in shapes_node.items():
            node = _object_mapping(unparsed_node, f"shape {shape_id}")
            parsed_id = ShapeID.parse(shape_id)
            if node.get("type") == "apply":
                applies.append(
                    (parsed_id, _expect_traits(node.get("traits", {}), parsed_id))
                )
                continue
            shapes.append(_parse_shape(parsed_id, node))

        if applies:
            shapes = _apply_traits(shapes, applies)
        return cls(smithy=version, metadata=_mapping(metadata), shapes=tuple(shapes))

    def __iter__(self) -> Iterator[Shape]:
        return iter(self.shapes)

    def get(self, shape_id: ShapeID | str) -> Shape | None:
        shape_id = ShapeID.parse(shape_id) if isinstance(shape_id, str) else shape_id
        if shape_id.member is not None:
            return self._index.get(shape_id.without_member())
        if (shape := self._index.get(shape_id)) is not None:
            return shape
        if shape_id.namespace == "smithy.api" and shape_id.name in _PRELUDE_TYPES:
            return Shape(id=shape_id, type=_PRELUDE_TYPES[shape_id.name])
        return None

    def expect(self, shape_id: ShapeID | str) -> Shape:
        if (shape := self.get(shape_id)) is None:
            raise ModelError(f"Shape not found: {shape_id}")
        return shape

    def replace_shapes(self, shapes: Iterable[Shape]) -> Self:
        return type(self)(
            smithy=self.smithy, metadata=self.metadata, shapes=tuple(shapes)
        )

    def service(self, service_id: ShapeID | str) -> Shape:
        shape = self.expect(service_id)
        if shape.type is not ShapeType.SERVICE:
            raise ModelError(
                f"Expected a service shape, found {shape.type}: {shape.id}"
            )
        return shape


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


def _apply_traits(
    shapes: list[Shape], applies: list[tuple[ShapeID, Mapping[str, JSONValue]]]
) -> list[Shape]:
    positions = {shape.id: index for index, shape in enumerate(shapes)}
    for target, traits in applies:
        container_id = target.without_member()
        if container_id not in positions:
            raise ModelError(f"Apply target not found: {target}")
        position = positions[container_id]
        shape = shapes[position]
        if target.member is None:
            shapes[position] = replace(
                shape, traits=_mapping({**shape.traits, **traits})
            )
            continue
        members = list(shape.members)
        for index, member in enumerate(members):
            if member.name == target.member:
                members[index] = replace(
                    member, traits=_mapping({**member.traits, **traits})
                )
                shapes[position] = replace(shape, members=tuple(members))
                break
        else:
            raise ModelError(f"Apply target member not found: {target}")
    return shapes
