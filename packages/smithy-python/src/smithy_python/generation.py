# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Shared settings and state for artifact generators."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Protocol

from .dependencies import DependencySet
from .files import FileManifest
from .model import Model, Node, Shape, ShapeId, ShapeType
from .selection import Selection, Selector
from .symbols import SymbolProvider


@dataclass(frozen=True, slots=True)
class ArtifactSettings:
    """Settings shared by generated artifacts."""

    package: str
    package_version: str
    package_description: str | None


@dataclass(frozen=True, slots=True)
class TypesSettings(ArtifactSettings):
    """Settings for a standalone types package."""

    selector: Selector = field(default_factory=Selector.identity)
    generate_inputs_and_outputs: bool = False


@dataclass(frozen=True, slots=True)
class GenerationPlan:
    """Derived semantic data shared by artifact emitters."""

    selected_shape_ids: tuple[ShapeId, ...]
    shapes_by_type: Mapping[ShapeType, tuple[Shape, ...]]
    schema_shapes: tuple[Shape, ...]
    recursive_schema_shapes: tuple[Shape, ...]
    schema_names: Mapping[ShapeId, str]
    schema_strings: Mapping[str, str]
    declaration_names: Mapping[ShapeId, str]
    model_renames: Mapping[str, str]
    union_variant_names: Mapping[ShapeId, str]
    union_unknown_names: Mapping[ShapeId, str]

    @classmethod
    def from_selection(
        cls, selection: Selection, symbols: SymbolProvider | None = None
    ) -> GenerationPlan:
        """Compute reusable indexes in stable selection order."""
        selected = selection.shapes
        grouped: dict[ShapeType, list[Shape]] = {}
        for shape in selected:
            grouped.setdefault(shape.type, []).append(shape)

        schema_shapes, recursive_schema_shapes = _schema_order(selected)
        schema_names = {
            shape.id: (
                symbols.schema_name(shape.id)
                if symbols is not None
                else _constant_name(_selected_name(selection, shape))
            )
            for shape in selected
        }
        declaration_names: dict[ShapeId, str] = {}
        model_renames: dict[str, str] = {}
        union_variant_names: dict[ShapeId, str] = {}
        union_unknown_names: dict[ShapeId, str] = {}
        for shape in selected:
            if shape.type not in {
                ShapeType.STRUCTURE,
                ShapeType.UNION,
                ShapeType.ENUM,
                ShapeType.INT_ENUM,
            }:
                continue
            declaration = (
                symbols.declaration_name(shape.id)
                if symbols is not None
                else _declaration_name(_selected_name(selection, shape))
            )
            declaration_names[shape.id] = declaration
            if declaration != shape.id.name:
                model_renames[declaration] = schema_names[shape.id]
            if shape.type is ShapeType.UNION:
                union_unknown_names[shape.id] = (
                    symbols.union_unknown_name(shape.id)
                    if symbols is not None
                    else declaration + "Unknown"
                )
                union_variant_names.update(
                    {
                        member.id: (
                            symbols.union_variant_name(member.id)
                            if symbols is not None
                            else declaration + member.name[:1].upper() + member.name[1:]
                        )
                        for member in shape.members.values()
                    }
                )

        return cls(
            selected_shape_ids=tuple(shape.id for shape in selected),
            shapes_by_type=MappingProxyType(
                {kind: tuple(shapes) for kind, shapes in grouped.items()}
            ),
            schema_shapes=schema_shapes,
            recursive_schema_shapes=recursive_schema_shapes,
            schema_names=MappingProxyType(schema_names),
            schema_strings=MappingProxyType(_schema_strings(selected)),
            declaration_names=MappingProxyType(declaration_names),
            model_renames=MappingProxyType(model_renames),
            union_variant_names=MappingProxyType(union_variant_names),
            union_unknown_names=MappingProxyType(union_unknown_names),
        )


@dataclass(frozen=True, slots=True)
class GenerationContext[SettingsT: ArtifactSettings]:
    """State shared by one artifact generation."""

    model: Model
    selection: Selection
    settings: SettingsT
    symbols: SymbolProvider
    plan: GenerationPlan
    dependencies: DependencySet
    files: FileManifest

    def __post_init__(self) -> None:
        if self.files.dependencies is not self.dependencies:
            raise ValueError(
                "GenerationContext dependencies must be shared with FileManifest"
            )


class ArtifactGenerator[SettingsT: ArtifactSettings](Protocol):
    """Generate one artifact into the context's file manifest."""

    def generate(self, context: GenerationContext[SettingsT]) -> None:
        """Register every generated file and dependency."""
        ...


def _schema_order(
    shapes: tuple[Shape, ...],
) -> tuple[tuple[Shape, ...], tuple[Shape, ...]]:
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

    ordered: list[Shape] = []
    visited.clear()
    for root in graph:
        if root in recursive or root in visited:
            continue
        visited.add(root)
        pending = [(root, 0)]
        while pending:
            current, index = pending[-1]
            targets = graph[current]
            while index < len(targets) and targets[index] in recursive:
                index += 1
            if index == len(targets):
                ordered.append(by_id[current])
                pending.pop()
                continue
            target = targets[index]
            pending[-1] = (current, index + 1)
            if target not in visited:
                visited.add(target)
                pending.append((target, 0))

    return (
        tuple(ordered),
        tuple(shape for shape in shapes if shape.id in recursive),
    )


def _schema_strings(shapes: tuple[Shape, ...]) -> dict[str, str]:
    strings = _StringStore()
    for shape in shapes:
        strings.intern(shape.id.namespace, preferred="n")
        strings.intern(shape.id.name)
        _intern_traits(strings, shape.traits)
        for member in shape.members.values():
            strings.intern(member.name)
            _intern_traits(strings, member.traits)
    return strings.values


def _selected_name(selection: Selection, shape: Shape) -> str:
    service = selection.service
    return service.rename.get(shape.id, shape.id.name) if service else shape.id.name


def _declaration_name(value: str) -> str:
    return "".join(word[:1].upper() + word[1:] for word in value.split("_"))


def _constant_name(value: str) -> str:
    value = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", value)
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
    return "_".join(word.upper() for word in value.split("_") if word)


def _intern_traits(strings: _StringStore, traits: Mapping[ShapeId, Node]) -> None:
    for trait_id, value in traits.items():
        strings.intern(str(trait_id))
        if isinstance(value, str):
            strings.intern(value)


class _StringStore:
    __slots__ = ("_allocated", "values")

    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self._allocated: set[str] = set()

    def intern(self, value: str, *, preferred: str | None = None) -> str:
        existing = self.values.get(value)
        if existing is not None:
            return existing
        if preferred is not None:
            suffix = 0
            candidate = f"{preferred}{suffix}"
            while candidate in self._allocated:
                suffix += 1
                candidate = f"{preferred}{suffix}"
        else:
            sections = tuple(part for part in re.split(r"[-_\s]", value) if part)
            candidate = "_"
            remaining: list[str] = []
            if len(sections) > 1:
                candidate += "".join(
                    part[0]
                    for part in sections
                    if part[0].isascii() and part[0].isalpha()
                )
            else:
                for char in value:
                    if char.isascii() and char.isalpha():
                        if char.isupper() or candidate == "_":
                            candidate += char
                        else:
                            remaining.append(char)
            if candidate == "_":
                candidate = "_v"
            while candidate in self._allocated:
                candidate += remaining.pop(0) if remaining else "_"
        self._allocated.add(candidate)
        self.values[value] = candidate
        return candidate
