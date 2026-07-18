# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any

import pytest
from smithy_python import Model


@pytest.fixture
def model_document() -> dict[str, Any]:
    return {
        "smithy": "2.0",
        "metadata": {"example": True},
        "shapes": {
            "example.weather#CityId": {
                "type": "string",
                "traits": {"smithy.api#pattern": "^[A-Za-z ]+$"},
            },
            "example.weather#Coordinates": {
                "type": "structure",
                "members": {
                    "latitude": {
                        "target": "smithy.api#Float",
                        "traits": {"smithy.api#required": {}},
                    },
                    "longitude": {
                        "target": "smithy.api#Float",
                        "traits": {"smithy.api#required": {}},
                    },
                },
            },
            "example.weather#Tags": {
                "type": "list",
                "member": {"target": "smithy.api#String"},
            },
            "example.weather#GetCityInput": {
                "type": "structure",
                "traits": {"smithy.api#input": {}},
                "members": {
                    "cityId": {
                        "target": "example.weather#CityId",
                        "traits": {
                            "smithy.api#required": {},
                            "smithy.api#httpLabel": {},
                        },
                    }
                },
            },
            "example.weather#GetCityOutput": {
                "type": "structure",
                "traits": {"smithy.api#output": {}},
                "members": {
                    "coordinates": {
                        "target": "example.weather#Coordinates",
                        "traits": {"smithy.api#required": {}},
                    },
                    "tags": {"target": "example.weather#Tags"},
                },
            },
            "example.weather#NoSuchCity": {
                "type": "structure",
                "traits": {"smithy.api#error": "client"},
                "members": {
                    "message": {"target": "smithy.api#String"},
                },
            },
            "example.weather#GetCity": {
                "type": "operation",
                "input": {"target": "example.weather#GetCityInput"},
                "output": {"target": "example.weather#GetCityOutput"},
                "errors": [{"target": "example.weather#NoSuchCity"}],
                "traits": {
                    "smithy.api#http": {
                        "method": "GET",
                        "uri": "/city/{cityId}",
                        "code": 200,
                    }
                },
            },
            "example.weather#Weather": {
                "type": "service",
                "version": "2026-01-01",
                "operations": [{"target": "example.weather#GetCity"}],
                "traits": {
                    "aws.protocols#restJson1": {},
                    "smithy.api#documentation": "Provides <b>weather</b> forecasts.",
                },
            },
            "example.unused#Unused": {"type": "string"},
        },
    }


@pytest.fixture
def model(model_document: dict[str, Any]) -> Model:
    return Model.from_dict(model_document)
