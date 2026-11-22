# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import asyncio
import base64
import importlib
import json
import struct
import subprocess
import sys
import tomllib
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from smithy_cbor import loads
from smithy_core.aio.types import AsyncBytesReader
from smithy_core.exceptions import EndpointResolutionError
from smithy_core.retries import SimpleRetryStrategy
from smithy_http import HTTPResponse, tuples_to_fields
from smithy_http.interfaces import HTTPRequest, HTTPRequestConfiguration
from smithy_python import aws as _aws
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

    def __init__(
        self,
        status: int = 200,
        body: bytes = b"",
        headers: list[tuple[str, str]] = _HEADERS,
    ) -> None:
        self.status = status
        self.body = body
        self.headers = headers
        self.requests: list[HTTPRequest] = []

    def __deepcopy__(self, memo: dict[int, Any]) -> "_Transport":
        # Clients copy their config, transport included. Keep one recorder.
        return self

    def _respond(self, request: HTTPRequest, body: Any) -> HTTPResponse:
        self.requests.append(request)
        return HTTPResponse(
            status=self.status, fields=tuples_to_fields(self.headers), body=body
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


def test_dashed_package_names_the_distribution_and_imports_with_underscores(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _generate(tmp_path, "greeter-dashed")
    project = tomllib.loads((tmp_path / "pyproject.toml").read_text())["project"]
    assert project["name"] == "greeter-dashed"
    monkeypatch.syspath_prepend(  # pyright: ignore[reportUnknownMemberType]
        str(tmp_path / "src")
    )
    package = importlib.import_module("greeter_dashed")
    assert package.Greeter.__module__ == "greeter_dashed.client"
    assert package.AsyncGreeter.__module__ == "greeter_dashed.aio.client"


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


def test_client_optional_input_members_may_be_omitted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    shapes = _shapes()
    shapes["example#GreetInput"]["members"]["name"]["traits"][
        "smithy.api#clientOptional"
    ] = {}
    _generate(tmp_path, "greeter_client_optional", shapes)
    stub = (tmp_path / "src/greeter_client_optional/models.pyi").read_text()
    assert "name: str | None\n" in stub
    assert "Required[" not in stub

    monkeypatch.syspath_prepend(  # pyright: ignore[reportUnknownMemberType]
        str(tmp_path / "src")
    )
    package = importlib.import_module("greeter_client_optional")
    transport = _Transport(body=_cbor_map({}))
    package.Greeter(_config(package, transport, aio=False)).greet()
    (request,) = transport.requests
    assert loads(_body(request)) == {}


def test_rpcv2_json_service_sends_json_and_requires_the_json_extra(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    shapes = _shapes()
    shapes["example#Greeter"]["traits"] = {"smithy.protocols#rpcv2Json": {}}
    _generate(tmp_path, "greeter_json", shapes)
    project = (tmp_path / "pyproject.toml").read_text()
    assert '"smithy-http[aiohttp,json,urllib3]~=' in project
    assert "cbor" not in project

    monkeypatch.syspath_prepend(  # pyright: ignore[reportUnknownMemberType]
        str(tmp_path / "src")
    )
    package = importlib.import_module("greeter_json")
    transport = _Transport(
        body=b'{"greeting": "Hello, Ana"}',
        headers=[
            ("Content-Type", "application/json"),
            ("smithy-protocol", "rpc-v2-json"),
        ],
    )
    output = package.Greeter(_config(package, transport, aio=False)).greet(name="Ana")
    assert output.greeting == "Hello, Ana"
    (request,) = transport.requests
    assert request.fields["smithy-protocol"].values == ["rpc-v2-json"]
    assert json.loads(_body(request)) == {"name": "Ana"}


def test_a_service_with_both_protocols_needs_a_protocol_selection() -> None:
    shapes = _shapes()
    shapes["example#Greeter"]["traits"]["smithy.protocols#rpcv2Json"] = {}
    with pytest.raises(CodegenError, match="more than one supported protocol"):
        generator = ClientGenerator(_plan(shapes))
        generator.generate(generator.context())
    settings = ClientSettings(
        "greeter", "1.0.0", None, protocol=ShapeId("smithy.protocols", "rpcv2Json")
    )
    model = load_model({"smithy": "2.0", "shapes": shapes})
    generator = ClientGenerator(ClientPlan.from_model(model, settings))
    generator.generate(generator.context())


def _add_endpoint_rules(shapes: dict[str, Any]) -> None:
    nodes = (-1, 1, -1, 0, 100_000_001, 100_000_002)
    traits = shapes["example#Greeter"]["traits"]
    traits["smithy.rules#clientContextParams"] = {
        "Stage": {"type": "string", "documentation": "The deployment stage."}
    }
    traits["smithy.rules#endpointBdd"] = {
        "version": "1.1",
        "parameters": {
            "Stage": {"type": "string"},
            "Name": {"type": "string"},
            "Op": {"type": "string"},
        },
        "conditions": [{"fn": "isSet", "argv": [{"ref": "Stage"}]}],
        "results": [
            {
                "conditions": [],
                "type": "endpoint",
                "endpoint": {"url": "https://{Name}-{Op}.{Stage}.example.com"},
            },
            {"conditions": [], "type": "error", "error": "Stage is not set"},
        ],
        "root": 2,
        "nodeCount": 2,
        "nodes": base64.b64encode(struct.pack(">6i", *nodes)).decode(),
    }
    shapes["example#GreetInput"]["members"]["name"]["traits"][
        "smithy.rules#contextParam"
    ] = {"name": "Name"}
    shapes["example#Greet"]["traits"]["smithy.rules#staticContextParams"] = {
        "Op": {"value": "greet"}
    }


def test_endpoint_rules_read_config_input_and_operation_parameters(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    shapes = _shapes()
    _add_endpoint_rules(shapes)
    _generate(tmp_path, "greeter_rules", shapes)
    config_source = (tmp_path / "src/greeter_rules/config.py").read_text()
    assert "stage: str | None\n" in config_source
    assert '"The deployment stage."' in config_source

    monkeypatch.syspath_prepend(  # pyright: ignore[reportUnknownMemberType]
        str(tmp_path / "src")
    )
    package = importlib.import_module("greeter_rules")
    transport = _Transport(body=_cbor_map({"greeting": "Hi"}))
    retry = SimpleRetryStrategy(max_attempts=1)
    client = package.Greeter(
        package.Config(stage="beta", transport=transport, retry_strategy=retry)
    )
    client.greet(name="ana")
    (request,) = transport.requests
    assert request.destination.host == "ana-greet.beta.example.com"

    unstaged = package.Greeter(
        package.Config(transport=transport, retry_strategy=retry)
    )
    with pytest.raises(EndpointResolutionError, match="Stage is not set"):
        unstaged.greet(name="ana")


def test_a_service_without_rules_requires_an_endpoint_uri(
    package: ModuleType,
) -> None:
    transport = _Transport()
    client = package.Greeter(
        package.Config(
            transport=transport, retry_strategy=SimpleRetryStrategy(max_attempts=1)
        )
    )
    with pytest.raises(EndpointResolutionError, match="must configure an endpoint"):
        client.ping()
    assert not transport.requests


def _add_endpoint_tests(shapes: dict[str, Any], *inputs: dict[str, Any]) -> None:
    _add_endpoint_rules(shapes)
    traits = shapes["example#Greeter"]["traits"]
    traits["smithy.rules#endpointBdd"]["parameters"]["Region"] = {
        "type": "string",
        "builtIn": "AWS::Region",
        "default": "us-east-1",
        "required": True,
    }
    traits["smithy.rules#endpointTests"] = {
        "version": "1.0",
        "testCases": [
            {
                "documentation": "A case",
                "params": {"Stage": "beta"},
                "expect": {"endpoint": {"url": "https://beta.example.com"}},
                "operationInputs": list(inputs),
            }
        ],
    }


def _endpoint_tests(tmp_path: Path, shapes: dict[str, Any]) -> str:
    _generate(tmp_path, "greeter_endpoint_tests", shapes)
    return (tmp_path / "tests/test_endpoints.py").read_text()


def test_endpoint_tests_set_config_and_keyword_arguments(tmp_path: Path) -> None:
    shapes = _shapes()
    _add_endpoint_tests(
        shapes,
        {
            "operationName": "Greet",
            "builtInParams": {"AWS::Region": "us-east-1"},
            "clientParams": {"Stage": "beta"},
            "operationParams": {"name": "ana", "friends": [{"name": "bo"}]},
        },
    )
    tests = _endpoint_tests(tmp_path, shapes)
    assert '    {"stage": "beta"},\n' in tests
    assert "AsyncGreeter.greet,\n" in tests
    assert '{"name": "ana", "friends": [{"name": "bo"}]},' in tests
    # A built-in at its default needs no config field.
    assert "mark.skip" not in tests
    project = (tmp_path / "pyproject.toml").read_text()
    assert '"smithy-test~=0.5.0",' in project
    assert '"pytest-asyncio>=1.3.0,<2.0.0",' in project


def test_endpoint_tests_skip_inputs_the_client_cannot_express(tmp_path: Path) -> None:
    shapes = _shapes()
    shapes["example#GreetInput"]["members"]["photo"] = {"target": "smithy.api#Blob"}
    _add_endpoint_tests(
        shapes,
        {
            "operationName": "Greet",
            "builtInParams": {"AWS::Region": "us-west-2"},
            "clientParams": {"Other": "x"},
            "operationParams": {"name": "ana", "photo": "abc"},
        },
    )
    tests = _endpoint_tests(tmp_path, shapes)
    assert (
        'marks=mark.skip(reason="No config field sets the built-in AWS::Region; '
        "Other is not a client context parameter; "
        "Endpoint tests can't set blob values\"),"
    ) in tests


@pytest.mark.parametrize(
    ("operation_input", "message"),
    [
        ({"operationName": "Missing"}, "operation Missing is not in service"),
        (
            {"operationName": "Greet", "operationParams": {"nope": 1}},
            "sets nope, which it doesn't have",
        ),
    ],
)
def test_endpoint_tests_reject_unknown_operations_and_members(
    tmp_path: Path, operation_input: dict[str, Any], message: str
) -> None:
    shapes = _shapes()
    _add_endpoint_tests(shapes, operation_input)
    with pytest.raises(CodegenError, match=message):
        _generate(tmp_path, "greeter_bad_endpoint_tests", shapes)


def test_services_without_endpoint_tests_get_no_test_module(tmp_path: Path) -> None:
    shapes = _shapes()
    _add_endpoint_rules(shapes)
    _generate(tmp_path, "greeter_no_endpoint_tests", shapes)
    assert not (tmp_path / "tests").exists()
    assert "[dependency-groups]" not in (tmp_path / "pyproject.toml").read_text()


def _add_api_key(shapes: dict[str, Any], **trait: Any) -> None:
    shapes["example#Greeter"]["traits"]["smithy.api#httpApiKeyAuth"] = trait or {
        "name": "key",
        "in": "query",
    }


def test_api_key_auth_signs_requests_in_the_query(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    shapes = _shapes()
    _add_api_key(shapes)
    _generate(tmp_path, "greeter_api_key", shapes)
    monkeypatch.syspath_prepend(  # pyright: ignore[reportUnknownMemberType]
        str(tmp_path / "src")
    )
    package = importlib.import_module("greeter_api_key")
    transport = _Transport(body=_cbor_map({}))
    config = package.Config(
        api_key="s3cret",
        endpoint_uri="https://example.com",
        transport=transport,
        retry_strategy=SimpleRetryStrategy(max_attempts=1),
    )
    package.Greeter(config).greet(name="Ana")
    (request,) = transport.requests
    assert request.destination.query == "key=s3cret"


def test_an_operation_needs_one_supported_auth_scheme(tmp_path: Path) -> None:
    shapes = _shapes()
    _add_api_key(shapes)
    _add_auth(shapes)
    # Bearer auth is unsupported, but API key auth is a fallback.
    _generate(tmp_path / "fallback", "greeter_fallback", shapes)
    shapes["example#Greet"]["traits"]["smithy.api#auth"] = ["smithy.api#httpBearerAuth"]
    with pytest.raises(CodegenError, match="Operation example#Greet requires auth"):
        _generate(tmp_path / "bearer", "greeter_bearer", shapes)


def test_api_key_auth_trait_must_name_a_location(tmp_path: Path) -> None:
    shapes = _shapes()
    _add_api_key(shapes, name="key", **{"in": "body"})
    with pytest.raises(CodegenError, match="Invalid httpApiKeyAuth trait"):
        _generate(tmp_path, "greeter_bad_api_key", shapes)


def _aws_generate(output: Path, package: str, shapes: dict[str, Any]) -> None:
    generator = ClientGenerator(
        _plan(shapes, package), integrations=_aws.AWS_INTEGRATIONS
    )
    context = generator.context()
    generator.generate(context)
    context.files.commit(output)


def test_aws_services_get_named_resolving_clients(tmp_path: Path) -> None:
    shapes = _shapes()
    shapes["example#Greeter"]["traits"]["aws.api#service"] = {"sdkId": "Hello World"}
    _aws_generate(tmp_path, "greeter_aws", shapes)
    source = tmp_path / "src/greeter_aws"
    config = (source / "config.py").read_text()
    assert "class HelloWorldConfig(AwsConfig):" in config
    assert 'EndpointUriResolver("hello_world")' in config
    client = (source / "aio/client.py").read_text()
    assert "class AsyncHelloWorldClient(AsyncClient[AsyncHelloWorldConfig]):" in client
    assert "return await AsyncHelloWorldConfig.resolve()" in client
    assert "_client_plugins = (aws_user_agent_plugin, user_agent_plugin)" in client
    assert 'service_id="Hello_World"' in (source / "user_agent.py").read_text()
    assert '"smithy-aws-core~=0.16.0",' in (tmp_path / "pyproject.toml").read_text()


def test_rest_json_services_use_the_aws_core_protocol(tmp_path: Path) -> None:
    shapes = _shapes()
    shapes["example#Greeter"]["traits"] = {"aws.protocols#restJson1": {}}
    shapes["example#Greet"]["traits"] = {
        "smithy.api#http": {"method": "POST", "uri": "/greet"}
    }
    with pytest.raises(CodegenError, match="has no supported protocol"):
        _generate(tmp_path / "core", "greeter_core", shapes)

    model = load_model({"smithy": "2.0", "shapes": shapes})
    settings = ClientSettings("greeter_rest", "1.0.0", None)
    generator = ClientGenerator(
        ClientPlan.from_model(model, settings, protocols=_aws.AWS_PROTOCOLS),
        protocols=_aws.AWS_PROTOCOLS,
    )
    context = generator.context()
    generator.generate(context)
    output = tmp_path / "rest"
    context.files.commit(output)
    source = output / "src/greeter_rest"
    assert (
        "RestJsonClientProtocol(_PROTOCOL_SETTINGS)"
        in (source / "config.py").read_text()
    )
    assert (
        "AsyncRestJsonClientProtocol(_PROTOCOL_SETTINGS)"
        in (source / "aio/config.py").read_text()
    )
    assert '"smithy-aws-core[json]~=0.16.0",' in (output / "pyproject.toml").read_text()
    # The service schema keeps the protocol trait, which the AST doesn't define.
    assert "aws.protocols#restJson1" in "".join(
        path.read_text() for path in (source / "_private").glob("schemas*.py")
    )


@pytest.mark.parametrize(
    ("trait", "protocol"),
    [
        ("awsJson1_0", "AwsJson10ClientProtocol"),
        ("awsJson1_1", "AwsJson11ClientProtocol"),
    ],
)
def test_aws_json_services_use_the_aws_core_protocol(
    tmp_path: Path, trait: str, protocol: str
) -> None:
    shapes = _shapes()
    shapes["example#Greeter"]["traits"] = {
        f"aws.protocols#{trait}": {},
        "aws.protocols#awsQueryCompatible": {},
    }
    model = load_model({"smithy": "2.0", "shapes": shapes})
    settings = ClientSettings("greeter_aws_json", "1.0.0", None)
    generator = ClientGenerator(
        ClientPlan.from_model(model, settings, protocols=_aws.AWS_PROTOCOLS),
        protocols=_aws.AWS_PROTOCOLS,
    )
    context = generator.context()
    generator.generate(context)
    context.files.commit(tmp_path)
    source = tmp_path / "src/greeter_aws_json"
    assert f"{protocol}(_PROTOCOL_SETTINGS)" in (source / "config.py").read_text()
    assert (
        f"Async{protocol}(_PROTOCOL_SETTINGS)" in (source / "aio/config.py").read_text()
    )
    assert (
        '"smithy-aws-core[json]~=0.16.0",' in (tmp_path / "pyproject.toml").read_text()
    )
    # The runtime reads query compatibility from the service schema.
    assert "aws.protocols#awsQueryCompatible" in "".join(
        path.read_text() for path in (source / "_private").glob("schemas*.py")
    )


def test_integrations_apply_only_to_services_they_match(tmp_path: Path) -> None:
    _aws_generate(tmp_path, "greeter_plain", _shapes())
    assert "class Config:" in (tmp_path / "src/greeter_plain/config.py").read_text()
    assert not (tmp_path / "src/greeter_plain/user_agent.py").exists()


def test_aws_services_need_an_sdk_id(tmp_path: Path) -> None:
    shapes = _shapes()
    shapes["example#Greeter"]["traits"]["aws.api#service"] = {}
    with pytest.raises(CodegenError, match="without an sdkId"):
        _aws_generate(tmp_path, "greeter_no_sdk_id", shapes)


def test_client_context_fields_must_not_take_aws_config_fields(tmp_path: Path) -> None:
    shapes = _shapes()
    _add_endpoint_rules(shapes)
    traits = shapes["example#Greeter"]["traits"]
    traits["aws.api#service"] = {"sdkId": "Greeter"}
    traits["smithy.rules#clientContextParams"] = {"Region": {"type": "string"}}
    with pytest.raises(CodegenError, match="which the config already has"):
        _aws_generate(tmp_path, "greeter_region", shapes)


def test_aws_clients_with_dashed_package_names_import(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    shapes = _shapes()
    shapes["example#Greeter"]["traits"]["aws.api#service"] = {"sdkId": "Greeter"}
    _aws_generate(tmp_path, "aws-greeter-dashed", shapes)
    source = tmp_path / "src/aws_greeter_dashed"
    assert (
        "from aws_greeter_dashed import __version__"
        in (source / "user_agent.py").read_text()
    )
    monkeypatch.syspath_prepend(  # pyright: ignore[reportUnknownMemberType]
        str(tmp_path / "src")
    )
    package = importlib.import_module("aws_greeter_dashed")
    assert package.AsyncGreeterClient._client_plugins[0].__module__ == (
        "aws_greeter_dashed.aio.user_agent"
    )


def _add_sigv4(shapes: dict[str, Any]) -> None:
    traits = shapes["example#Greeter"]["traits"]
    traits["aws.api#service"] = {"sdkId": "Greeter"}
    traits["aws.auth#sigv4"] = {"name": "greeter"}


def test_sigv4_services_sign_with_the_signing_name(tmp_path: Path) -> None:
    shapes = _shapes()
    _add_sigv4(shapes)
    _aws_generate(tmp_path, "greeter_sigv4", shapes)
    source = tmp_path / "src/greeter_sigv4"
    config = (source / "aio/config.py").read_text()
    assert 'ShapeID("aws.auth#sigv4"): AsyncSigV4AuthScheme(service="greeter")' in (
        config
    )
    client = (source / "aio/client.py").read_text()
    assert "async def _post_setup(self, config: AsyncGreeterConfig) -> None:" in client
    assert "await AsyncIdentityChain.create(" in client
    assert "return await AsyncGreeterConfig.resolve()" in client
    models = (source / "models.py").read_text()
    assert '("aws.auth#sigv4",)' in models


def test_sigv4_needs_the_aws_integrations(tmp_path: Path) -> None:
    # Without its definition in the AST, sigv4 is still an auth scheme, so a
    # client that can't sign it isn't generated as unsigned.
    shapes = _shapes()
    _add_sigv4(shapes)
    with pytest.raises(CodegenError, match=r"requires auth \(aws\.auth#sigv4\)"):
        _generate(tmp_path, "greeter_unsigned", shapes)


def test_sigv4_trait_needs_a_signing_name(tmp_path: Path) -> None:
    shapes = _shapes()
    _add_sigv4(shapes)
    shapes["example#Greeter"]["traits"]["aws.auth#sigv4"] = {}
    with pytest.raises(CodegenError, match="needs a name"):
        _aws_generate(tmp_path, "greeter_no_signing_name", shapes)


def _add_aws_rules(shapes: dict[str, Any]) -> None:
    nodes = (-1, 1, -1, 0, 100_000_001, 100_000_002)
    shapes["example#Greeter"]["traits"]["smithy.rules#endpointBdd"] = {
        "version": "1.1",
        "parameters": {
            "Region": {"type": "string", "builtIn": "AWS::Region"},
            "UseFIPS": {
                "type": "boolean",
                "builtIn": "AWS::UseFIPS",
                "required": True,
                "default": False,
                "documentation": "Whether to use FIPS.",
            },
        },
        "conditions": [
            {"fn": "aws.partition", "argv": [{"ref": "Region"}], "assign": "p"}
        ],
        "results": [
            {
                "conditions": [],
                "type": "endpoint",
                "endpoint": {"url": "https://{Region}.{p#dnsSuffix}"},
            },
            {"conditions": [], "type": "error", "error": "No region"},
        ],
        "root": 2,
        "nodeCount": 2,
        "nodes": base64.b64encode(struct.pack(">6i", *nodes)).decode(),
    }


def test_aws_rules_use_the_aws_rules_extension(tmp_path: Path) -> None:
    shapes = _shapes()
    _add_aws_rules(shapes)
    shapes["example#Greeter"]["traits"]["aws.api#service"] = {"sdkId": "Greeter"}
    _aws_generate(tmp_path, "greeter_aws_rules", shapes)
    config = (tmp_path / "src/greeter_aws_rules/aio/config.py").read_text()
    assert "BddEndpointResolver(BDD, extensions=[AWS_RULES_EXTENSION])" in config
    assert "use_fips_endpoint: bool | None = None" in config
    assert "resolver=resolve_use_fips_endpoint_program" in config


def test_non_aws_services_with_aws_rules_use_the_extension(tmp_path: Path) -> None:
    shapes = _shapes()
    _add_aws_rules(shapes)
    _aws_generate(tmp_path, "greeter_plain_aws_rules", shapes)
    config = (tmp_path / "src/greeter_plain_aws_rules/config.py").read_text()
    assert "class Config:" in config
    assert "BddEndpointResolver(BDD, extensions=[AWS_RULES_EXTENSION])" in config


def test_aws_rule_functions_need_the_aws_integrations(tmp_path: Path) -> None:
    shapes = _shapes()
    _add_aws_rules(shapes)
    with pytest.raises(CodegenError, match=r"rules call aws\.partition"):
        _generate(tmp_path, "greeter_no_aws_rules", shapes)
