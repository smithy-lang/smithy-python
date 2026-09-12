# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any

import pytest
from smithy_python.exceptions import CodegenError, InvalidInvocationError
from smithy_python.model import Model, ShapeID
from smithy_python.selection import resolve_service, select_generated_shapes

WEATHER = ShapeID.parse("example.weather#Weather")


def _names(model: Model) -> list[str]:
    return [shape.id.name for shape in select_generated_shapes(model)]


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


class TestSelectGeneratedShapes:
    def test_selects_every_data_shape_in_model_order(self, model: Model) -> None:
        assert _names(model) == [
            "CityId",
            "Coordinates",
            "Tags",
            "GetCityInput",
            "GetCityOutput",
            "NoSuchCity",
            "Unused",
        ]

    def test_skips_traits_mixins_and_prelude(
        self, model_document: dict[str, Any]
    ) -> None:
        shapes = model_document["shapes"]
        shapes["example.weather#myTrait"] = {
            "type": "structure",
            "traits": {"smithy.api#trait": {}},
        }
        shapes["example.weather#Auditable"] = {
            "type": "structure",
            "traits": {"smithy.api#mixin": {}},
            "members": {"createdAt": {"target": "smithy.api#Timestamp"}},
        }
        shapes["smithy.api#String"] = {"type": "string"}
        names = _names(Model.from_dict(model_document))
        assert "myTrait" not in names
        assert "Auditable" not in names
        assert "String" not in names

    def test_private_shapes_are_generated_only_when_referenced(
        self, model_document: dict[str, Any]
    ) -> None:
        shapes = model_document["shapes"]
        shapes["example.weather#Hidden"] = {
            "type": "structure",
            "traits": {"smithy.api#private": {}},
        }
        shapes["example.weather#Nested"] = {
            "type": "structure",
            "traits": {"smithy.api#private": {}},
        }
        shapes["example.weather#Used"] = {
            "type": "structure",
            "traits": {"smithy.api#private": {}},
            "members": {"nested": {"target": "example.weather#Nested"}},
        }
        shapes["example.weather#Coordinates"]["members"]["used"] = {
            "target": "example.weather#Used"
        }
        names = _names(Model.from_dict(model_document))
        assert "Used" in names
        assert "Nested" in names
        assert "Hidden" not in names

    def test_private_shapes_referenced_by_operations_are_generated(
        self, model_document: dict[str, Any]
    ) -> None:
        shapes = model_document["shapes"]
        shapes["example.weather#NoSuchCity"]["traits"]["smithy.api#private"] = {}
        assert "NoSuchCity" in _names(Model.from_dict(model_document))

    def test_case_insensitive_name_conflicts_are_an_error(
        self, model_document: dict[str, Any]
    ) -> None:
        model_document["shapes"]["example.other#coordinates"] = {"type": "string"}
        with pytest.raises(CodegenError) as info:
            select_generated_shapes(Model.from_dict(model_document))
        message = str(info.value)
        assert "renameShapes" in message
        assert "example.weather#Coordinates, example.other#coordinates" in message

    def test_conflicts_with_skipped_shapes_are_ignored(
        self, model_document: dict[str, Any]
    ) -> None:
        model_document["shapes"]["example.other#Coordinates"] = {
            "type": "structure",
            "traits": {"smithy.api#private": {}},
        }
        assert "Coordinates" in _names(Model.from_dict(model_document))
