# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
from collections.abc import Mapping
from io import BytesIO
from typing import Any, BinaryIO, Protocol

import pytest
from smithy_python.cli import main
from smithy_python.model import Model


@pytest.fixture
def model_document() -> dict[str, Any]:
    """A small weather service model in JSON AST form."""
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


@pytest.fixture
def model_json(model_document: dict[str, Any]) -> bytes:
    return json.dumps(model_document).encode()


class CliRunner(Protocol):
    """Runs the CLI and reports its exit code with what it wrote to stderr."""

    def __call__(
        self,
        *argv: str,
        environ: Mapping[str, str] | None = None,
        stdin: bytes | BinaryIO | None = None,
    ) -> tuple[int, str]: ...


@pytest.fixture
def run_cli(capsys: pytest.CaptureFixture[str]) -> CliRunner:
    """Run the CLI with an empty environment unless one is given."""

    def run(
        *argv: str,
        environ: Mapping[str, str] | None = None,
        stdin: bytes | BinaryIO | None = None,
    ) -> tuple[int, str]:
        stream = BytesIO(stdin) if isinstance(stdin, bytes) else stdin
        exit_code = main(argv, environ={} if environ is None else environ, stdin=stream)
        return exit_code, capsys.readouterr().err

    return run
