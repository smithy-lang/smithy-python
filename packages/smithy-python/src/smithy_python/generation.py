# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Shared settings and state for artifact generators."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from .dependencies import DependencySet
from .files import FileManifest
from .model import Model, ShapeId
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

    @classmethod
    def from_selection(cls, selection: Selection) -> GenerationPlan:
        """Create the foundational plan in stable selection order."""
        return cls(tuple(shape.id for shape in selection.shapes))


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
