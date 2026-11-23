# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import ast
import asyncio
import importlib
import json
import os
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from smithy_aws_core.config.exceptions import ConfigError
from smithy_cbor import loads
from smithy_core.aio.types import AsyncBytesReader
from smithy_core.exceptions import SmithyIdentityError
from smithy_core.retries import SimpleRetryStrategy
from smithy_http import HTTPResponse, tuples_to_fields
from smithy_http.interfaces import HTTPRequest, HTTPRequestConfiguration
from smithy_python.model import OperationShape, load_model

_ROOT = Path(__file__).resolve().parents[3]
_INPUTS = _ROOT / "scripts/codegen-output-py"
_PROJECTIONS: dict[str, Any] = json.loads(
    (_INPUTS / "client-projections.json").read_text()
)
_CBOR = _PROJECTIONS["rpcv2-cbor-client"]
_SOURCE = _ROOT / "codegen-output-py/rpcv2-cbor-client/src"
_PACKAGE = _CBOR["package"]
_JAVA_CLIENT = _ROOT / "codegen-output/rpcv2-cbor/src/rpcv2cbor/client.py"


@pytest.fixture(scope="module")
def package() -> Iterator[ModuleType]:
    sys.path.insert(0, str(_SOURCE))
    try:
        yield importlib.import_module(_PACKAGE)
    finally:
        sys.path.remove(str(_SOURCE))
        for name in tuple(sys.modules):
            if name == _PACKAGE or name.startswith(_PACKAGE + "."):
                del sys.modules[name]


def _methods(path: Path, class_name: str) -> set[str]:
    tree = ast.parse(path.read_text())
    (cls,) = (
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == class_name
    )
    return {
        node.name
        for node in cls.body
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        and not node.name.startswith("_")
    }


def test_clients_have_a_method_per_operation_like_java() -> None:
    model = load_model(json.loads((_INPUTS / _CBOR["model"]).read_text()))
    operations = sum(1 for _ in model.iter_shapes(OperationShape))
    native = _SOURCE / _PACKAGE
    sync = _methods(native / "client.py", "RpcV2Protocol")
    assert len(sync) == operations == 14
    assert sync == _methods(native / "aio/client.py", "AsyncRpcV2Protocol")
    assert sync == _methods(_JAVA_CLIENT, "RpcV2Protocol")


class _Transport:
    TIMEOUT_EXCEPTIONS = ()

    def __init__(self, body: bytes) -> None:
        self.body = body
        self.requests: list[HTTPRequest] = []

    def __deepcopy__(self, memo: dict[int, Any]) -> _Transport:
        # Clients copy their config, transport included. Keep one recorder.
        return self

    def _respond(self, request: HTTPRequest, body: Any) -> HTTPResponse:
        self.requests.append(request)
        headers = [
            ("Content-Type", "application/cbor"),
            ("smithy-protocol", "rpc-v2-cbor"),
        ]
        return HTTPResponse(status=200, fields=tuples_to_fields(headers), body=body)

    def send(
        self,
        request: HTTPRequest,
        *,
        request_config: HTTPRequestConfiguration | None = None,
    ) -> HTTPResponse:
        return self._respond(request, self.body)


class _AsyncTransport(_Transport):
    async def send(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        request: HTTPRequest,
        *,
        request_config: HTTPRequestConfiguration | None = None,
    ) -> HTTPResponse:
        return self._respond(request, AsyncBytesReader(self.body))


@pytest.mark.parametrize("aio", [False, True])
def test_snapshot_client_round_trips_through_the_runtime(
    package: ModuleType, aio: bool
) -> None:
    # CBOR {"stringValue": "out"}.
    transport = (_AsyncTransport if aio else _Transport)(b"\xa1\x6bstringValue\x63out")
    config = (package.AsyncConfig if aio else package.Config)(
        endpoint_uri="https://example.com",
        transport=transport,
        retry_strategy=SimpleRetryStrategy(max_attempts=1),
    )
    client = (package.AsyncRpcV2Protocol if aio else package.RpcV2Protocol)(config)
    call = client.simple_scalar_properties(string_value="in", integer_value=3)
    output = asyncio.run(call) if aio else call

    assert output.string_value == "out"
    (request,) = transport.requests
    assert request.destination.path == (
        "/service/RpcV2Protocol/operation/SimpleScalarProperties"
    )
    body: Any = request.body
    if not isinstance(body, bytes):
        body = body.read()
        if asyncio.iscoroutine(body):
            body = asyncio.run(body)
    assert loads(body) == {"stringValue": "in", "integerValue": 3}


def test_generated_endpoint_tests_pass() -> None:
    projection = _ROOT / "codegen-output-py/endpoint-rules-client"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests",
            "-q",
            "-p",
            "no:cacheprovider",
            "-o",
            "addopts=",
        ],
        cwd=projection,
        env={**os.environ, "PYTHONPATH": str(projection / "src")},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "14 passed, 1 skipped" in result.stdout


@pytest.fixture(scope="module")
def api_key_package() -> Iterator[ModuleType]:
    source = _ROOT / "codegen-output-py/api-key-auth-client/src"
    name = _PROJECTIONS["api-key-auth-client"]["package"]
    sys.path.insert(0, str(source))
    try:
        yield importlib.import_module(name)
    finally:
        sys.path.remove(str(source))
        for module in tuple(sys.modules):
            if module == name or module.startswith(name + "."):
                del sys.modules[module]


def _api_key_client(package: ModuleType, aio: bool, **config: Any) -> Any:
    transport = (_AsyncTransport if aio else _Transport)(b"\xa0")
    client = (package.AsyncApiKeyService if aio else package.ApiKeyService)(
        (package.AsyncConfig if aio else package.Config)(
            endpoint_uri="https://example.com",
            transport=transport,
            retry_strategy=SimpleRetryStrategy(max_attempts=1),
            **config,
        )
    )
    return client, transport


def _call(aio: bool, call: Any) -> Any:
    return asyncio.run(call) if aio else call


@pytest.mark.parametrize("aio", [False, True])
def test_api_key_auth_signs_by_operation(
    api_key_package: ModuleType, aio: bool
) -> None:
    client, transport = _api_key_client(api_key_package, aio, api_key="secret")
    _call(aio, client.get_thing(name="a"))
    _call(aio, client.ping())
    _call(aio, client.health())
    get_thing, ping, health = transport.requests
    assert get_thing.fields["Authorization"].values == ["ApiKey secret"]
    assert ping.fields["Authorization"].values == ["ApiKey secret"]
    # @auth([]) leaves only noAuth, so the request is unsigned.
    assert "Authorization" not in health.fields


@pytest.mark.parametrize("aio", [False, True])
def test_api_key_auth_requires_a_key(api_key_package: ModuleType, aio: bool) -> None:
    client, transport = _api_key_client(api_key_package, aio)
    with pytest.raises(SmithyIdentityError, match="api_key was not set"):
        _call(aio, client.get_thing(name="a"))
    _call(aio, client.health())
    assert len(transport.requests) == 1


@pytest.fixture
def aws_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> pytest.MonkeyPatch:
    """An environment with no AWS settings and empty shared config files."""
    for name in list(os.environ):
        if name.startswith("AWS_"):
            monkeypatch.delenv(name)
    monkeypatch.setenv("AWS_CONFIG_FILE", str(tmp_path / "config"))
    monkeypatch.setenv("AWS_SHARED_CREDENTIALS_FILE", str(tmp_path / "credentials"))
    # The base AWS config requires a region.
    monkeypatch.setenv("AWS_REGION", "us-west-2")
    return monkeypatch


@pytest.fixture(scope="module")
def aws_package() -> Iterator[ModuleType]:
    source = _ROOT / "codegen-output-py/aws-config-client/src"
    name = _PROJECTIONS["aws-config-client"]["package"]
    sys.path.insert(0, str(source))
    try:
        yield importlib.import_module(name)
    finally:
        sys.path.remove(str(source))
        for module in tuple(sys.modules):
            if module == name or module.startswith(name + "."):
                del sys.modules[module]


def _aws_client(package: ModuleType, aio: bool, **overrides: Any) -> Any:
    transport = (_AsyncTransport if aio else _Transport)(b"\xa1\x67summary\x63sun")
    config_class = (
        package.AsyncWeatherStationConfig if aio else package.WeatherStationConfig
    )
    config = config_class.resolve(
        transport=transport,
        retry_strategy=SimpleRetryStrategy(max_attempts=1),
        **overrides,
    )
    if aio:
        config = asyncio.run(config)
    client = package.AsyncWeatherStationClient if aio else package.WeatherStationClient
    return client(config), transport


@pytest.mark.parametrize("aio", [False, True])
def test_aws_config_resolves_the_endpoint_from_the_environment(
    aws_package: ModuleType, aio: bool, aws_env: pytest.MonkeyPatch
) -> None:
    aws_env.setenv("AWS_ENDPOINT_URL_WEATHER_STATION", "https://weather.example.com")
    client, transport = _aws_client(aws_package, aio, sdk_ua_app_id="forecaster")
    output = _call(aio, client.get_forecast(city="Lisbon"))
    assert output.summary == "sun"
    (request,) = transport.requests
    assert request.destination.host == "weather.example.com"
    user_agent = request.fields["User-Agent"].as_string()
    assert "api/Weather_Station#0.0.1" in user_agent
    assert "app/forecaster" in user_agent


@pytest.mark.parametrize("aio", [False, True])
def test_aws_config_rejects_unknown_fields(
    aws_package: ModuleType, aio: bool, aws_env: pytest.MonkeyPatch
) -> None:
    config_class = (
        aws_package.AsyncWeatherStationConfig
        if aio
        else aws_package.WeatherStationConfig
    )
    with pytest.raises(Exception, match="nope"):
        _call(aio, config_class.resolve(nope=1))
    with pytest.raises(ConfigError, match="cannot be constructed directly"):
        config_class()


def test_aws_client_resolves_its_own_config(
    aws_package: ModuleType, aws_env: pytest.MonkeyPatch
) -> None:
    (Path(os.environ["AWS_CONFIG_FILE"])).write_text(
        "[default]\nendpoint_url = https://profile.example.com\n"
    )
    transport = _Transport(b"\xa0")

    def use_transport(config: Any) -> None:
        config.transport = transport

    client = aws_package.WeatherStationClient(plugins=[use_transport])
    client.get_forecast(city="Lisbon")
    (request,) = transport.requests
    assert request.destination.host == "profile.example.com"
