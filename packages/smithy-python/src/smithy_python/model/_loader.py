# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Load a Smithy JSON AST into a flattened :class:`Model`.

Loading happens in phases:

1. Decode and structurally check the JSON AST, parsing every shape into an
   intermediate ``_RawShape`` (input order is kept everywhere; Python dicts
   preserve insertion order, and ``json`` decodes objects in document order).
2. Add the embedded prelude shapes the input does not define.
3. Apply ``"type": "apply"`` entries in input order. Traits applied to a shape
   or to one of its locally declared members are merged into that local
   definition (so they propagate through mixins); traits applied to a member
   the shape only inherits are kept aside and merged after flattening.
4. Flatten mixins (depth-first, memoized, cycle-checked).
5. Resolve every relationship and member target, then build the immutable
   shape objects.

Trait merge order, used both for mixins and member overrides, is ``dict``
update order: traits inherited from each mixin in declaration order, then the
shape's own traits, then applied traits. A key keeps the position where it was
first introduced and takes the value from the last writer.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Final, cast

from ..exceptions import InvalidShapeIdError, ModelError
from ._model import Model
from ._prelude import prelude_ast
from ._shape_id import ShapeId
from ._shapes import (
    MIXIN_TRAIT,
    SHAPE_CLASSES,
    UNIT,
    MemberShape,
    Node,
    OperationShape,
    ResourceShape,
    ServiceShape,
    Shape,
    ShapeType,
    SimpleShape,
)

# Smithy 1.0 differs semantically (set shapes, boxing), so only 2.x is loaded.
SUPPORTED_MAJOR_VERSION: Final = "2"

type _Json = dict[str, object]
type _Traits = dict[ShapeId, Node]

_LIFECYCLE: Final = ("create", "put", "read", "update", "delete", "list")


@dataclass(slots=True)
class _RawMember:
    target: ShapeId
    traits: _Traits


@dataclass(slots=True)
class _RawShape:
    id: ShapeId
    type: ShapeType
    traits: _Traits = field(default_factory=dict[ShapeId, Node])
    mixins: list[ShapeId] = field(default_factory=list[ShapeId])
    members: dict[str, _RawMember] = field(default_factory=dict[str, _RawMember])
    # Service / resource / operation properties. ``None`` means "not set".
    version: str | None = None
    refs: dict[str, ShapeId] = field(default_factory=dict[str, ShapeId])
    """Single references: resource lifecycle operations, operation input/output."""
    ref_lists: dict[str, list[ShapeId]] = field(
        default_factory=dict[str, list[ShapeId]]
    )
    """operations, resources, errors, collectionOperations."""
    named_refs: dict[str, dict[str, ShapeId]] = field(
        default_factory=dict[str, dict[str, ShapeId]]
    )
    """identifiers, properties."""
    rename: dict[ShapeId, str] = field(default_factory=dict[ShapeId, str])
    applied_member_traits: dict[str, _Traits] = field(
        default_factory=dict[str, _Traits]
    )
    """Traits applied to members this shape does not declare locally."""


def load_model(source: bytes | str | Mapping[str, object]) -> Model:
    """Load a Smithy JSON AST model.

    :param source: The JSON AST as bytes, text, or an already-decoded mapping.
    :returns: The flattened model, with embedded prelude shapes.
    :raises ModelError: If the input is malformed or a reference is dangling.
    """
    root = _decode(source)
    version = root.get("smithy")
    if not isinstance(version, str):
        raise ModelError('Smithy JSON AST model must contain a "smithy" version string')
    if version.partition(".")[0] != SUPPORTED_MAJOR_VERSION:
        raise ModelError(
            f"Unsupported Smithy version {version!r}: only Smithy "
            f"{SUPPORTED_MAJOR_VERSION}.x JSON ASTs are supported"
        )
    metadata = _freeze(_object(root.get("metadata", {}), '"metadata"'))
    shapes_node = _object(root.get("shapes", {}), '"shapes"')

    raw_shapes: dict[ShapeId, _RawShape] = {}
    applies: list[tuple[ShapeId, _Traits]] = []
    for key, value in shapes_node.items():
        shape_id = _parse_id(key, "Shape ID")
        node = _object(value, f"Shape {key}")
        type_name = node.get("type")
        if type_name == "apply":
            traits = _parse_traits(node.get("traits", {}), key)
            applies.append((shape_id, traits))
            continue
        if shape_id.member is not None:
            raise ModelError(
                f"Shape ID {key} must not contain a member; "
                "only apply entries may target members"
            )
        raw_shapes[shape_id] = _parse_shape(shape_id, node)

    for key, value in prelude_ast().items():
        shape_id = ShapeId.from_string(key)
        if shape_id not in raw_shapes:
            raw_shapes[shape_id] = _parse_shape(shape_id, dict(value))

    for target, traits in applies:
        _apply(raw_shapes, target, traits)

    flattener = _Flattener(raw_shapes)
    flat = {shape_id: flattener.flatten(shape_id) for shape_id in raw_shapes}

    for raw in flat.values():
        _check_required_members(raw)
        _check_references(raw, flat)

    return Model(
        smithy_version=version,
        metadata=cast(Mapping[str, Node], metadata),
        shapes={shape_id: _build(raw) for shape_id, raw in flat.items()},
    )


# --- Decoding -----------------------------------------------------------------


def _reject_constant(value: str) -> object:
    # Python's json module accepts NaN/Infinity by default; JSON does not.
    raise ValueError(f"{value} is not valid JSON")


def _decode(source: bytes | str | Mapping[str, object]) -> _Json:
    if isinstance(source, bytes | str):
        try:
            decoded: object = json.loads(source, parse_constant=_reject_constant)
        except ValueError as error:
            raise ModelError(f"Invalid JSON in Smithy model: {error}") from None
    else:
        decoded = source
    if not isinstance(decoded, Mapping):
        raise ModelError("Smithy JSON AST model must be a JSON object")
    return dict(cast(Mapping[str, object], decoded))


def _object(value: object, what: str) -> _Json:
    if not isinstance(value, Mapping):
        raise ModelError(f"{what} must be a JSON object")
    return dict(cast(Mapping[str, object], value))


def _array(value: object, what: str) -> list[object]:
    if not isinstance(value, list):
        raise ModelError(f"{what} must be a JSON array")
    return cast(list[object], value)


def _parse_id(value: object, what: str) -> ShapeId:
    if not isinstance(value, str):
        raise ModelError(f"{what} must be a string shape ID, found {value!r}")
    try:
        return ShapeId.from_string(value)
    except InvalidShapeIdError as error:
        raise InvalidShapeIdError(f"{what}: {error}") from None


def _parse_ref(value: object, what: str) -> ShapeId:
    """Parse a ``{"target": "ns#Name"}`` reference."""
    node = _object(value, what)
    if "target" not in node:
        raise ModelError(f'{what} is missing a "target"')
    return _parse_id(node["target"], what)


def _parse_traits(value: object, owner: str) -> _Traits:
    node = _object(value, f'{owner}: "traits"')
    return {
        _parse_id(key, f"{owner}: trait"): _freeze(trait) for key, trait in node.items()
    }


def _freeze(value: object) -> Node:
    """Copy a decoded JSON value into a deeply immutable form.

    Objects become read-only mappings (keeping key order) and arrays become
    tuples. Values inherited through mixins are shared between shapes, so
    freezing them keeps one consumer from changing another shape's traits.
    """
    if isinstance(value, Mapping):
        return MappingProxyType(
            {k: _freeze(v) for k, v in cast(Mapping[str, object], value).items()}
        )
    if isinstance(value, list | tuple):
        return tuple(_freeze(v) for v in cast(Sequence[object], value))
    return cast(Node, value)


def _parse_member(container: ShapeId, name: str, value: object) -> _RawMember:
    member_id = str(container.with_member(name))
    node = _object(value, f"Member {member_id}")
    if "target" not in node:
        raise ModelError(f'Member {member_id} is missing a "target"')
    return _RawMember(
        target=_parse_id(node["target"], f"Member {member_id}"),
        traits=_parse_traits(node.get("traits", {}), f"Member {member_id}"),
    )


def _parse_shape(shape_id: ShapeId, node: _Json) -> _RawShape:
    if "type" not in node:
        raise ModelError(f'Shape {shape_id} is missing a "type"')
    type_name = node["type"]
    try:
        shape_type = ShapeType(type_name)
    except ValueError:
        shape_type = None
    if shape_type is None or shape_type is ShapeType.MEMBER:
        raise ModelError(f"Shape {shape_id} has unknown type {type_name!r}")

    what = f"Shape {shape_id}"
    raw = _RawShape(
        id=shape_id,
        type=shape_type,
        traits=_parse_traits(node.get("traits", {}), what),
        mixins=[
            _parse_ref(ref, f"{what}: mixin")
            for ref in _array(node.get("mixins", []), f'{what}: "mixins"')
        ],
    )

    match shape_type:
        case ShapeType.LIST:
            _parse_named_members(raw, node, ("member",))
        case ShapeType.MAP:
            _parse_named_members(raw, node, ("key", "value"))
        case (
            ShapeType.STRUCTURE | ShapeType.UNION | ShapeType.ENUM | ShapeType.INT_ENUM
        ):
            members = _object(node.get("members", {}), f'{what}: "members"')
            for name, member in members.items():
                raw.members[name] = _parse_member(shape_id, name, member)
        case ShapeType.SERVICE:
            if "version" in node:
                version = node["version"]
                if not isinstance(version, str):
                    raise ModelError(f'{what}: "version" must be a string')
                raw.version = version
            _parse_ref_lists(raw, node, ("operations", "resources", "errors"))
            rename = _object(node.get("rename", {}), f'{what}: "rename"')
            for key, name in rename.items():
                if not isinstance(name, str):
                    raise ModelError(f'{what}: "rename" values must be strings')
                raw.rename[_parse_id(key, f"{what}: rename")] = name
        case ShapeType.RESOURCE:
            for prop in ("identifiers", "properties"):
                named = _object(node.get(prop, {}), f'{what}: "{prop}"')
                raw.named_refs[prop] = {
                    name: _parse_ref(ref, f"{what}: {prop} {name!r}")
                    for name, ref in named.items()
                }
            _parse_refs(raw, node, _LIFECYCLE)
            _parse_ref_lists(
                raw, node, ("operations", "collectionOperations", "resources")
            )
        case ShapeType.OPERATION:
            _parse_refs(raw, node, ("input", "output"))
            _parse_ref_lists(raw, node, ("errors",))
        case _:
            pass
    return raw


def _parse_named_members(raw: _RawShape, node: _Json, names: Iterable[str]) -> None:
    for name in names:
        if name in node:
            raw.members[name] = _parse_member(raw.id, name, node[name])


def _parse_refs(raw: _RawShape, node: _Json, keys: Iterable[str]) -> None:
    for key in keys:
        if key in node:
            raw.refs[key] = _parse_ref(node[key], f'Shape {raw.id}: "{key}"')


def _parse_ref_lists(raw: _RawShape, node: _Json, keys: Iterable[str]) -> None:
    for key in keys:
        what = f'Shape {raw.id}: "{key}"'
        if key in node:
            raw.ref_lists[key] = [
                _parse_ref(ref, what) for ref in _array(node[key], what)
            ]


# --- Apply ----------------------------------------------------------------------


def _merge_applied(traits: _Traits, applied: Mapping[ShapeId, Node]) -> None:
    """Merge applied traits; array values are concatenated as the spec requires."""
    for key, value in applied.items():
        existing = traits.get(key)
        if isinstance(existing, tuple) and isinstance(value, tuple):
            traits[key] = (*existing, *value)
        else:
            traits[key] = value


def _apply(
    raw_shapes: Mapping[ShapeId, _RawShape], target: ShapeId, traits: _Traits
) -> None:
    raw = raw_shapes.get(target.root)
    if raw is None:
        raise ModelError(
            f"Cannot apply traits to {target}: shape {target.root} is not defined"
        )
    if target.member is None:
        _merge_applied(raw.traits, traits)
    elif (member := raw.members.get(target.member)) is not None:
        _merge_applied(member.traits, traits)
    else:
        # Possibly an inherited member; checked after flattening.
        _merge_applied(raw.applied_member_traits.setdefault(target.member, {}), traits)


# --- Mixins ---------------------------------------------------------------------


def _inheritable_traits(mixin: _RawShape) -> _Traits:
    local: set[ShapeId] = {MIXIN_TRAIT}
    mixin_trait = mixin.traits.get(MIXIN_TRAIT)
    if isinstance(mixin_trait, Mapping):
        local_traits = cast(Mapping[str, Node], mixin_trait).get("localTraits", [])
        if isinstance(local_traits, tuple):
            for trait in local_traits:
                local.add(_parse_id(trait, f"Mixin {mixin.id}: localTraits"))
    return {k: v for k, v in mixin.traits.items() if k not in local}


def _union(*lists: Iterable[ShapeId]) -> list[ShapeId]:
    return list(dict.fromkeys(item for ids in lists for item in ids))


class _Flattener:
    def __init__(self, raw_shapes: Mapping[ShapeId, _RawShape]) -> None:
        self._raw = raw_shapes
        self._done: dict[ShapeId, _RawShape] = {}
        self._visiting: list[ShapeId] = []

    def flatten(self, shape_id: ShapeId) -> _RawShape:
        if (done := self._done.get(shape_id)) is not None:
            return done
        if shape_id in self._visiting:
            cycle = [*self._visiting[self._visiting.index(shape_id) :], shape_id]
            raise ModelError(
                "Mixin cycle detected: " + " -> ".join(str(i) for i in cycle)
            )
        raw = self._raw[shape_id]
        self._visiting.append(shape_id)
        try:
            mixins: list[_RawShape] = []
            for mixin_id in raw.mixins:
                if mixin_id not in self._raw:
                    raise ModelError(
                        f"Shape {shape_id} uses mixin {mixin_id}, which is not "
                        "defined in the model or prelude"
                    )
                mixin = self.flatten(mixin_id)
                if mixin.type is not raw.type:
                    raise ModelError(
                        f"Shape {shape_id} ({raw.type}) cannot use mixin "
                        f"{mixin_id} ({mixin.type})"
                    )
                mixins.append(mixin)
            flat = _merge(raw, mixins)
        finally:
            self._visiting.pop()
        self._done[shape_id] = flat
        return flat


def _merge(raw: _RawShape, mixins: list[_RawShape]) -> _RawShape:
    traits: _Traits = {}
    members: dict[str, _RawMember] = {}
    for mixin in mixins:
        traits.update(_inheritable_traits(mixin))
        for name, member in mixin.members.items():
            inherited = members.get(name)
            merged = {**inherited.traits} if inherited else {}
            merged.update(member.traits)
            members[name] = _RawMember(member.target, merged)
    traits.update(raw.traits)
    for name, member in raw.members.items():
        inherited = members.get(name)
        merged = {**inherited.traits, **member.traits} if inherited else member.traits
        members[name] = _RawMember(member.target, dict(merged))
    for name, applied in raw.applied_member_traits.items():
        member = members.get(name)
        if member is None:
            raise ModelError(
                f"Cannot apply traits to {raw.id.with_member(name)}: "
                f"member is not defined on {raw.id}"
            )
        _merge_applied(member.traits, applied)

    flat = _RawShape(
        id=raw.id,
        type=raw.type,
        traits=traits,
        mixins=list(raw.mixins),
        members=members,
        version=raw.version,
    )
    for mixin in mixins:
        if flat.version is None:
            flat.version = mixin.version
    if raw.version is not None:
        flat.version = raw.version

    for key in {k: None for m in [*mixins, raw] for k in m.refs}:
        value = raw.refs.get(key)
        for mixin in reversed(mixins):
            if value is not None:
                break
            value = mixin.refs.get(key)
        if value is not None:
            flat.refs[key] = value
    for key in {k: None for m in [*mixins, raw] for k in m.ref_lists}:
        flat.ref_lists[key] = _union(
            *(m.ref_lists.get(key, ()) for m in [*mixins, raw])
        )
    for key in {k: None for m in [*mixins, raw] for k in m.named_refs}:
        named: dict[str, ShapeId] = {}
        for m in [*mixins, raw]:
            named.update(m.named_refs.get(key, {}))
        flat.named_refs[key] = named
    for m in [*mixins, raw]:
        flat.rename.update(m.rename)
    return flat


# --- Validation -------------------------------------------------------------------


def _check_required_members(raw: _RawShape) -> None:
    required: tuple[str, ...] = ()
    if raw.type is ShapeType.LIST:
        required = ("member",)
    elif raw.type is ShapeType.MAP:
        required = ("key", "value")
    for name in required:
        if name not in raw.members:
            raise ModelError(f'Shape {raw.id} ({raw.type}) is missing its "{name}"')


def _check_references(raw: _RawShape, shapes: Mapping[ShapeId, _RawShape]) -> None:
    def missing(target: ShapeId) -> bool:
        return target not in shapes

    for name, member in raw.members.items():
        if missing(member.target):
            raise ModelError(
                f"Member {raw.id.with_member(name)} targets {member.target}, "
                "which is not defined in the model or prelude"
            )
    refs: list[ShapeId] = [
        *raw.refs.values(),
        *(ref for refs in raw.ref_lists.values() for ref in refs),
        *(ref for named in raw.named_refs.values() for ref in named.values()),
        *raw.rename,
    ]
    for ref in refs:
        if missing(ref):
            raise ModelError(
                f"Shape {raw.id} references {ref}, which is not defined in the "
                "model or prelude"
            )


# --- Building -----------------------------------------------------------------------


def _freeze_traits(traits: _Traits) -> Mapping[ShapeId, Node]:
    return MappingProxyType(dict(traits))


def _build(raw: _RawShape) -> Shape:
    traits = _freeze_traits(raw.traits)
    mixins = tuple(raw.mixins)
    members = MappingProxyType(
        {
            name: MemberShape(
                id=raw.id.with_member(name),
                target=member.target,
                traits=_freeze_traits(member.traits),
            )
            for name, member in raw.members.items()
        }
    )
    cls = SHAPE_CLASSES[raw.type]
    shape_id, shape_type = raw.id, raw.type
    lists = {k: tuple(v) for k, v in raw.ref_lists.items()}
    if cls is ServiceShape:
        return ServiceShape(
            id=shape_id,
            type=shape_type,
            traits=traits,
            mixins=mixins,
            version=raw.version,
            operations=lists.get("operations", ()),
            resources=lists.get("resources", ()),
            errors=lists.get("errors", ()),
            rename=MappingProxyType(dict(raw.rename)),
        )
    if cls is ResourceShape:
        return ResourceShape(
            id=shape_id,
            type=shape_type,
            traits=traits,
            mixins=mixins,
            identifiers=MappingProxyType(raw.named_refs.get("identifiers", {})),
            properties=MappingProxyType(raw.named_refs.get("properties", {})),
            create=raw.refs.get("create"),
            put=raw.refs.get("put"),
            read=raw.refs.get("read"),
            update=raw.refs.get("update"),
            delete=raw.refs.get("delete"),
            list=raw.refs.get("list"),
            operations=lists.get("operations", ()),
            collection_operations=lists.get("collectionOperations", ()),
            resources=lists.get("resources", ()),
        )
    if cls is OperationShape:
        return OperationShape(
            id=shape_id,
            type=shape_type,
            traits=traits,
            mixins=mixins,
            input=raw.refs.get("input", UNIT),
            output=raw.refs.get("output", UNIT),
            errors=lists.get("errors", ()),
        )
    # Simple shapes carry no members; aggregate shapes carry all of theirs.
    return cls(
        id=shape_id,
        type=shape_type,
        traits=traits,
        mixins=mixins,
        members=members if cls is not SimpleShape else MappingProxyType({}),
    )
