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
from smithy_core.interceptors import InputContext
from smithy_core.interceptors import Interceptor as SmithyInterceptor
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


_JSON_HEADERS = [
    ("Content-Type", "application/json"),
    ("smithy-protocol", "rpc-v2-json"),
]


class _PagedTransport(_Transport):
    """Answers each request with the next response, and fails past the last."""

    def __init__(self, *bodies: bytes) -> None:
        super().__init__(headers=_JSON_HEADERS)
        self._bodies = list(bodies)

    def send(
        self,
        request: HTTPRequest,
        *,
        request_config: HTTPRequestConfiguration | None = None,
    ) -> HTTPResponse:
        if not self._bodies:
            raise AssertionError(f"unexpected request {len(self.requests) + 1}")
        return self._respond(request, self._bodies.pop(0))


def _paginated_shapes() -> dict[str, Any]:
    shapes = _shapes()
    service = shapes["example#Greeter"]
    service["traits"] = {
        "smithy.protocols#rpcv2Json": {},
        "smithy.api#paginated": {
            "inputToken": "nextToken",
            "outputToken": "nextToken",
            "pageSize": "maxResults",
        },
    }
    service["operations"].append({"target": "example#ListThings"})
    shapes["example#ListThings"] = {
        "type": "operation",
        "input": {"target": "example#ListThingsInput"},
        "output": {"target": "example#ListThingsOutput"},
        "traits": {
            "smithy.api#readonly": {},
            "smithy.api#paginated": {"items": "things"},
        },
    }
    shapes["example#ListThingsInput"] = {
        "type": "structure",
        "members": {
            "filter": {"target": "smithy.api#String"},
            "nextToken": {"target": "smithy.api#String"},
            "maxResults": {"target": "smithy.api#Integer"},
        },
    }
    shapes["example#ListThingsOutput"] = {
        "type": "structure",
        "members": {
            "nextToken": {"target": "smithy.api#String"},
            "things": {"target": "example#Things"},
        },
    }
    shapes["example#Things"] = {
        "type": "list",
        "member": {"target": "smithy.api#String"},
    }
    return shapes


def test_paginator_lazily_requests_pages_until_the_output_token_ends(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _generate(tmp_path, "greeter_paginated", _paginated_shapes())
    monkeypatch.syspath_prepend(  # pyright: ignore[reportUnknownMemberType]
        str(tmp_path / "src")
    )
    package = importlib.import_module("greeter_paginated")
    transport = _PagedTransport(
        b'{"things": ["a", "b"], "nextToken": "t1"}',
        b'{"things": [], "nextToken": "t2"}',
        b'{"things": ["c"]}',
    )
    client = package.Greeter(_config(package, transport, aio=False))

    pages = client.paginate_list_things(filter="f", max_results=2)
    assert not transport.requests
    assert iter(pages) is pages

    # An empty page with a token continues. A page without one ends.
    assert [(type(page).__name__, page.things, page.next_token) for page in pages] == [
        ("ListThingsOutput", ["a", "b"], "t1"),
        ("ListThingsOutput", [], "t2"),
        ("ListThingsOutput", ["c"], None),
    ]
    assert [json.loads(_body(request)) for request in transport.requests] == [
        {"filter": "f", "maxResults": 2},
        {"filter": "f", "maxResults": 2, "nextToken": "t1"},
        {"filter": "f", "maxResults": 2, "nextToken": "t2"},
    ]
    assert next(pages, None) is None
    assert len(transport.requests) == 3


class _AsyncPagedTransport(_PagedTransport):
    async def send(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        request: HTTPRequest,
        *,
        request_config: HTTPRequestConfiguration | None = None,
    ) -> HTTPResponse:
        response = super().send(request, request_config=request_config)
        response.body = AsyncBytesReader(response.body)  # pyright: ignore[reportArgumentType]
        return response


def _scan_shapes() -> dict[str, Any]:
    """Adds pagination exercising names, nested paths, maps, and unions.

    ``PaginateListThings`` takes the name ``ListThings``'s paginator prefers.
    ``ScanItems`` overrides the service's tokens with a keyword-named input
    token and nested map outputs. ``Count`` inherits every setting and has no
    items.
    """
    shapes = _paginated_shapes()
    operations = shapes["example#Greeter"]["operations"]
    for name in ("PaginateListThings", "ScanItems", "Count"):
        operations.append({"target": f"example#{name}"})
        shapes[f"example#{name}"] = {
            "type": "operation",
            "input": {"target": f"example#{name}Input"},
            "output": {"target": f"example#{name}Output"},
        }
        shapes[f"example#{name}Input"] = {"type": "structure", "members": {}}
        shapes[f"example#{name}Output"] = {"type": "structure", "members": {}}
    shapes["example#ScanItems"]["traits"] = {
        "smithy.api#paginated": {
            "inputToken": "from",
            "outputToken": "page.lastKey",
            "pageSize": "limit",
            "items": "page.entries",
        }
    }
    shapes["example#ScanItemsInput"]["members"] = {
        "from": {"target": "example#Key"},
        "limit": {"target": "smithy.api#Integer"},
    }
    shapes["example#ScanItemsOutput"]["members"] = {
        "page": {"target": "example#ScanPage"}
    }
    shapes["example#ScanPage"] = {
        "type": "structure",
        "members": {
            "lastKey": {"target": "example#Key"},
            "entries": {"target": "example#Entries"},
        },
    }
    shapes["example#Key"] = {
        "type": "map",
        "key": {"target": "smithy.api#String"},
        "value": {"target": "example#AttributeValue"},
    }
    shapes["example#AttributeValue"] = {
        "type": "union",
        "members": {
            "s": {"target": "smithy.api#String"},
            "b": {"target": "smithy.api#Blob"},
        },
    }
    shapes["example#Entries"] = {
        "type": "map",
        "key": {"target": "smithy.api#String"},
        "value": {"target": "example#Thing"},
        "traits": {"smithy.api#sparse": {}},
    }
    shapes["example#Thing"] = {
        "type": "structure",
        "members": {"name": {"target": "smithy.api#String"}},
    }
    shapes["example#Count"]["traits"] = {"smithy.api#paginated": {}}
    shapes["example#CountInput"]["members"] = {
        "nextToken": {"target": "smithy.api#String"},
        "maxResults": {"target": "smithy.api#Integer"},
    }
    shapes["example#CountOutput"]["members"] = {
        "nextToken": {"target": "smithy.api#String"},
        "total": {"target": "smithy.api#Integer"},
    }
    return shapes


def test_paginators_type_check_with_their_page_and_item_types(
    tmp_path: Path,
) -> None:
    shapes = _scan_shapes()
    # An input member named like the SDK option is escaped, so the SDK keyword
    # and the input's dictionary keys don't overlap.
    shapes["example#CountInput"]["members"]["stopOnSameToken"] = {
        "target": "smithy.api#String"
    }
    _generate(tmp_path, "greeter_pages_typing", shapes)
    (tmp_path / "pyrightconfig.json").write_text(
        json.dumps({"typeCheckingMode": "strict", "enableExperimentalFeatures": True})
    )
    (tmp_path / "src" / "consumer.py").write_text(
        # An ignore comment that hides no error is itself an error.
        "# pyright: reportUnnecessaryTypeIgnoreComment=true\n"
        "from typing import assert_type\n\n"
        "from smithy_core.aio.pagination import AsyncItemPaginator, AsyncPaginator\n"
        "from smithy_core.pagination import ItemPaginator, Paginator\n\n"
        "from greeter_pages_typing import AsyncGreeter, Config, Greeter, models\n\n"
        "type Entry = tuple[str, models.Thing | None]\n"
        "client = Greeter(Config(endpoint_uri='https://example.com'))\n"
        "assert_type(client.paginate_list_things(), models.PaginateListThingsOutput)\n"
        "assert_type(\n"
        "    client.paginate_list_things_(filter='f', max_results=1),\n"
        "    ItemPaginator[models.ListThingsOutput, str],\n"
        ")\n"
        "scan = client.paginate_scan_items({'from_': {'k': {'s': 'v'}}})\n"
        "assert_type(scan, ItemPaginator[models.ScanItemsOutput, Entry])\n"
        "for page in scan:\n"
        "    assert_type(page, models.ScanItemsOutput)\n"
        "for entry in client.paginate_scan_items(models.ScanItemsInput()).items():\n"
        "    assert_type(entry, Entry)\n"
        "assert_type(client.paginate_count(), Paginator[models.CountOutput])\n"
        "polled = client.paginate_count(next_token='t', stop_on_same_token=False)\n"
        "assert_type(polled, Paginator[models.CountOutput])\n"
        "modeled = client.paginate_count(\n"
        "    stop_on_same_token_='t', stop_on_same_token=False\n"
        ")\n"
        "assert_type(modeled, Paginator[models.CountOutput])\n"
        "assert_type(client.count({'stop_on_same_token_': 't'}), models.CountOutput)\n"
        "client.paginate_count(stop_on_same_token='no')  # pyright: ignore\n"
        "client.paginate_count({}, stop_on_same_token=None)  # pyright: ignore\n"
        "client.paginate_count({'stop_on_same_token': 't'})  # pyright: ignore\n"
        "client.count(stop_on_same_token='t')  # pyright: ignore\n\n\n"
        "async def run(client: AsyncGreeter) -> None:\n"
        "    count = client.paginate_count(next_token='t')\n"
        "    assert_type(count, AsyncPaginator[models.CountOutput])\n"
        "    request = models.ScanItemsInput()\n"
        "    scan = client.paginate_scan_items(request, stop_on_same_token=False)\n"
        "    assert_type(scan, AsyncItemPaginator[models.ScanItemsOutput, Entry])\n"
        "    things = client.paginate_list_things_()\n"
        "    assert_type(things, AsyncItemPaginator[models.ListThingsOutput, str])\n"
        "    async for thing in things.items():\n"
        "        assert_type(thing, str)\n"
    )
    checked = subprocess.run(
        [sys.executable, "-m", "pyright", "src"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert checked.returncode == 0, checked.stdout + checked.stderr


class _AddToken:
    """A per-call plugin whose interceptor changes the request token in place.

    It changes the token's string union values and adds an entry.
    """

    def __init__(self, models: Any) -> None:
        self.models = models
        self.calls = 0

    def __call__(self, config: Any) -> None:
        self.calls += 1
        models = self.models

        class Interceptor(SmithyInterceptor[Any, Any, Any, Any]):
            def modify_before_serialization(self, context: InputContext[Any]) -> Any:
                token = context.request.from_
                if token is not None:
                    for value in token.values():
                        if isinstance(value, models.AttributeValueS):
                            value.value = "changed"
                    token["extra"] = models.AttributeValueS(value="x")
                return context.request

        config.interceptors.append(Interceptor())


@pytest.mark.parametrize("aio", [False, True], ids=["sync", "async"])
async def test_union_map_tokens_are_isolated_and_compared_by_value(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, aio: bool
) -> None:
    name = "greeter_scan_aio" if aio else "greeter_scan"
    _generate(tmp_path, name, _scan_shapes())
    monkeypatch.syspath_prepend(  # pyright: ignore[reportUnknownMemberType]
        str(tmp_path / "src")
    )
    package = importlib.import_module(name)
    models: Any = importlib.import_module(f"{name}.models")
    key = base64.b64encode(b"\x00k1").decode()
    bodies = (
        json.dumps(
            {
                "page": {
                    "lastKey": {"id": {"b": key}},
                    "entries": {"a": {"name": "x"}, "b": None},
                }
            }
        ).encode(),
        json.dumps({"page": {"lastKey": {"id": {"b": key}}}}).encode(),
    )
    transport = (_AsyncPagedTransport if aio else _PagedTransport)(*bodies)
    client = (package.AsyncGreeter if aio else package.Greeter)(
        _config(package, transport, aio=aio)
    )
    plugin = _AddToken(models)
    value = models.AttributeValueS(value="original")
    initial = {"id": value}
    request = models.ScanItemsInput(from_=initial, limit=5)
    pages = client.paginate_scan_items(request, plugins=[plugin])
    # A change to the caller's token after the paginator is made is not sent.
    initial["late"] = models.AttributeValueS(value="late")

    async def advance() -> Any:
        return await anext(pages) if aio else next(pages)

    first = await advance()
    # The interceptor's changes to the first request reached neither the
    # caller's map nor its union values.
    assert initial == {"id": value, "late": models.AttributeValueS(value="late")}
    assert value == models.AttributeValueS(value="original")
    assert first.page.last_key == {"id": models.AttributeValueB(value=b"\x00k1")}
    assert first.page.entries == {"a": models.Thing(name="x"), "b": None}
    first.page.last_key["id"].value = b"changed by caller"
    second = await advance()
    # The second response repeats the token its request sent, so pagination ends
    # after it. The interceptor's addition to that request changed neither the
    # stored token nor the comparison.
    assert second.page.last_key == {"id": models.AttributeValueB(value=b"\x00k1")}
    if aio:
        with pytest.raises(StopAsyncIteration):
            await anext(pages)
    else:
        assert next(pages, None) is None
    assert [json.loads(_body(request)) for request in transport.requests] == [
        {"limit": 5, "from": {"id": {"s": "changed"}, "extra": {"s": "x"}}},
        {"limit": 5, "from": {"id": {"b": key}, "extra": {"s": "x"}}},
    ]
    assert plugin.calls == 2


def test_paginator_input_styles_validate_early_and_copy_the_request(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _generate(tmp_path, "greeter_pages_input", _scan_shapes())
    monkeypatch.syspath_prepend(  # pyright: ignore[reportUnknownMemberType]
        str(tmp_path / "src")
    )
    package = importlib.import_module("greeter_pages_input")
    models: Any = importlib.import_module("greeter_pages_input.models")
    transport = _PagedTransport(*[b'{"total": 1}'] * 3)
    client = package.Greeter(_config(package, transport, aio=False))

    request = models.CountInput(next_token="start", max_results=3)
    values = {"next_token": "start", "max_results": 3}
    for pages in (
        client.paginate_count(request),
        client.paginate_count(values),
        client.paginate_count(**values),
    ):
        assert [page.total for page in pages] == [1]
    assert request == models.CountInput(next_token="start", max_results=3)
    assert values == {"next_token": "start", "max_results": 3}
    assert [json.loads(_body(sent)) for sent in transport.requests] == [
        {"nextToken": "start", "maxResults": 3}
    ] * 3

    with pytest.raises(TypeError, match="unknown"):
        client.paginate_count(unknown=1)
    with pytest.raises(TypeError, match="not both"):
        client.paginate_count(request, max_results=1)
    assert len(transport.requests) == 3


@pytest.mark.parametrize("aio", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("style", ["keywords", "model", "dict"])
async def test_paginators_continue_on_repeated_tokens_when_asked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, aio: bool, style: str
) -> None:
    name = f"greeter_pages_poll_{style}" + ("_aio" if aio else "")
    _generate(tmp_path, name, _paginated_shapes())
    monkeypatch.syspath_prepend(  # pyright: ignore[reportUnknownMemberType]
        str(tmp_path / "src")
    )
    package = importlib.import_module(name)
    models: Any = importlib.import_module(f"{name}.models")
    # The first response repeats the starting token, and the second repeats the
    # token its request sent.
    bodies = (b'{"nextToken": "t1"}', b'{"nextToken": "t1"}', b'{"things": ["a"]}')
    transport = (_AsyncPagedTransport if aio else _PagedTransport)(*bodies)
    client = (package.AsyncGreeter if aio else package.Greeter)(
        _config(package, transport, aio=aio)
    )
    calls: list[object] = []
    options: dict[str, Any] = {"plugins": [calls.append], "stop_on_same_token": False}
    values = {"filter": "f", "next_token": "t1"}
    if style == "keywords":
        pages = client.paginate_list_things(**values, **options)
    elif style == "model":
        pages = client.paginate_list_things(models.ListThingsInput(**values), **options)
    else:
        pages = client.paginate_list_things(values, **options)

    collected = [page async for page in pages] if aio else list(pages)
    assert [page.next_token for page in collected] == ["t1", "t1", None]
    # The SDK option is not sent.
    assert [json.loads(_body(request)) for request in transport.requests] == [
        {"filter": "f", "nextToken": "t1"}
    ] * 3
    assert len(calls) == 3


@pytest.mark.parametrize("aio", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("style", ["keywords", "model", "dict"])
async def test_input_members_named_like_the_sdk_option_are_escaped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, aio: bool, style: str
) -> None:
    # A modeled stopOnSameToken, also the input token, and a sibling already named
    # like its escape. Output members keep their names.
    shapes = _scan_shapes()
    members = shapes["example#CountInput"]["members"]
    members["stopOnSameToken"] = {"target": "smithy.api#String"}
    members["stop_on_same_token_"] = {"target": "smithy.api#String"}
    shapes["example#Count"]["traits"] = {
        "smithy.api#paginated": {"inputToken": "stopOnSameToken"}
    }
    output = shapes["example#CountOutput"]["members"]
    output["stopOnSameToken"] = {"target": "smithy.api#String"}
    name = f"greeter_pages_names_{style}" + ("_aio" if aio else "")
    _generate(tmp_path, name, shapes)
    stub = (tmp_path / "src" / name / "models.pyi").read_text()
    typed_dict = stub.split("class CountInputDict(")[1].split("\nclass ")[0]
    assert "stop_on_same_token__: str | None" in typed_dict
    assert "stop_on_same_token_: str | None" in typed_dict
    assert "stop_on_same_token: " not in typed_dict

    monkeypatch.syspath_prepend(  # pyright: ignore[reportUnknownMemberType]
        str(tmp_path / "src")
    )
    package = importlib.import_module(name)
    models: Any = importlib.import_module(f"{name}.models")
    # The first response repeats the starting token, which the SDK option allows.
    bodies = (
        b'{"nextToken": "t1", "stopOnSameToken": "out"}',
        b'{"nextToken": "t2"}',
        b"{}",
        b"{}",
    )
    transport = (_AsyncPagedTransport if aio else _PagedTransport)(*bodies)
    client = (package.AsyncGreeter if aio else package.Greeter)(
        _config(package, transport, aio=aio)
    )
    values = {"stop_on_same_token__": "t1", "stop_on_same_token_": "s"}
    if style == "keywords":
        pages = client.paginate_count(**values, stop_on_same_token=False)
    elif style == "model":
        request = models.CountInput(**values)
        pages = client.paginate_count(request, stop_on_same_token=False)
    else:
        pages = client.paginate_count(values, stop_on_same_token=False)

    collected = [page async for page in pages] if aio else list(pages)
    assert [page.next_token for page in collected] == ["t1", "t2", None]
    assert collected[0].stop_on_same_token == "out"
    # The ordinary operation method takes the same escaped field.
    if aio:
        await client.count(stop_on_same_token__="x")
    else:
        client.count(stop_on_same_token__="x")
    assert [json.loads(_body(request)) for request in transport.requests] == [
        {"stopOnSameToken": "t1", "stop_on_same_token_": "s"},
        {"stopOnSameToken": "t1", "stop_on_same_token_": "s"},
        {"stopOnSameToken": "t2", "stop_on_same_token_": "s"},
        {"stopOnSameToken": "x"},
    ]


@pytest.mark.parametrize("target", ["Byte", "Short", "Long"])
def test_page_size_may_target_any_integral_type(target: str) -> None:
    shapes = _scan_shapes()
    integral = f"smithy.api#{target}"
    # Count inherits the service's pageSize, and ScanItems names its own.
    shapes["example#CountInput"]["members"]["maxResults"]["target"] = integral
    shapes["example#ScanItemsInput"]["members"]["limit"]["target"] = integral
    generator = ClientGenerator(_plan(shapes))
    generator.generate(generator.context())


def test_paginated_clients_load_no_models_until_used(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _generate(tmp_path, "greeter_pages_lazy", _scan_shapes())
    monkeypatch.syspath_prepend(  # pyright: ignore[reportUnknownMemberType]
        str(tmp_path / "src")
    )
    importlib.import_module("greeter_pages_lazy.client")
    importlib.import_module("greeter_pages_lazy.aio.client")
    models: Any = sys.modules["greeter_pages_lazy.models"]
    assert not models._registry._classes  # pyright: ignore[reportPrivateUsage]


def _set_scan(**settings: str) -> Callable[[dict[str, Any]], None]:
    def change(shapes: dict[str, Any]) -> None:
        shapes["example#ScanItems"]["traits"]["smithy.api#paginated"].update(settings)

    return change


def _drop_service_tokens(shapes: dict[str, Any]) -> None:
    del shapes["example#Greeter"]["traits"]["smithy.api#paginated"]["inputToken"]


def _set_service(**settings: str) -> Callable[[dict[str, Any]], None]:
    def change(shapes: dict[str, Any]) -> None:
        shapes["example#Greeter"]["traits"]["smithy.api#paginated"].update(settings)

    return change


def _string_count_page_size(shapes: dict[str, Any]) -> None:
    shapes["example#CountInput"]["members"]["maxResults"]["target"] = (
        "smithy.api#String"
    )


def _string_scan_input_token(shapes: dict[str, Any]) -> None:
    shapes["example#ScanItemsInput"]["members"]["from"]["target"] = "smithy.api#String"


def _map_count_input_token(shapes: dict[str, Any]) -> None:
    shapes["example#CountInput"]["members"]["nextToken"]["target"] = "example#Key"


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (_drop_service_tokens, "example#ListThings needs an inputToken"),
        (_set_scan(inputToken="limitless"), "inputToken 'limitless'"),
        (
            _set_scan(inputToken="limit"),
            "example#ScanItems has inputToken 'limit' targeting a integer",
        ),
        (
            _string_scan_input_token,
            "example#ScanItems has inputToken 'from' targeting a string, but "
            "outputToken 'page.lastKey' targets a map",
        ),
        (
            _map_count_input_token,
            "example#Count has inputToken 'nextToken' targeting a map, but "
            "outputToken 'nextToken' targets a string",
        ),
        (_set_scan(outputToken="page.missing"), "'missing' is not a member"),
        (_set_scan(outputToken="page.lastKey.id"), "'id' is not a member"),
        (_set_scan(outputToken="page"), "outputToken 'page' targeting a structure"),
        (_set_scan(items="page.lastKey.x"), "'x' is not a member"),
        (_set_scan(items="page"), "items 'page' targeting a structure"),
        # An inherited pageSize, then an operation's own, that isn't a member.
        (
            _set_service(pageSize="pageLimit"),
            "example#ListThings names pageSize 'pageLimit'",
        ),
        (_set_scan(pageSize="size"), "example#ScanItems names pageSize 'size'"),
        # An inherited pageSize, then an operation's own, that isn't an integer.
        (
            _string_count_page_size,
            "example#Count has pageSize 'maxResults' targeting a string",
        ),
        (
            _set_scan(pageSize="from"),
            "example#ScanItems has pageSize 'from' targeting a map",
        ),
    ],
)
def test_unresolvable_pagination_fails_naming_the_operation(
    change: Callable[[dict[str, Any]], None], message: str
) -> None:
    shapes = _scan_shapes()
    change(shapes)
    generator = ClientGenerator(_plan(shapes))
    with pytest.raises(CodegenError, match=message):
        generator.generate(generator.context())


async def test_async_paginator_is_returned_without_awaiting(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _generate(tmp_path, "greeter_pages_aio", _paginated_shapes())
    monkeypatch.syspath_prepend(  # pyright: ignore[reportUnknownMemberType]
        str(tmp_path / "src")
    )
    package = importlib.import_module("greeter_pages_aio")
    transport = _AsyncPagedTransport(
        b'{"things": ["a"], "nextToken": "t1"}',
        b'{"nextToken": "t2"}',
        b'{"things": ["b"]}',
    )
    client = package.AsyncGreeter(_config(package, transport, aio=True))
    things = client.paginate_list_things(filter="f")
    assert not transport.requests
    assert [thing async for thing in things.items()] == ["a", "b"]
    assert [
        json.loads(_body(request)).get("nextToken") for request in transport.requests
    ] == [
        None,
        "t1",
        "t2",
    ]


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
