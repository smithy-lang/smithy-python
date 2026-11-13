# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Planning and emission for compact, lazily hydrated schemas."""

from __future__ import annotations

from collections.abc import Collection, Mapping
from dataclasses import dataclass
from math import ceil, isfinite, sqrt
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from . import dependencies as _dependencies
from . import exceptions as _exceptions
from . import model as _model
from . import symbols as _symbols

if TYPE_CHECKING:
    from .generation import GenerationContext, ModelArtifactSettings
    from .writer import PythonWriter

__all__ = ["SchemaGenerator", "SchemaPlan"]

_PARTITION_BALANCE_TOLERANCE: Final = 0.25
_MIN_COMMON_OPERATION_COUNT: Final = 12
_AFFINITY_PASSES: Final = 3


@dataclass(frozen=True, slots=True)
class SchemaPlan:
    """Derived semantic data used to emit compact schemas."""

    shapes: tuple[_model.Shape, ...]
    partition_groups: tuple[tuple[_model.Shape, ...], ...]
    operations_by_group: tuple[frozenset[_model.ShapeId], ...]
    names: Mapping[_model.ShapeId, str]
    strings: Mapping[str, str]
    traits: Mapping[_model.ShapeId, _TraitPlan]

    @classmethod
    def from_shapes(
        cls,
        model: _model.Model,
        shapes: tuple[_model.Shape, ...],
        symbols: _symbols.SymbolProvider,
        *,
        retained_traits: Collection[_model.ShapeId] = (),
    ) -> SchemaPlan:
        """Plan schema order, filtered traits, names, and interned strings.

        ``retained_traits`` are kept even when the model omits their definitions.
        """
        emitted, recursive_groups = _schema_order(shapes)
        operations = _partition_operations(model, emitted)
        partition_groups = _merge_operation_groups(operations, recursive_groups)
        operations_by_group = _operations_by_group(
            partition_groups,
            _operation_closures(emitted, operations),
        )
        included = _included_traits(model) | frozenset(retained_traits)
        inputs = {
            operation.input for operation in model.iter_shapes(_model.OperationShape)
        }
        outputs = {
            operation.output for operation in model.iter_shapes(_model.OperationShape)
        }
        strings = _StringStore()
        traits: dict[_model.ShapeId, _TraitPlan] = {}
        for shape in emitted:
            additional: list[_model.ShapeId] = []
            if shape.type is _model.ShapeType.STRUCTURE:
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
            partition_groups=partition_groups,
            operations_by_group=operations_by_group,
            names=MappingProxyType(
                {shape.id: symbols.schema_name(shape.id) for shape in emitted}
            ),
            strings=MappingProxyType(strings.values),
            traits=MappingProxyType(traits),
        )


class SchemaGenerator:
    """Emit the compact schema module for a standalone types package."""

    def generate(self, context: GenerationContext[ModelArtifactSettings]) -> None:
        """Register ``<package>._private.schemas`` with the file manifest."""
        package = context.settings.package
        directory = package.replace(".", "/")
        plan = context.plan.schemas
        size = context.settings.schema_partition_size
        if size is None or len(plan.shapes) <= size:
            writer = context.files.python_module(
                f"src/{directory}/_private/schemas.py",
                f"{package}._private.schemas",
            )
            _write_schema_module(writer, plan, plan.shapes)
            return

        partitions = _schema_partitions(plan, size)
        width = len(str(len(partitions) - 1))
        _write_schema_facade(
            context.files.python_module(
                f"src/{directory}/_private/schemas.py",
                f"{package}._private.schemas",
            ),
            plan,
            partitions,
        )
        for index, shapes in enumerate(partitions):
            module = f"schemas_{index:0{width}d}"
            _write_schema_module(
                context.files.python_module(
                    f"src/{directory}/_private/{module}.py",
                    f"{package}._private.{module}",
                ),
                plan,
                shapes,
                facade="schemas",
            )


_IMPORT_MODULE: Final = _symbols.TypeReference("import_module", "importlib")


def _write_schema_facade(
    writer: PythonWriter,
    plan: SchemaPlan,
    partitions: tuple[tuple[_model.Shape, ...], ...],
) -> None:
    width = len(str(len(partitions) - 1))
    writer.line("_PARTITION_NAMES: tuple[tuple[str, ...], ...] = (")
    with writer.indent():
        for shapes in partitions:
            writer.line("(")
            with writer.indent():
                for shape in shapes:
                    writer.line(repr(plan.names[shape.id]), ",")
            writer.line("),")
    writer.line(")")
    writer.line("_PARTITIONS = {")
    with writer.indent():
        writer.line("name: index")
        writer.line("for index, names in enumerate(_PARTITION_NAMES)")
        writer.line("for name in names")
    writer.line("}")
    writer.line("del _PARTITION_NAMES")
    writer.line("def __getattr__(name: str):")
    with writer.indent():
        writer.line("try:")
        with writer.indent():
            writer.line("partition = _PARTITIONS[name]")
        writer.line("except KeyError as error:")
        with writer.indent():
            writer.line("raise AttributeError(name) from error")
        writer.line(
            "module = ",
            _IMPORT_MODULE,
            f'(f".schemas_{{partition:0{width}d}}", __package__)',
        )
        writer.line("value = getattr(module, name)")
        writer.line("globals()[name] = value")
        writer.line("return value")
    writer.line()
    writer.line()
    writer.line("def __dir__() -> list[str]:")
    with writer.indent():
        writer.line("return sorted({*globals(), *_PARTITIONS})")


def _write_schema_module(
    writer: PythonWriter,
    plan: SchemaPlan,
    shapes: tuple[_model.Shape, ...],
    *,
    facade: str | None = None,
) -> None:
    local = frozenset(shape.id for shape in shapes)
    if facade is not None and any(
        target in plan.names and target not in local
        for shape in shapes
        for target in _schema_references(shape)
    ):
        writer.line("from . import ", facade)
        writer.line()
    strings = _schema_strings(plan, shapes)
    for value, name in plan.strings.items():
        if value in strings:
            writer.line(name, " = ", repr(value))
    if strings:
        writer.line()

    written: set[_model.ShapeId] = set()
    for shape in shapes:
        _write_shape(writer, plan, shape, written, local=local, facade=facade)
        written.add(shape.id)


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

_TYPE_INTS: Final[Mapping[_model.ShapeType, int]] = {
    _model.ShapeType.BLOB: 1,
    _model.ShapeType.BOOLEAN: 2,
    _model.ShapeType.STRING: 3,
    _model.ShapeType.TIMESTAMP: 4,
    _model.ShapeType.BYTE: 5,
    _model.ShapeType.SHORT: 6,
    _model.ShapeType.INTEGER: 7,
    _model.ShapeType.LONG: 8,
    _model.ShapeType.FLOAT: 9,
    _model.ShapeType.DOUBLE: 10,
    _model.ShapeType.BIG_INTEGER: 11,
    _model.ShapeType.BIG_DECIMAL: 12,
    _model.ShapeType.DOCUMENT: 13,
    _model.ShapeType.ENUM: 14,
    _model.ShapeType.INT_ENUM: 15,
    _model.ShapeType.LIST: 16,
    _model.ShapeType.MAP: 17,
    _model.ShapeType.STRUCTURE: 18,
    _model.ShapeType.UNION: 19,
    _model.ShapeType.SERVICE: 21,
    _model.ShapeType.OPERATION: 23,
}


def _shape_id(value: str) -> _model.ShapeId:
    return _model.ShapeId.from_string(value)


_PRELUDE_INTS: Final[Mapping[_model.ShapeId, int]] = {
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

_STATIC_SCHEMA: Final = _symbols.TypeReference(
    "StaticSchema",
    "smithy_core._schema_compact",
    dependencies=(_dependencies.SMITHY_CORE,),
)
_STATIC_OPERATION_SCHEMA: Final = _symbols.TypeReference(
    "StaticOperationSchema",
    "smithy_core._schema_compact",
    dependencies=(_dependencies.SMITHY_CORE,),
)
_MAPPING_PROXY: Final = _symbols.TypeReference("MappingProxyType", "types")
_TYPED_MAPPING_PROXY: Final = _symbols.TypeReference(
    "MappingProxyType",
    "types",
    arguments=(
        _symbols.TypeReference("str", "builtins"),
        _symbols.TypeReference("object", "builtins"),
    ),
)

type _SourcePart = str | _symbols.TypeReference
type _TraitPlan = int | Mapping[_model.ShapeId, _model.Node]


def _write_shape(
    writer: PythonWriter,
    plan: SchemaPlan,
    shape: _model.Shape,
    written: set[_model.ShapeId],
    *,
    local: Collection[_model.ShapeId],
    facade: str | None,
) -> None:
    is_operation = isinstance(shape, _model.OperationShape)
    annotation = _STATIC_OPERATION_SCHEMA if is_operation else _STATIC_SCHEMA
    writer.line(plan.names[shape.id], ": ", annotation, " = (")
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
                        *_schema_ref(
                            plan,
                            member.target,
                            written,
                            local=local,
                            facade=facade,
                        ),
                        ", ",
                        *_trait_parts(plan, plan.traits[member.id]),
                        "),",
                    )
            writer.line("),")
        if isinstance(shape, _model.OperationShape):

            def ref(target: _model.ShapeId) -> tuple[_SourcePart, ...]:
                return _schema_ref(plan, target, written, local=local, facade=facade)

            writer.line(*ref(shape.input), ",")
            writer.line(*ref(shape.output), ",")
            errors: list[_SourcePart] = ["("]
            for index, error in enumerate(shape.errors):
                errors.extend((", " if index else "", *ref(error)))
            writer.line(*errors, "," if len(shape.errors) == 1 else "", "),")
    writer.line(")")
    writer.line()


def _included_traits(model: _model.Model) -> frozenset[_model.ShapeId]:
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
    shape: _model.Shape,
    included: frozenset[_model.ShapeId],
    additional: Collection[_model.ShapeId] = (),
) -> _TraitPlan:
    bits = 0
    values: dict[_model.ShapeId, _model.Node] = {}
    valueless_bits: list[_model.ShapeId] = []
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
    value: _model.Node,
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
        raise _exceptions.CodegenError("Cannot emit a non-finite numeric trait value")
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


def _schema_ref(
    plan: SchemaPlan,
    target: _model.ShapeId,
    written: set[_model.ShapeId],
    *,
    local: Collection[_model.ShapeId],
    facade: str | None,
) -> tuple[_SourcePart, ...]:
    if (prelude := _PRELUDE_INTS.get(target)) is not None:
        return (str(prelude),)
    try:
        name = plan.names[target]
    except KeyError as error:
        raise _exceptions.CodegenError(
            f"Schema target {target} was not selected"
        ) from error
    if target in local:
        return (name if target in written else f"lambda: {name}",)
    if facade is None:
        raise _exceptions.CodegenError(f"Schema target {target} is not in this module")
    return ("lambda: ", facade, ".", name)


def _schema_order(
    shapes: tuple[_model.Shape, ...],
) -> tuple[
    tuple[_model.Shape, ...],
    tuple[tuple[_model.Shape, ...], ...],
]:
    by_id = {shape.id: shape for shape in shapes}
    positions = {shape.id: index for index, shape in enumerate(shapes)}
    graph = {
        shape.id: tuple(
            target for target in _schema_references(shape) if target in by_id
        )
        for shape in shapes
    }
    reverse: dict[_model.ShapeId, list[_model.ShapeId]] = {
        shape.id: [] for shape in shapes
    }
    for source, targets in graph.items():
        for target in targets:
            reverse[target].append(source)

    finished: list[_model.ShapeId] = []
    visited: set[_model.ShapeId] = set()
    for root in graph:
        if root in visited:
            continue
        visited.add(root)
        pending: list[tuple[_model.ShapeId, int]] = [(root, 0)]
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

    recursive: set[_model.ShapeId] = set()
    recursive_components: dict[_model.ShapeId, tuple[_model.ShapeId, ...]] = {}
    visited.clear()
    for root in reversed(finished):
        if root in visited:
            continue
        component: list[_model.ShapeId] = []
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
            ordered_component = tuple(sorted(component, key=positions.__getitem__))
            for shape_id in component:
                recursive_components[shape_id] = ordered_component

    emitted = (
        *(by_id[shape_id] for shape_id in finished if shape_id not in recursive),
        *(shape for shape in shapes if shape.id in recursive),
    )
    groups: list[tuple[_model.Shape, ...]] = []
    grouped: set[_model.ShapeId] = set()
    for shape in emitted:
        if shape.id in grouped:
            continue
        group_ids = recursive_components.get(shape.id, (shape.id,))
        groups.append(tuple(by_id[shape_id] for shape_id in group_ids))
        grouped.update(group_ids)
    return emitted, tuple(groups)


def _schema_references(shape: _model.Shape) -> tuple[_model.ShapeId, ...]:
    references = dict.fromkeys(member.target for member in shape.members.values())
    if isinstance(shape, _model.OperationShape):
        references.update(dict.fromkeys((shape.input, shape.output, *shape.errors)))
    return tuple(references)


def _merge_operation_groups(
    operations: tuple[_model.OperationShape, ...],
    groups: tuple[tuple[_model.Shape, ...], ...],
) -> tuple[tuple[_model.Shape, ...], ...]:
    group_by_shape: dict[_model.ShapeId, int] = {}
    parents = list(range(len(groups)))
    for index, group in enumerate(groups):
        for shape in group:
            group_by_shape[shape.id] = index

    for operation in operations:
        _merge_groups(parents, group_by_shape, operation.id, operation.input)
        _merge_groups(parents, group_by_shape, operation.id, operation.output)
        _merge_groups(parents, group_by_shape, operation.input, operation.output)

    merged: dict[int, list[_model.Shape]] = {}
    for index, group in enumerate(groups):
        merged.setdefault(_find_group(parents, index), []).extend(group)
    return tuple(tuple(group) for group in merged.values())


def _merge_groups(
    parents: list[int],
    group_by_shape: Mapping[_model.ShapeId, int],
    left_shape: _model.ShapeId,
    right_shape: _model.ShapeId,
) -> None:
    left = group_by_shape.get(left_shape)
    right = group_by_shape.get(right_shape)
    if left is None or right is None:
        return
    left_root = _find_group(parents, left)
    right_root = _find_group(parents, right)
    if left_root != right_root:
        parents[max(left_root, right_root)] = min(left_root, right_root)


def _find_group(parents: list[int], group: int) -> int:
    root = group
    while parents[root] != root:
        root = parents[root]
    while parents[group] != group:
        next_group = parents[group]
        parents[group] = root
        group = next_group
    return root


def _schema_partitions(
    plan: SchemaPlan,
    size: int,
) -> tuple[tuple[_model.Shape, ...], ...]:
    groups = plan.partition_groups
    partitions: list[tuple[_model.Shape, ...]] = []
    current: list[_model.Shape] = []
    for group in groups:
        if current and len(current) + len(group) > size:
            partitions.append(tuple(current))
            current.clear()
        current.extend(group)
    if current:
        partitions.append(tuple(current))
    partition_count = len(partitions)
    if partition_count < 2:
        return tuple(partitions)

    weights = tuple(_schema_group_weight(plan, group) for group in groups)
    layout = _source_balanced_layout(weights, partition_count)
    layout = _improve_operation_affinity_layout(
        tuple(map(len, groups)),
        weights,
        plan.operations_by_group,
        layout,
        size,
    )
    return tuple(
        tuple(shape for group_index in partition for shape in groups[group_index])
        for partition in layout
    )


def _source_balanced_layout(
    weights: tuple[int, ...],
    partition_count: int,
) -> list[list[int]]:
    partitions: list[list[int]] = []
    start = 0
    remaining_weight = sum(weights)
    for remaining_parts in range(partition_count, 1, -1):
        target = remaining_weight / remaining_parts
        end = start
        weight = 0
        last_end = len(weights) - remaining_parts + 1
        while end < last_end:
            next_weight = weight + weights[end]
            if weight and abs(target - weight) <= abs(target - next_weight):
                break
            weight = next_weight
            end += 1
        partitions.append(list(range(start, end)))
        start = end
        remaining_weight -= weight
    partitions.append(list(range(start, len(weights))))
    return partitions


def _operation_closures(
    shapes: tuple[_model.Shape, ...],
    operations: tuple[_model.OperationShape, ...],
) -> dict[_model.ShapeId, frozenset[_model.ShapeId]]:
    by_id = {shape.id: shape for shape in shapes}
    closures: dict[_model.ShapeId, frozenset[_model.ShapeId]] = {}
    for operation in operations:
        visited: set[_model.ShapeId] = set()
        pending = [operation.id]
        while pending:
            current = pending.pop()
            if current in visited:
                continue
            visited.add(current)
            current_shape = operation if current == operation.id else by_id.get(current)
            if current_shape is None:
                continue
            pending.extend(
                target
                for target in reversed(_schema_references(current_shape))
                if target in by_id and target not in visited
            )
        closures[operation.id] = frozenset(visited)
    return closures


def _partition_operations(
    model: _model.Model,
    shapes: tuple[_model.Shape, ...],
) -> tuple[_model.OperationShape, ...]:
    emitted = tuple(
        shape for shape in shapes if isinstance(shape, _model.OperationShape)
    )
    if emitted:
        return emitted
    return tuple(model.iter_shapes(_model.OperationShape))


def _operations_by_group(
    groups: tuple[tuple[_model.Shape, ...], ...],
    operation_closures: Mapping[_model.ShapeId, Collection[_model.ShapeId]],
) -> tuple[frozenset[_model.ShapeId], ...]:
    group_by_shape = {
        shape.id: index for index, group in enumerate(groups) for shape in group
    }
    operations_by_group: list[set[_model.ShapeId]] = [set() for _ in groups]
    for operation, closure in operation_closures.items():
        for shape_id in closure:
            if (group := group_by_shape.get(shape_id)) is not None:
                operations_by_group[group].add(operation)
    return tuple(frozenset(operations) for operations in operations_by_group)


def _improve_operation_affinity_layout(
    group_shape_counts: tuple[int, ...],
    group_weights: tuple[int, ...],
    group_operations: tuple[Collection[_model.ShapeId], ...],
    initial_layout: list[list[int]],
    target_size: int,
) -> list[list[int]]:
    assigned = [list(partition) for partition in initial_layout]
    partition_count = len(assigned)
    shape_counts = [0] * partition_count
    source_weights = [0] * partition_count
    operation_counts: list[dict[_model.ShapeId, int]] = []
    operation_locations: dict[_model.ShapeId, set[int]] = {}
    for partition, group_indexes in enumerate(assigned):
        counts: dict[_model.ShapeId, int] = {}
        for group_index in group_indexes:
            shape_counts[partition] += group_shape_counts[group_index]
            source_weights[partition] += group_weights[group_index]
            for operation in sorted(group_operations[group_index]):
                counts[operation] = counts.get(operation, 0) + 1
        operation_counts.append(counts)
        for operation in counts:
            operation_locations.setdefault(operation, set()).add(partition)

    ideal_source_weight = sum(group_weights) / partition_count
    ideal_shape_count = sum(group_shape_counts) / partition_count
    source_ceilings = [
        max(
            ceil(ideal_source_weight * (1 + _PARTITION_BALANCE_TOLERANCE)),
            source_weight,
        )
        for source_weight in source_weights
    ]
    source_floors = [
        min(
            int(ideal_source_weight * (1 - _PARTITION_BALANCE_TOLERANCE)),
            source_weight,
        )
        for source_weight in source_weights
    ]
    shape_ceilings = [
        max(
            shape_count,
            ceil(
                max(target_size, ideal_shape_count) * (1 + _PARTITION_BALANCE_TOLERANCE)
            ),
        )
        for shape_count in shape_counts
    ]
    common_threshold = max(
        _MIN_COMMON_OPERATION_COUNT,
        ceil(sqrt(len(operation_locations))),
    )

    for _ in range(_AFFINITY_PASSES):
        changed = False
        for source in range(partition_count):
            for group_index in tuple(assigned[source]):
                if len(assigned[source]) == 1:
                    continue
                operations = group_operations[group_index]
                if not 2 <= len(operations) <= common_threshold:
                    continue
                candidates = sorted(
                    {
                        partition
                        for operation in sorted(operations)
                        for partition in operation_locations[operation]
                        if partition != source
                    }
                )
                best: tuple[int, float, int] | None = None
                for target in candidates:
                    new_source_weight = (
                        source_weights[source] - group_weights[group_index]
                    )
                    new_target_weight = (
                        source_weights[target] + group_weights[group_index]
                    )
                    new_target_shapes = (
                        shape_counts[target] + group_shape_counts[group_index]
                    )
                    if (
                        new_source_weight < source_floors[source]
                        or new_target_weight > source_ceilings[target]
                        or new_target_shapes > shape_ceilings[target]
                    ):
                        continue
                    delta = _operation_touch_delta(
                        operations,
                        operation_counts[source],
                        operation_counts[target],
                    )
                    if delta >= 0:
                        continue
                    balance = abs(new_source_weight - ideal_source_weight) + abs(
                        new_target_weight - ideal_source_weight
                    )
                    candidate = (delta, balance, target)
                    if best is None or candidate < best:
                        best = candidate
                if best is None:
                    continue

                target = best[2]
                assigned[source].remove(group_index)
                assigned[target].append(group_index)
                shape_counts[source] -= group_shape_counts[group_index]
                shape_counts[target] += group_shape_counts[group_index]
                source_weights[source] -= group_weights[group_index]
                source_weights[target] += group_weights[group_index]
                _update_operation_counts(
                    source,
                    operations,
                    operation_counts,
                    operation_locations,
                    -1,
                )
                _update_operation_counts(
                    target,
                    operations,
                    operation_counts,
                    operation_locations,
                    1,
                )
                changed = True
        if not changed:
            break

    return [sorted(partition) for partition in assigned]


def _operation_touch_delta(
    operations: Collection[_model.ShapeId],
    source_counts: Mapping[_model.ShapeId, int],
    target_counts: Mapping[_model.ShapeId, int],
) -> int:
    delta = 0
    for operation in sorted(operations):
        if target_counts.get(operation, 0) == 0:
            delta += 1
        if source_counts.get(operation, 0) == 1:
            delta -= 1
    return delta


def _update_operation_counts(
    partition: int,
    operations: Collection[_model.ShapeId],
    operation_counts: list[dict[_model.ShapeId, int]],
    operation_locations: Mapping[_model.ShapeId, set[int]],
    adjustment: int,
) -> None:
    counts = operation_counts[partition]
    for operation in sorted(operations):
        current = counts.get(operation, 0)
        updated = current + adjustment
        if updated == 0:
            counts.pop(operation)
        else:
            counts[operation] = updated
        locations = operation_locations[operation]
        if current == 0 and updated == 1:
            locations.add(partition)
        elif current == 1 and updated == 0:
            locations.remove(partition)


def _schema_group_weight(plan: SchemaPlan, group: tuple[_model.Shape, ...]) -> int:
    declarations = sum(
        len(plan.strings[value]) + len(repr(value)) + 4
        for value in _schema_strings(plan, group)
    )
    return declarations + sum(_schema_shape_weight(plan, shape) for shape in group)


def _schema_shape_weight(plan: SchemaPlan, shape: _model.Shape) -> int:
    """Estimate compact-schema source bytes without rendering shapes twice."""
    weight = (
        60
        + len(shape.id.namespace)
        + 2 * len(shape.id.name)
        + _source_size(_trait_parts(plan, plan.traits[shape.id]))
        + sum(
            40
            + 2 * len(member.name)
            + len(plan.names.get(member.target, member.target.name))
            + _source_size(_trait_parts(plan, plan.traits[member.id]))
            for member in shape.members.values()
        )
    )
    if isinstance(shape, _model.OperationShape):
        weight += sum(
            len(plan.names.get(target, target.name))
            for target in (shape.input, shape.output, *shape.errors)
        )
    return weight


def _source_size(parts: Collection[_SourcePart]) -> int:
    return sum(
        len(part.name if isinstance(part, _symbols.TypeReference) else part)
        for part in parts
    )


def _intern_traits(strings: _StringStore, traits: _TraitPlan) -> None:
    if isinstance(traits, int):
        return
    for trait_id, value in traits.items():
        strings.intern(str(trait_id))
        if isinstance(value, str):
            strings.intern(value)


def _schema_strings(
    plan: SchemaPlan, shapes: Collection[_model.Shape]
) -> frozenset[str]:
    values: set[str] = set()
    for shape in shapes:
        values.update((shape.id.namespace, shape.id.name))
        _collect_trait_strings(values, plan.traits[shape.id])
        for member in shape.members.values():
            values.add(member.name)
            _collect_trait_strings(values, plan.traits[member.id])
    return frozenset(values)


def _collect_trait_strings(values: set[str], traits: _TraitPlan) -> None:
    if isinstance(traits, int):
        return
    for trait_id, value in traits.items():
        values.add(str(trait_id))
        if isinstance(value, str):
            values.add(value)


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
