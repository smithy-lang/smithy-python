# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import pytest
from smithy_python import ConnectedShapeFilter, Model, ModelError, ShapeID, ShapeType


def test_parser_preserves_shape_member_and_trait_order(model: Model) -> None:
    assert [shape.id.name for shape in model][:3] == ["CityId", "Coordinates", "Tags"]
    coordinates = model.expect("example.weather#Coordinates")
    assert [member.name for member in coordinates.members] == ["latitude", "longitude"]
    assert coordinates.type is ShapeType.STRUCTURE
    with pytest.raises(TypeError):
        coordinates.traits["example#trait"] = {}  # type: ignore[index]


def test_parser_resolves_prelude_without_inserting_it(model: Model) -> None:
    assert model.expect("smithy.api#String").type is ShapeType.STRING
    assert all(shape.id.namespace != "smithy.api" for shape in model)


def test_connected_filter_selects_service_closure_in_model_order(model: Model) -> None:
    selected = ConnectedShapeFilter((ShapeID.parse("example.weather#Weather"),)).select(
        model
    )
    assert {shape.id.name for shape in selected} == {
        "CityId",
        "Coordinates",
        "Tags",
        "GetCityInput",
        "GetCityOutput",
        "NoSuchCity",
        "GetCity",
        "Weather",
    }
    assert "Unused" not in {shape.id.name for shape in selected}


def test_parser_reports_invalid_references(model_document: dict[str, object]) -> None:
    shapes = model_document["shapes"]
    assert isinstance(shapes, dict)
    shapes["example#Bad"] = {"type": "list", "member": {}}
    with pytest.raises(ModelError, match="shape target"):
        Model.from_dict(model_document)
