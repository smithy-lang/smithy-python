# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import json

import pytest
from smithy_python.dependencies import DependencySet
from smithy_python.files import FileManifest
from smithy_python.generation import (
    ArtifactSettings,
    GenerationContext,
    GenerationPlan,
    TypesSettings,
)
from smithy_python.model import load_model
from smithy_python.selection import Selector, select_shapes
from smithy_python.symbols import SymbolProvider


def test_artifact_settings_are_immutable_values() -> None:
    settings = ArtifactSettings(
        package="example.types",
        package_version="1.2.3",
        package_description=None,
    )
    assert settings.package == "example.types"
    assert settings.package_version == "1.2.3"


def test_types_settings_default_to_identity_selection() -> None:
    settings = TypesSettings(
        package="example.types",
        package_version="1.2.3",
        package_description="Example types",
    )
    assert settings.selector == Selector.identity()
    assert not settings.generate_inputs_and_outputs


def test_generation_plan_preserves_selection_order() -> None:
    model = load_model(
        json.dumps(
            {
                "smithy": "2.0",
                "shapes": {
                    "example#Second": {"type": "string"},
                    "example#First": {"type": "integer"},
                },
            }
        )
    )
    plan = GenerationPlan.from_selection(select_shapes(model))
    assert tuple(map(str, plan.selected_shape_ids)) == (
        "example#Second",
        "example#First",
    )


def test_generation_context_shares_manifest_dependencies() -> None:
    model = load_model('{"smithy": "2.0"}')
    selection = select_shapes(model)
    settings = TypesSettings("example", "1.0.0", None)
    symbols = SymbolProvider(model, selection, package=settings.package)
    dependencies = DependencySet()
    context = GenerationContext(
        model=model,
        selection=selection,
        settings=settings,
        symbols=symbols,
        plan=GenerationPlan.from_selection(selection),
        dependencies=dependencies,
        files=FileManifest(dependencies),
    )
    assert context.files.dependencies is context.dependencies

    with pytest.raises(ValueError, match="must be shared"):
        GenerationContext(
            model=model,
            selection=selection,
            settings=settings,
            symbols=symbols,
            plan=context.plan,
            dependencies=dependencies,
            files=FileManifest(),
        )
