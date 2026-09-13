# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any

import pytest
from smithy_python.exceptions import CodegenError, InvalidInvocationError
from smithy_python.model import Model, Shape, ShapeID
from smithy_python.selection import resolve_service, select_generated_shapes

WEATHER = ShapeID.parse("example.weather#Weather")


def _service(model: Model) -> Shape:
    service = resolve_service(model, None, required=True)
    assert service is not None
    return service


def _names(shapes: tuple[Shape, ...]) -> list[str]:
    return [shape.id.name for shape in shapes]


class TestResolveService:
    def test_single_service_is_detected(self, model: Model) -> None:
        for required in (True, False):
            service = resolve_service(model, None, required=required)
            assert service is not None and service.id == WEATHER

    def test_explicit_service_is_used(self, model: Model) -> None:
        service = resolve_service(model, WEATHER, required=True)
        assert service is not None and service.id == WEATHER

    def test_explicit_service_must_exist(self, model: Model) -> None:
        with pytest.raises(InvalidInvocationError, match="Service not found"):
            resolve_service(model, ShapeID.parse("example#Nope"), required=True)

    def test_explicit_service_must_be_a_service(self, model: Model) -> None:
        with pytest.raises(InvalidInvocationError, match="found structure"):
            resolve_service(
                model, ShapeID.parse("example.weather#Coordinates"), required=True
            )

    def test_multiple_services_require_a_selection(
        self, model_document: dict[str, Any]
    ) -> None:
        model_document["shapes"]["example.other#Other"] = {
            "type": "service",
            "version": "1",
        }
        model = Model.from_dict(model_document)

        with pytest.raises(InvalidInvocationError) as info:
            resolve_service(model, None, required=False)
        assert "example.weather#Weather, example.other#Other" in str(info.value)

        service = resolve_service(model, WEATHER, required=True)
        assert service is not None and service.id == WEATHER

    def test_no_service_is_allowed_only_when_optional(self) -> None:
        model = Model.from_dict({"smithy": "2.0"})
        assert resolve_service(model, None, required=False) is None
        with pytest.raises(InvalidInvocationError, match="does not contain a service"):
            resolve_service(model, None, required=True)

    def test_mixin_services_are_not_candidates(
        self, model_document: dict[str, Any]
    ) -> None:
        model_document["shapes"]["example.weather#Base"] = {
            "type": "service",
            "version": "1",
            "traits": {"smithy.api#mixin": {}},
        }
        model_document["shapes"]["example.weather#Weather"]["mixins"] = [
            {"target": "example.weather#Base"}
        ]
        model = Model.from_dict(model_document)

        service = resolve_service(model, None, required=True)
        assert service is not None and service.id == WEATHER

        with pytest.raises(InvalidInvocationError, match="mixin service"):
            resolve_service(model, ShapeID.parse("example.weather#Base"), required=True)


class TestSelectWithService:
    def test_selects_the_service_closure_in_model_order(self, model: Model) -> None:
        selection = select_generated_shapes(model, _service(model))
        assert _names(selection.shapes) == [
            "CityId",
            "Coordinates",
            "Tags",
            "GetCityInput",
            "GetCityOutput",
            "NoSuchCity",
        ]
        assert _names(selection.excluded) == ["Unused"]

    def test_closure_follows_resources_and_service_errors(
        self, model_document: dict[str, Any]
    ) -> None:
        shapes = model_document["shapes"]
        shapes["example.weather#Throttled"] = {
            "type": "structure",
            "traits": {"smithy.api#error": "client"},
        }
        shapes["example.weather#Weather"]["errors"] = [
            {"target": "example.weather#Throttled"}
        ]
        shapes["example.weather#Forecast"] = {"type": "structure"}
        shapes["example.weather#City"] = {
            "type": "resource",
            "identifiers": {"cityId": {"target": "example.weather#CityId"}},
            "properties": {"forecast": {"target": "example.weather#Forecast"}},
        }
        shapes["example.weather#Weather"]["resources"] = [
            {"target": "example.weather#City"}
        ]
        model = Model.from_dict(model_document)

        names = _names(select_generated_shapes(model, _service(model)).shapes)
        assert "Throttled" in names
        assert "Forecast" in names
        assert "City" not in names

    def test_excludes_traits_mixins_and_prelude_even_when_connected(
        self, model_document: dict[str, Any]
    ) -> None:
        shapes = model_document["shapes"]
        shapes["example.weather#Auditable"] = {
            "type": "structure",
            "traits": {"smithy.api#mixin": {}},
            "members": {"createdAt": {"target": "smithy.api#Timestamp"}},
        }
        shapes["example.weather#Coordinates"]["mixins"] = [
            {"target": "example.weather#Auditable"}
        ]
        shapes["example.weather#myTrait"] = {
            "type": "structure",
            "traits": {"smithy.api#trait": {}},
        }
        shapes["smithy.api#String"] = {"type": "string"}
        model = Model.from_dict(model_document)

        selection = select_generated_shapes(model, _service(model))
        all_names = _names(selection.shapes) + _names(selection.excluded)
        assert "Auditable" not in all_names
        assert "myTrait" not in all_names
        assert "String" not in all_names

    def test_conflicting_names_outside_the_closure_are_harmless(
        self, model_document: dict[str, Any]
    ) -> None:
        model_document["shapes"]["example.other#coordinates"] = {"type": "string"}
        model = Model.from_dict(model_document)
        selection = select_generated_shapes(model, _service(model))
        assert "Coordinates" in _names(selection.shapes)
        assert "coordinates" in _names(selection.excluded)


class TestSelectWithoutService:
    def test_selects_every_data_shape_in_model_order(
        self, model_document: dict[str, Any]
    ) -> None:
        del model_document["shapes"]["example.weather#Weather"]
        model = Model.from_dict(model_document)
        selection = select_generated_shapes(model, None)
        assert _names(selection.shapes) == [
            "CityId",
            "Coordinates",
            "Tags",
            "GetCityInput",
            "GetCityOutput",
            "NoSuchCity",
            "Unused",
        ]
        assert selection.excluded == ()

    def test_case_insensitive_name_conflicts_are_an_error(
        self, model_document: dict[str, Any]
    ) -> None:
        model_document["shapes"]["example.other#coordinates"] = {"type": "string"}
        model = Model.from_dict(model_document)
        with pytest.raises(CodegenError) as info:
            select_generated_shapes(model, None)
        message = str(info.value)
        assert "renameShapes" in message
        assert "example.weather#Coordinates, example.other#coordinates" in message
