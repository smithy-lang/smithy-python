# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import asyncio
import importlib
import py_compile
import runpy
import sys
from collections.abc import Callable, Coroutine
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

from smithy_python import (
    ArtifactType,
    GeneratorSettings,
    Model,
    PluginEnvironment,
    PluginRegistry,
    PythonCodeGenerator,
    ShapeID,
)
from smithy_python.integrations.aws import AwsPlugin
from smithy_python.integrations.rest_json import RestJsonPlugin


def _settings(mode: ArtifactType) -> GeneratorSettings:
    return GeneratorSettings(
        artifact_type=mode,
        service=ShapeID.parse("example.weather#Weather")
        if mode is ArtifactType.CLIENT
        else None,
        module_name="weather",
        module_version="1.2.3",
        format_code=False,
    )


def _generate(model: Model, output: Path, mode: ArtifactType) -> None:
    PythonCodeGenerator(PluginRegistry((RestJsonPlugin(), AwsPlugin()))).generate(
        model,
        _settings(mode),
        output_dir=output,
        environment=PluginEnvironment(plugin_dir=output),
    )


def test_client_generation_is_complete_and_compiles(
    model: Model, tmp_path: Path
) -> None:
    _generate(model, tmp_path, ArtifactType.CLIENT)
    module = tmp_path / "src" / "weather"
    assert (module / "client.py").is_file()
    assert (module / "config.py").is_file()
    schemas = (module / "_private" / "schemas.py").read_text()
    assert "Complete member links after every schema exists" in schemas
    models = (module / "models.py").read_text()
    assert "class GetCityInput" in models
    assert "city_id: str" in models
    assert "tags: list[str] | None = None" in models
    assert "GET_CITY = APIOperation(" in models
    assert "example.unused" not in schemas
    for path in tmp_path.rglob("*.py"):
        py_compile.compile(str(path), doraise=True)
    import_paths = [
        str(tmp_path / "src"),
        str(Path(__file__).parents[2] / "smithy-core" / "src"),
    ]
    sys.path[:0] = import_paths
    try:
        generated = importlib.import_module("weather.models")
        assert generated.GetCityInput(city_id="New York").city_id == "New York"
        generated_config = importlib.import_module("weather.config")
        config = generated_config.Config()
        assert config.protocol is not None
        generated_client = importlib.import_module("weather.client")
        assert generated_client.WeatherClient(config=config) is not None
    finally:
        for name in tuple(sys.modules):
            if name == "weather" or name.startswith("weather."):
                del sys.modules[name]
        del sys.path[: len(import_paths)]


def test_types_generation_omits_client_and_io_shapes(
    model: Model, tmp_path: Path
) -> None:
    _generate(model, tmp_path, ArtifactType.TYPES)
    module = tmp_path / "src" / "weather"
    assert not (module / "client.py").exists()
    assert not (module / "config.py").exists()
    models = (module / "models.py").read_text()
    assert "class Coordinates" in models
    assert "class GetCityInput" not in models
    assert "class GetCityOutput" not in models
    assert "Unused" in (module / "_private" / "schemas.py").read_text()


def test_generated_metadata_contains_runtime_dependencies(
    model: Model, tmp_path: Path
) -> None:
    _generate(model, tmp_path, ArtifactType.CLIENT)
    pyproject = (tmp_path / "pyproject.toml").read_text()
    assert '"smithy-aws-core[json]~=0.7.0"' in pyproject
    assert '"smithy-http[aiohttp]~=0.4.0"' in pyproject


def test_generated_package_passes_opt_in_formatters_and_linters(
    model: Model, tmp_path: Path
) -> None:
    settings = replace(_settings(ArtifactType.CLIENT), format_code=True, lint_code=True)
    PythonCodeGenerator(PluginRegistry((RestJsonPlugin(), AwsPlugin()))).generate(
        model,
        settings,
        output_dir=tmp_path,
        environment=PluginEnvironment(plugin_dir=tmp_path),
    )


def test_generates_modeled_protocol_test_cases(
    model_document: dict[str, object], tmp_path: Path
) -> None:
    shapes = model_document["shapes"]
    assert isinstance(shapes, dict)
    typed_shapes = cast(dict[str, object], shapes)
    operation = typed_shapes["example.weather#GetCity"]
    assert isinstance(operation, dict)
    typed_operation = cast(dict[str, object], operation)
    traits = typed_operation["traits"]
    assert isinstance(traits, dict)
    typed_traits = cast(dict[str, object], traits)
    typed_traits["smithy.test#httpRequestTests"] = [
        {
            "id": "GetCityRequest",
            "protocol": "aws.protocols#restJson1",
            "method": "GET",
            "uri": "/city/New%20York",
            "params": {"cityId": "New York"},
        }
    ]
    typed_traits["smithy.test#httpResponseTests"] = [
        {
            "id": "GetCityResponse",
            "protocol": "aws.protocols#restJson1",
            "code": 200,
            "headers": {"content-type": "application/json"},
            "body": '{"coordinates":{"latitude":40.7,"longitude":-74.0},"tags":["coastal"]}',
            "bodyMediaType": "application/json",
            "params": {
                "coordinates": {"latitude": 40.7, "longitude": -74.0},
                "tags": ["coastal"],
            },
        }
    ]
    error_shape = typed_shapes["example.weather#NoSuchCity"]
    assert isinstance(error_shape, dict)
    error_traits = cast(dict[str, object], error_shape["traits"])
    error_traits["smithy.test#httpResponseTests"] = [
        {
            "id": "NoSuchCityResponse",
            "protocol": "aws.protocols#restJson1",
            "code": 404,
            "headers": {
                "content-type": "application/json",
                "x-amzn-errortype": "NoSuchCity",
            },
            "body": '{"message":"not found"}',
            "bodyMediaType": "application/json",
            "params": {"message": "not found"},
        }
    ]
    _generate(Model.from_dict(model_document), tmp_path, ArtifactType.CLIENT)
    generated_test = (tmp_path / "tests" / "test_protocol.py").read_text()
    assert "test_get_city_request_request_get_city" in generated_test
    assert "protocol.serialize_request(" in generated_test
    assert "assert request.method == 'GET'" in generated_test
    assert "pytest>=9,<10" in (tmp_path / "pyproject.toml").read_text()
    sys.path.insert(0, str(tmp_path / "src"))
    try:
        namespace = runpy.run_path(str(tmp_path / "tests" / "test_protocol.py"))
        generated_cases = cast(
            list[Callable[[], Coroutine[Any, Any, None]]],
            [
                value
                for name, value in namespace.items()
                if name.startswith("test_") and callable(value)
            ],
        )
        assert len(generated_cases) == 3
        for generated_case in generated_cases:
            asyncio.run(generated_case())
    finally:
        for name in tuple(sys.modules):
            if name == "weather" or name.startswith("weather."):
                del sys.modules[name]
        del sys.path[0]


def test_aws_customizations_are_python_plugins(
    model_document: dict[str, object], tmp_path: Path
) -> None:
    shapes = model_document["shapes"]
    assert isinstance(shapes, dict)
    typed_shapes = cast(dict[str, object], shapes)
    service = typed_shapes["example.weather#Weather"]
    assert isinstance(service, dict)
    typed_service = cast(dict[str, object], service)
    traits = typed_service["traits"]
    assert isinstance(traits, dict)
    typed_traits = cast(dict[str, object], traits)
    typed_traits.update(
        {
            "aws.api#service": {"sdkId": "Weather", "endpointPrefix": "weather"},
            "aws.auth#sigv4": {"name": "weather"},
            "smithy.api#auth": ["aws.auth#sigv4"],
        }
    )
    _generate(Model.from_dict(model_document), tmp_path, ArtifactType.CLIENT)
    module = tmp_path / "src" / "weather"
    user_agent = (module / "user_agent.py").read_text()
    assert "UserAgentInterceptor(" in user_agent
    assert "service_id='Weather'" in user_agent
    config = (module / "config.py").read_text()
    assert "SigV4AuthScheme(service='weather')" in config
    assert "StandardRegionalEndpointsResolver(endpoint_prefix='weather')" in config


def test_nullability_defaults_and_recursive_schemas(
    model_document: dict[str, object], tmp_path: Path
) -> None:
    shapes = model_document["shapes"]
    assert isinstance(shapes, dict)
    shapes["example.weather#Node"] = {
        "type": "structure",
        "members": {
            "name": {
                "target": "smithy.api#String",
                "traits": {"smithy.api#required": {}},
            },
            "next": {"target": "example.weather#Node"},
            "enabled": {
                "target": "smithy.api#Boolean",
                "traits": {"smithy.api#default": False},
            },
            "labels": {
                "target": "example.weather#Tags",
                "traits": {"smithy.api#default": []},
            },
            "nullableDefault": {
                "target": "smithy.api#String",
                "traits": {"smithy.api#default": None},
            },
            "clientOptional": {
                "target": "smithy.api#Boolean",
                "traits": {
                    "smithy.api#clientOptional": {},
                    "smithy.api#default": True,
                },
            },
        },
    }
    _generate(Model.from_dict(model_document), tmp_path, ArtifactType.TYPES)
    models = (tmp_path / "src" / "weather" / "models.py").read_text()
    assert "name: str" in models
    assert "next: Node | None = None" in models
    assert "enabled: bool = False" in models
    assert "labels: list[str] = field(default_factory=lambda: [])" in models
    assert "nullable_default: str | None = None" in models
    assert "client_optional: bool | None = None" in models
    assert "if self.nullable_default is not None:" in models
    assert "if self.client_optional is not None:" in models
    schemas = (tmp_path / "src" / "weather" / "_private" / "schemas.py").read_text()
    assert "NODE.members['next'] = Schema.member(" in schemas
    assert "target=NODE" in schemas
