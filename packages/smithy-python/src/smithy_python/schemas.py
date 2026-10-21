# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Planning and emission for compact, lazily hydrated schemas."""

from __future__ import annotations

from collections.abc import Collection, Mapping
from dataclasses import dataclass
from math import isfinite
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from .dependencies import SMITHY_CORE
from .exceptions import CodegenError
from .model import Model, Node, OperationShape, Shape, ShapeId, ShapeType
from .symbols import SymbolProvider, TypeReference

if TYPE_CHECKING:
    from .generation import GenerationContext, TypesSettings
    from .writer import PythonWriter

# This contract is intentionally local to the generator. It must match
# smithy_core._schema_compact without making smithy-python import smithy-core.
_ENCODING_VERSION: Final = 2
_UNIT_INT: Final = -1
_PRIMITIVE_BOOLEAN_INT: Final = -2
_PRIMITIVE_BYTE_INT: Final = -3
_PRIMITIVE_SHORT_INT: Final = -4
_PRIMITIVE_INTEGER_INT: Final = -5
_PRIMITIVE_LONG_INT: Final = -6
_PRIMITIVE_FLOAT_INT: Final = -7
_PRIMITIVE_DOUBLE_INT: Final = -8

_TYPE_INTS: Final[Mapping[ShapeType, int]] = {
    ShapeType.BLOB: 1,
    ShapeType.BOOLEAN: 2,
    ShapeType.STRING: 3,
    ShapeType.TIMESTAMP: 4,
    ShapeType.BYTE: 5,
    ShapeType.SHORT: 6,
    ShapeType.INTEGER: 7,
    ShapeType.LONG: 8,
    ShapeType.FLOAT: 9,
    ShapeType.DOUBLE: 10,
    ShapeType.BIG_INTEGER: 11,
    ShapeType.BIG_DECIMAL: 12,
    ShapeType.DOCUMENT: 13,
    ShapeType.ENUM: 14,
    ShapeType.INT_ENUM: 15,
    ShapeType.LIST: 16,
    ShapeType.MAP: 17,
    ShapeType.STRUCTURE: 18,
    ShapeType.UNION: 19,
    ShapeType.SERVICE: 21,
    ShapeType.OPERATION: 23,
}


def _shape_id(value: str) -> ShapeId:
    return ShapeId.from_string(value)


_PRELUDE_INTS: Final[Mapping[ShapeId, int]] = {
    _shape_id("smithy.api#Blob"): 1,
    _shape_id("smithy.api#Boolean"): 2,
    _shape_id("smithy.api#String"): 3,
    _shape_id("smithy.api#Timestamp"): 4,
    _shape_id("smithy.api#Byte"): 5,
    _shape_id("smithy.api#Short"): 6,
    _shape_id("smithy.api#Integer"): 7,
    _shape_id("smithy.api#Long"): 8,
    _shape_id("smithy.api#Float"): 9,
    _shape_id("smithy.api#Double"): 10,
    _shape_id("smithy.api#BigInteger"): 11,
    _shape_id("smithy.api#BigDecimal"): 12,
    _shape_id("smithy.api#Document"): 13,
    _shape_id("smithy.api#PrimitiveBoolean"): _PRIMITIVE_BOOLEAN_INT,
    _shape_id("smithy.api#PrimitiveByte"): _PRIMITIVE_BYTE_INT,
    _shape_id("smithy.api#PrimitiveShort"): _PRIMITIVE_SHORT_INT,
    _shape_id("smithy.api#PrimitiveInteger"): _PRIMITIVE_INTEGER_INT,
    _shape_id("smithy.api#PrimitiveLong"): _PRIMITIVE_LONG_INT,
    _shape_id("smithy.api#PrimitiveFloat"): _PRIMITIVE_FLOAT_INT,
    _shape_id("smithy.api#PrimitiveDouble"): _PRIMITIVE_DOUBLE_INT,
    _shape_id("smithy.api#Unit"): _UNIT_INT,
}

# Bit position must match smithy_core._schema_compact._TRAIT_BITS.
_TRAIT_BITS: Final = tuple(
    map(
        _shape_id,
        (
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
        ),
    )
)
_TRAIT_BIT_INDEX: Final = {
    trait_id: index for index, trait_id in enumerate(_TRAIT_BITS)
}

# This is the client-side set from Java's SchemaTraitFilterIndex. Constraint
# traits are intentionally omitted because standalone types do not enable
# server-side validation.
_INCLUDED_TRAITS: Final = frozenset(
    map(
        _shape_id,
        (
            "smithy.api#sparse",
            "smithy.api#sensitive",
            "smithy.api#idempotencyToken",
            "smithy.api#default",
            "smithy.api#enumValue",
            "smithy.api#required",
            "smithy.api#input",
            "smithy.api#output",
            "smithy.api#timestampFormat",
            "smithy.synthetic#originalShapeId",
            "aws.api#service",
            "smithy.rules#endpointBdd",
            "smithy.api#longPoll",
            "smithy.api#requestCompression",
            "smithy.api#jsonName",
            "smithy.api#mediaType",
            "smithy.api#xmlAttribute",
            "smithy.api#xmlFlattened",
            "smithy.api#xmlName",
            "smithy.api#xmlNamespace",
            "smithy.api#streaming",
            "smithy.api#endpoint",
            "smithy.api#error",
            "smithy.api#requiresLength",
            "smithy.api#eventHeader",
            "smithy.api#eventPayload",
            "smithy.api#httpError",
            "smithy.api#http",
            "smithy.api#httpHeader",
            "smithy.api#httpQuery",
            "smithy.api#httpLabel",
            "smithy.api#httpPayload",
            "smithy.api#httpPrefixHeaders",
            "smithy.api#httpQueryParams",
            "smithy.api#httpResponseCode",
            "smithy.api#hostLabel",
        ),
    )
)
_DEFAULT_TRAIT: Final = _shape_id("smithy.api#default")
_INPUT_TRAIT: Final = _shape_id("smithy.api#input")
_OUTPUT_TRAIT: Final = _shape_id("smithy.api#output")
_DEFINITION_TRAITS: Final = (
    _shape_id("smithy.api#protocolDefinition"),
    _shape_id("smithy.api#authDefinition"),
)

_STATIC_SCHEMA: Final = TypeReference(
    "StaticSchema",
    "smithy_core._schema_compact",
    dependencies=(SMITHY_CORE,),
)
_MAPPING_PROXY: Final = TypeReference("MappingProxyType", "types")
_TYPED_MAPPING_PROXY: Final = TypeReference(
    "MappingProxyType",
    "types",
    arguments=(
        TypeReference("str", "builtins"),
        TypeReference("object", "builtins"),
    ),
)

type _SourcePart = str | TypeReference
type _TraitPlan = int | Mapping[ShapeId, Node]


@dataclass(frozen=True, slots=True)
class SchemaPlan:
    """Derived semantic data used to emit compact schemas."""

    shapes: tuple[Shape, ...]
    names: Mapping[ShapeId, str]
    strings: Mapping[str, str]
    traits: Mapping[ShapeId, _TraitPlan]

    @classmethod
    def from_shapes(
        cls,
        model: Model,
        shapes: tuple[Shape, ...],
        symbols: SymbolProvider,
    ) -> SchemaPlan:
        """Plan schema order, filtered traits, names, and interned strings."""
        emitted = _schema_order(shapes)
        included = _included_traits(model)
        inputs = {operation.input for operation in model.iter_shapes(OperationShape)}
        outputs = {operation.output for operation in model.iter_shapes(OperationShape)}
        strings = _StringStore()
        traits: dict[ShapeId, _TraitPlan] = {}
        for shape in emitted:
            additional: list[ShapeId] = []
            if shape.type is ShapeType.STRUCTURE:
                if shape.id in inputs:
                    additional.append(_INPUT_TRAIT)
                if shape.id in outputs:
                    additional.append(_OUTPUT_TRAIT)
            shape_traits = _plan_traits(shape, included, additional)
            traits[shape.id] = shape_traits
            strings.intern(shape.id.namespace, preferred="n")
            strings.intern(shape.id.name)
            _intern_traits(strings, shape_traits)
            for member in shape.members.values():
                member_traits = _plan_traits(member, included)
                traits[member.id] = member_traits
                strings.intern(member.name)
                _intern_traits(strings, member_traits)

        return cls(
            shapes=emitted,
            names=MappingProxyType(
                {shape.id: symbols.schema_name(shape.id) for shape in emitted}
            ),
            strings=MappingProxyType(strings.values),
            traits=MappingProxyType(traits),
        )


class SchemaGenerator:
    """Emit the compact schema module for a standalone types package."""

    def generate(self, context: GenerationContext[TypesSettings]) -> None:
        """Register ``<package>._private.schemas`` with the file manifest."""
        package = context.settings.package
        path = f"src/{package.replace('.', '/')}/_private/schemas.py"
        writer = context.files.python_module(path, f"{package}._private.schemas")
        plan = context.plan.schemas
        for value, name in plan.strings.items():
            writer.line(name, " = ", repr(value))
        if plan.strings:
            writer.line()

        written: set[ShapeId] = set()
        for shape in plan.shapes:
            _write_shape(writer, plan, shape, written)
            written.add(shape.id)


def _write_shape(
    writer: PythonWriter,
    plan: SchemaPlan,
    shape: Shape,
    written: set[ShapeId],
) -> None:
    writer.line(plan.names[shape.id], ": ", _STATIC_SCHEMA, " = (")
    with writer.indent():
        writer.line(f"{_TYPE_INTS[shape.type]},")
        writer.line(plan.strings[shape.id.namespace], ",")
        writer.line(plan.strings[shape.id.name], ",")
        writer.line(*_trait_parts(plan, plan.traits[shape.id]), ",")
        if shape.members:
            writer.line(
                "(",
                ", ".join(
                    plan.strings[member.name] for member in shape.members.values()
                ),
                ",),",
            )
            writer.line("(")
            with writer.indent():
                for member in shape.members.values():
                    writer.line(
                        "(",
                        _schema_ref(plan, member.target, written),
                        ", ",
                        *_trait_parts(plan, plan.traits[member.id]),
                        "),",
                    )
            writer.line("),")
    writer.line(")")
    writer.line()


def _included_traits(model: Model) -> frozenset[ShapeId]:
    included = set(_INCLUDED_TRAITS)
    for shape in model.iter_shapes():
        for definition_trait in _DEFINITION_TRAITS:
            if not shape.has_trait(definition_trait):
                continue
            included.add(shape.id)
            definition = shape.get_trait(definition_trait)
            if not isinstance(definition, Mapping):
                continue
            referenced = definition.get("traits")
            if not isinstance(referenced, tuple):
                continue
            for value in referenced:
                if isinstance(value, str):
                    included.add(_shape_id(value))
    return frozenset(included)


def _plan_traits(
    shape: Shape,
    included: frozenset[ShapeId],
    additional: Collection[ShapeId] = (),
) -> _TraitPlan:
    bits = 0
    values: dict[ShapeId, Node] = {}
    valueless_bits: list[ShapeId] = []
    for trait_id, value in shape.traits.items():
        if trait_id not in included:
            continue
        valueless = (
            trait_id != _DEFAULT_TRAIT and isinstance(value, Mapping) and not value
        )
        bit = _TRAIT_BIT_INDEX.get(trait_id)
        if valueless and bit is not None:
            bits |= 1 << bit
            valueless_bits.append(trait_id)
        else:
            values[trait_id] = None if valueless else value
    for trait_id in additional:
        bit = _TRAIT_BIT_INDEX.get(trait_id)
        if bit is not None:
            bits |= 1 << bit
            valueless_bits.append(trait_id)
        else:
            values[trait_id] = None
    if not values:
        return bits
    values.update(dict.fromkeys(valueless_bits))
    return MappingProxyType(values)


def _trait_parts(plan: SchemaPlan, traits: _TraitPlan) -> tuple[_SourcePart, ...]:
    if isinstance(traits, int):
        return (str(traits),)
    parts: list[_SourcePart] = ["{"]
    for index, (trait_id, value) in enumerate(traits.items()):
        if index:
            parts.append(", ")
        parts.extend((plan.strings[str(trait_id)], ": "))
        parts.extend(
            _node_parts(
                value,
                strings=plan.strings,
                intern_string=True,
            )
        )
    parts.append("}")
    return tuple(parts)


def _node_parts(
    value: Node,
    *,
    strings: Mapping[str, str],
    intern_string: bool = False,
) -> tuple[_SourcePart, ...]:
    if value is None:
        return ("None",)
    if isinstance(value, bool):
        return ("True" if value else "False",)
    if isinstance(value, str):
        if intern_string:
            return (strings[value],)
        return (repr(value),)
    if isinstance(value, float) and not isfinite(value):
        raise CodegenError("Cannot emit a non-finite numeric trait value")
    if isinstance(value, int | float):
        return (repr(value),)
    if isinstance(value, tuple):
        parts: list[_SourcePart] = ["("]
        for index, item in enumerate(value):
            if index:
                parts.append(", ")
            parts.extend(_node_parts(item, strings=strings))
        if len(value) == 1:
            parts.append(",")
        parts.append(")")
        return tuple(parts)

    proxy = _TYPED_MAPPING_PROXY if not value else _MAPPING_PROXY
    parts = [proxy, "({"]
    for index, (key, item) in enumerate(value.items()):
        if index:
            parts.append(", ")
        parts.extend((repr(key), ": "))
        parts.extend(_node_parts(item, strings=strings))
    parts.append("})")
    return tuple(parts)


def _schema_ref(plan: SchemaPlan, target: ShapeId, written: set[ShapeId]) -> str:
    if (prelude := _PRELUDE_INTS.get(target)) is not None:
        return str(prelude)
    try:
        name = plan.names[target]
    except KeyError as error:
        raise CodegenError(f"Schema target {target} was not selected") from error
    return name if target in written else f"lambda: {name}"


def _schema_order(
    shapes: tuple[Shape, ...],
) -> tuple[Shape, ...]:
    by_id = {shape.id: shape for shape in shapes}
    graph = {
        shape.id: tuple(
            member.target for member in shape.members.values() if member.target in by_id
        )
        for shape in shapes
    }
    reverse: dict[ShapeId, list[ShapeId]] = {shape.id: [] for shape in shapes}
    for source, targets in graph.items():
        for target in targets:
            reverse[target].append(source)

    finished: list[ShapeId] = []
    visited: set[ShapeId] = set()
    for root in graph:
        if root in visited:
            continue
        visited.add(root)
        pending: list[tuple[ShapeId, int]] = [(root, 0)]
        while pending:
            current, index = pending[-1]
            targets = graph[current]
            if index == len(targets):
                finished.append(current)
                pending.pop()
                continue
            target = targets[index]
            pending[-1] = (current, index + 1)
            if target not in visited:
                visited.add(target)
                pending.append((target, 0))

    recursive: set[ShapeId] = set()
    visited.clear()
    for root in reversed(finished):
        if root in visited:
            continue
        component: list[ShapeId] = []
        component_pending = [root]
        visited.add(root)
        while component_pending:
            current = component_pending.pop()
            component.append(current)
            for target in reverse[current]:
                if target not in visited:
                    visited.add(target)
                    component_pending.append(target)
        if len(component) > 1 or root in graph[root]:
            recursive.update(component)

    return (
        *(by_id[shape_id] for shape_id in finished if shape_id not in recursive),
        *(shape for shape in shapes if shape.id in recursive),
    )


def _intern_traits(strings: _StringStore, traits: _TraitPlan) -> None:
    if isinstance(traits, int):
        return
    for trait_id, value in traits.items():
        strings.intern(str(trait_id))
        if isinstance(value, str):
            strings.intern(value)


class _StringStore:
    __slots__ = ("_allocated", "_next", "values")

    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self._allocated: set[str] = set()
        self._next: dict[str, int] = {}

    def intern(self, value: str, *, preferred: str | None = None) -> str:
        existing = self.values.get(value)
        if existing is not None:
            return existing
        prefix = preferred or "_s"
        suffix = self._next.get(prefix, 0)
        candidate = f"{prefix}{suffix}"
        while candidate in self._allocated:
            suffix += 1
            candidate = f"{prefix}{suffix}"
        self._next[prefix] = suffix + 1
        self._allocated.add(candidate)
        self.values[value] = candidate
        return candidate
