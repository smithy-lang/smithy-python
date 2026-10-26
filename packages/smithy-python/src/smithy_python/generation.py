# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Shared settings and state for artifact generators."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Protocol

from . import dependencies as _dependencies
from . import files as _files
from . import model as _model
from . import schemas as _schemas
from . import selection as _selection
from . import symbols as _symbols

__all__ = [
    "ArtifactGenerator",
    "ArtifactSettings",
    "GenerationContext",
    "GenerationPlan",
    "ModelPlan",
    "TypesSettings",
]


@dataclass(frozen=True, slots=True)
class ArtifactSettings:
    """Settings shared by generated artifacts."""

    package: str
    package_version: str
    package_description: str | None


@dataclass(frozen=True, slots=True)
class TypesSettings(ArtifactSettings):
    """Settings for a standalone types package."""

    selector: _selection.Selector = field(default_factory=_selection.Selector.identity)
    generate_inputs_and_outputs: bool = False


@dataclass(frozen=True, slots=True)
class ModelPlan:
    """Derived semantic data used to emit lazy model declarations."""

    declaration_names: Mapping[_model.ShapeId, str]
    renames: Mapping[str, str]
    union_variant_names: Mapping[_model.ShapeId, str]
    union_unknown_names: Mapping[_model.ShapeId, str]

    @classmethod
    def from_shapes(
        cls,
        shapes: tuple[_model.Shape, ...],
        symbols: _symbols.SymbolProvider,
        schema_names: Mapping[_model.ShapeId, str],
    ) -> ModelPlan:
        """Plan declaration and union names in stable shape order."""
        declarations: dict[_model.ShapeId, str] = {}
        variants: dict[_model.ShapeId, str] = {}
        unknowns: dict[_model.ShapeId, str] = {}
        for shape in shapes:
            if shape.type not in _model.DECLARATION_TYPES or shape.has_trait(
                "streaming"
            ):
                continue
            declarations[shape.id] = symbols.declaration_name(shape.id)
            if shape.type is _model.ShapeType.UNION:
                for member in shape.members.values():
                    variants[member.id] = symbols.union_variant_name(member.id)
                unknowns[shape.id] = symbols.union_unknown_name(shape.id)

        return cls(
            declaration_names=MappingProxyType(declarations),
            renames=MappingProxyType(
                {
                    declaration: schema_names[shape_id]
                    for shape_id, declaration in declarations.items()
                    if declaration != shape_id.name
                }
            ),
            union_variant_names=MappingProxyType(variants),
            union_unknown_names=MappingProxyType(unknowns),
        )


@dataclass(frozen=True, slots=True)
class GenerationPlan:
    """Derived semantic data shared by artifact emitters."""

    schemas: _schemas.SchemaPlan
    models: ModelPlan

    @classmethod
    def from_selection(
        cls,
        model: _model.Model,
        selection: _selection.Selection,
        symbols: _symbols.SymbolProvider,
    ) -> GenerationPlan:
        """Build focused plans in stable selection order."""
        selected = selection.shapes
        schemas = _schemas.SchemaPlan.from_shapes(model, selected, symbols)
        return cls(
            schemas=schemas,
            models=ModelPlan.from_shapes(selected, symbols, schemas.names),
        )


@dataclass(frozen=True, slots=True)
class GenerationContext[SettingsT: ArtifactSettings]:
    """State shared by one artifact generation."""

    model: _model.Model
    selection: _selection.Selection
    settings: SettingsT
    symbols: _symbols.SymbolProvider
    plan: GenerationPlan
    dependencies: _dependencies.DependencySet
    files: _files.FileManifest

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
