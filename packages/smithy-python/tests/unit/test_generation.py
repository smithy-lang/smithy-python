# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

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
from smithy_python.selection import Selector, select_shapes, select_type_shapes
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
    assert settings.schema_partition_size == 250
    assert settings.stub_partition_size == 250


def test_types_settings_require_positive_partition_size() -> None:
    with pytest.raises(ValueError, match="Partition sizes must be positive"):
        TypesSettings("example", "1.0.0", None, schema_partition_size=0)
    with pytest.raises(ValueError, match="Partition sizes must be positive"):
        TypesSettings("example", "1.0.0", None, stub_partition_size=0)


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
        plan=GenerationPlan.from_selection(model, selection, symbols),
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


def test_generation_plan_orders_schemas_and_plans_names() -> None:
    model = load_model(
        {
            "smithy": "2.0",
            "shapes": {
                "example#Leaf": {"type": "string"},
                "example#CycleB": {
                    "type": "structure",
                    "members": {"a": {"target": "example#CycleA"}},
                },
                "example#CycleA": {
                    "type": "structure",
                    "members": {"b": {"target": "example#CycleB"}},
                },
                "example#Root": {
                    "type": "structure",
                    "members": {"leaf": {"target": "example#Leaf"}},
                },
                "example#Choice": {
                    "type": "union",
                    "members": {"foo": {"target": "example#Leaf"}},
                },
                "example#ChoiceFoo": {"type": "structure"},
                "example#ChoiceUnknown": {"type": "structure"},
            },
        }
    )
    selection = select_type_shapes(model)
    symbols = SymbolProvider(model, selection, package="example")
    plan = GenerationPlan.from_selection(model, selection, symbols)

    assert tuple(map(str, (shape.id for shape in plan.schemas.shapes))) == (
        "example#Leaf",
        "example#Root",
        "example#Choice",
        "example#ChoiceFoo",
        "example#ChoiceUnknown",
        "example#CycleB",
        "example#CycleA",
    )
    assert plan.schemas.names[model.get_shape("example#Choice").id] == "CHOICE"
    assert (
        plan.models.union_variant_names[model.get_shape("example#Choice$foo").id]
        == "Choice_Foo"
    )
    assert (
        plan.models.union_unknown_names[model.get_shape("example#Choice").id]
        == "Choice_Unknown"
    )
    assert plan.schemas.strings["example"] == "n0"


def test_generation_plan_includes_streaming_union_models() -> None:
    model = load_model(
        {
            "smithy": "2.0",
            "shapes": {
                "example#Events": {
                    "type": "union",
                    "traits": {"smithy.api#streaming": {}},
                    "members": {"message": {"target": "smithy.api#String"}},
                }
            },
        }
    )
    selection = select_type_shapes(model)
    symbols = SymbolProvider(model, selection, package="example")
    plan = GenerationPlan.from_selection(model, selection, symbols)
    shape_id = model.get_shape("example#Events").id
    assert plan.schemas.names[shape_id] == "EVENTS"
    assert plan.models.declaration_names[shape_id] == "Events"
    assert (
        plan.models.union_variant_names[model.get_shape("example#Events$message").id]
        == "EventsMessage"
    )
    assert plan.models.union_unknown_names[shape_id] == "EventsUnknown"
