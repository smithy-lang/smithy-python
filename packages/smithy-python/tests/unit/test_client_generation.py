# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import asyncio
import importlib
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from smithy_cbor import loads
from smithy_core.aio.types import AsyncBytesReader
from smithy_core.retries import SimpleRetryStrategy
from smithy_http import HTTPResponse, tuples_to_fields
from smithy_http.interfaces import HTTPRequest, HTTPRequestConfiguration
from smithy_python.clients import ClientGenerator, ClientPlan
from smithy_python.exceptions import CodegenError
from smithy_python.generation import ClientSettings
from smithy_python.model import ShapeId, load_model

_CBOR = "smithy.protocols#rpcv2Cbor"


def _shapes() -> dict[str, Any]:
    return {
        "example#Greeter": {
            "type": "service",
            "version": "2026-01-01",
            "operations": [
                {"target": "example#Greet"},
                {"target": "example#Ping"},
                {"target": "example#Empty"},
            ],
            "traits": {_CBOR: {}},
        },
        "example#Greet": {
            "type": "operation",
            "input": {"target": "example#GreetInput"},
            "output": {"target": "example#GreetOutput"},
            "errors": [{"target": "example#InvalidGreeting"}],
            "traits": {"smithy.api#documentation": "Greets someone."},
        },
        "example#GreetInput": {
            "type": "structure",
            "members": {
                "name": {
                    "target": "smithy.api#String",
                    "traits": {"smithy.api#required": {}},
                },
                "friends": {"target": "example#People"},
            },
        },
        "example#People": {"type": "list", "member": {"target": "example#Person"}},
        "example#Person": {
            "type": "structure",
            "members": {"name": {"target": "smithy.api#String"}},
        },
        "example#GreetOutput": {
            "type": "structure",
            "members": {"greeting": {"target": "smithy.api#String"}},
        },
        "example#InvalidGreeting": {
            "type": "structure",
            "members": {"message": {"target": "smithy.api#String"}},
            "traits": {"smithy.api#error": "client"},
        },
        "example#Ping": {"type": "operation"},
        "example#Empty": {
            "type": "operation",
            "input": {"target": "example#EmptyInput"},
            "output": {"target": "example#EmptyOutput"},
        },
        "example#EmptyInput": {"type": "structure", "members": {}},
        "example#EmptyOutput": {"type": "structure", "members": {}},
    }


def _plan(shapes: dict[str, Any], package: str = "greeter") -> ClientPlan:
    return ClientPlan.from_model(
        load_model({"smithy": "2.0", "shapes": shapes}),
        ClientSettings(package, "1.0.0", None),
    )


def _generate(output: Path, package: str, shapes: dict[str, Any] | None = None) -> None:
    generator = ClientGenerator(_plan(shapes or _shapes(), package))
    context = generator.context()
    generator.generate(context)
    context.files.commit(output)


def _text(value: str) -> bytes:
    data = value.encode()
    assert len(data) < 24
    return bytes([0x60 + len(data)]) + data


def _cbor_map(values: dict[str, str]) -> bytes:
    """Encode a small map of short strings, enough for test responses."""
    return bytes([0xA0 + len(values)]) + b"".join(
        _text(key) + _text(value) for key, value in values.items()
    )


_HEADERS = [("Content-Type", "application/cbor"), ("smithy-protocol", "rpc-v2-cbor")]


class _Transport:
    TIMEOUT_EXCEPTIONS = ()

    def __init__(self, status: int = 200, body: bytes = b"") -> None:
        self.status = status
        self.body = body
        self.requests: list[HTTPRequest] = []

    def __deepcopy__(self, memo: dict[int, Any]) -> "_Transport":
        # Clients copy their config, transport included. Keep one recorder.
        return self

    def _respond(self, request: HTTPRequest, body: Any) -> HTTPResponse:
        self.requests.append(request)
        return HTTPResponse(
            status=self.status, fields=tuples_to_fields(_HEADERS), body=body
        )

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


def _body(request: HTTPRequest) -> bytes:
    body: Any = request.body
    if isinstance(body, bytes | bytearray):
        return bytes(body)
    if hasattr(body, "read"):
        result = body.read()
        return asyncio.run(result) if asyncio.iscoroutine(result) else result
    return b"".join(body) if body else b""


@pytest.fixture(scope="module")
def package(tmp_path_factory: pytest.TempPathFactory) -> ModuleType:
    output = tmp_path_factory.mktemp("client")
    _generate(output, "greeter")
    sys.path.insert(0, str(output / "src"))
    try:
        return importlib.import_module("greeter")
    finally:
        sys.path.remove(str(output / "src"))


def _config(package: ModuleType, transport: _Transport, *, aio: bool) -> Any:
    config = package.AsyncConfig if aio else package.Config
    return config(
        endpoint_uri="https://example.com",
        transport=transport,
        retry_strategy=SimpleRetryStrategy(max_attempts=1),
    )


def test_package_loads_no_clients_or_models_until_used(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _generate(tmp_path, "greeter_lazy")
    monkeypatch.syspath_prepend(  # pyright: ignore[reportUnknownMemberType]
        str(tmp_path / "src")
    )
    package = importlib.import_module("greeter_lazy")
    assert not [name for name in sys.modules if name.startswith("greeter_lazy.")]
    assert package.Greeter.__module__ == "greeter_lazy.client"
    assert "greeter_lazy.aio.client" not in sys.modules
    models: Any = sys.modules["greeter_lazy.models"]
    assert not models._registry._classes  # pyright: ignore[reportPrivateUsage]


@pytest.mark.parametrize("aio", [False, True])
def test_operation_sends_cbor_request_and_returns_output(
    package: ModuleType, aio: bool
) -> None:
    transport = (_AsyncTransport if aio else _Transport)(
        body=_cbor_map({"greeting": "Hello, Ana"})
    )
    client = (package.AsyncGreeter if aio else package.Greeter)(
        _config(package, transport, aio=aio)
    )
    call = client.greet(name="Ana", friends=[{"name": "Bo"}])
    output = asyncio.run(call) if aio else call

    assert type(output).__name__ == "GreetOutput"
    assert output.greeting == "Hello, Ana"
    (request,) = transport.requests
    assert request.method == "POST"
    assert request.destination.host == "example.com"
    assert request.destination.path == "/service/Greeter/operation/Greet"
    assert request.fields["smithy-protocol"].values == ["rpc-v2-cbor"]
    assert request.fields["content-type"].values == ["application/cbor"]
    assert loads(_body(request)) == {"name": "Ana", "friends": [{"name": "Bo"}]}


@pytest.mark.parametrize("aio", [False, True])
def test_modeled_errors_raise_their_generated_types(
    package: ModuleType, aio: bool
) -> None:
    transport = (_AsyncTransport if aio else _Transport)(
        status=400,
        body=_cbor_map({"__type": "example#InvalidGreeting", "message": "No"}),
    )
    client = (package.AsyncGreeter if aio else package.Greeter)(
        _config(package, transport, aio=aio)
    )
    models: Any = importlib.import_module("greeter.models")
    with pytest.raises(models.InvalidGreeting) as error:
        call = client.greet({"name": "Ana"})
        asyncio.run(call) if aio else call
    assert isinstance(error.value, models.ServiceError)
    assert error.value.message == "No"


def test_unit_input_omits_the_body_and_explicit_empty_input_sends_one(
    package: ModuleType,
) -> None:
    transport = _Transport(body=b"")
    client = package.Greeter(_config(package, transport, aio=False))
    client.ping()
    transport.body = _cbor_map({})
    client.empty()
    ping, empty = transport.requests
    assert not _body(ping)
    with pytest.raises(KeyError):
        ping.fields["content-type"]
    assert loads(_body(empty)) == {}
    assert empty.fields["content-type"].values == ["application/cbor"]


def test_required_keyword_input_is_enforced_before_sending(
    package: ModuleType,
) -> None:
    transport = _Transport()
    client = package.Greeter(_config(package, transport, aio=False))
    with pytest.raises(TypeError, match="name"):
        client.greet()
    assert not transport.requests


def test_generated_client_type_checks_for_consumers(tmp_path: Path) -> None:
    _generate(tmp_path, "greeter_typing")
    (tmp_path / "src" / "consumer.py").write_text(
        "from greeter_typing import AsyncGreeter, Config, Greeter, models\n\n"
        "client = Greeter(Config(endpoint_uri='https://example.com'))\n"
        "output: models.GreetOutput = client.greet(name='Ana', friends=[{'name': 'Bo'}])\n"
        "other: models.GreetOutput = client.greet({'name': 'Ana'})\n"
        "client.ping()\n\n\n"
        "async def call(client: AsyncGreeter) -> models.GreetOutput:\n"
        "    return await client.greet(models.GreetInput(name='Ana'))\n"
    )
    checked = subprocess.run(
        [sys.executable, "-m", "pyright", "src"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert checked.returncode == 0, checked.stdout + checked.stderr


def _add_auth(shapes: dict[str, Any]) -> None:
    shapes["example#Greeter"]["traits"]["smithy.api#httpBearerAuth"] = {}


def _add_rules(shapes: dict[str, Any]) -> None:
    shapes["example#Greeter"]["traits"]["smithy.rules#endpointRuleSet"] = {}


def _add_stream(shapes: dict[str, Any]) -> None:
    shapes["example#GreetOutput"]["members"]["data"] = {"target": "example#Stream"}
    shapes["example#Stream"] = {
        "type": "blob",
        "traits": {"smithy.api#streaming": {}},
    }


def _remove_protocol(shapes: dict[str, Any]) -> None:
    del shapes["example#Greeter"]["traits"][_CBOR]


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (_add_auth, "Operation example#Greet requires auth"),
        (_add_rules, "smithy.rules#endpointRuleSet"),
        (_add_stream, "Operation example#Greet streams"),
        (_remove_protocol, "has no supported protocol"),
    ],
)
def test_unsupported_models_fail_before_writing_files(
    tmp_path: Path, change: Callable[[dict[str, Any]], None], message: str
) -> None:
    shapes = _shapes()
    change(shapes)
    with pytest.raises(CodegenError, match=message):
        _generate(tmp_path, "greeter_unsupported", shapes)
    assert not any(tmp_path.iterdir())


def test_protocol_selection_must_be_modeled_and_supported() -> None:
    plan = _plan(_shapes())
    for protocol, message in (
        (ShapeId("smithy.protocols", "rpcv2Json"), "is not a trait on service"),
        (ShapeId("smithy.protocols", "rpcv2Cbor"), None),
    ):
        settings = ClientSettings("greeter", "1.0.0", None, protocol=protocol)
        generator = ClientGenerator(ClientPlan.from_model(plan.model, settings))
        context = generator.context()
        if message is None:
            generator.generate(context)
        else:
            with pytest.raises(CodegenError, match=message):
                generator.generate(context)
