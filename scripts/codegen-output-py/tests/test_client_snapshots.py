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
from collections.abc import Callable, Iterator
from pathlib import Path
from types import ModuleType
from typing import Any, NamedTuple

import pytest
from smithy_aws_core.aio.identity.chain import AsyncIdentityChain
from smithy_aws_core.config.exceptions import ConfigError
from smithy_aws_core.identity.chain.exceptions import IdentityChainError
from smithy_aws_core.identity.chain.resolver import IdentityChain
from smithy_cbor import loads
from smithy_core import waiters as sync_waiters
from smithy_core.aio import waiters as async_waiters
from smithy_core.aio.types import AsyncBytesReader
from smithy_core.exceptions import SmithyIdentityError, WaiterFailureError
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

    def __init__(self, *bodies: bytes | tuple[int, bytes]) -> None:
        self.bodies = bodies
        self.requests: list[HTTPRequest] = []

    def __deepcopy__(self, memo: dict[int, Any]) -> _Transport:
        # Clients copy their config, transport included. Keep one recorder.
        return self

    def _record(self, request: HTTPRequest) -> tuple[int, bytes]:
        # Each request gets the next body, and the last body repeats.
        self.requests.append(request)
        body = self.bodies[min(len(self.requests), len(self.bodies)) - 1]
        return body if isinstance(body, tuple) else (200, body)

    def _respond(self, status: int, body: Any) -> HTTPResponse:
        headers = [
            ("Content-Type", "application/cbor"),
            ("smithy-protocol", "rpc-v2-cbor"),
        ]
        return HTTPResponse(status=status, fields=tuples_to_fields(headers), body=body)

    def send(
        self,
        request: HTTPRequest,
        *,
        request_config: HTTPRequestConfiguration | None = None,
    ) -> HTTPResponse:
        return self._respond(*self._record(request))


class _AsyncTransport(_Transport):
    async def send(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        request: HTTPRequest,
        *,
        request_config: HTTPRequestConfiguration | None = None,
    ) -> HTTPResponse:
        status, body = self._record(request)
        return self._respond(status, AsyncBytesReader(body))


def _body(request: HTTPRequest) -> Any:
    body: Any = request.body
    if not isinstance(body, bytes):
        body = body.read()
        if asyncio.iscoroutine(body):
            body = asyncio.run(body)
    return loads(body)


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
    assert _body(request) == {"stringValue": "in", "integerValue": 3}


@pytest.fixture
def aws_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> pytest.MonkeyPatch:
    """An environment with only a region, credentials, and empty config files."""
    for name in list(os.environ):
        if name.startswith("AWS_"):
            monkeypatch.delenv(name)
    monkeypatch.setenv("AWS_CONFIG_FILE", str(tmp_path / "config"))
    monkeypatch.setenv("AWS_SHARED_CREDENTIALS_FILE", str(tmp_path / "credentials"))
    # The base AWS config requires a region, and SigV4 requires credentials.
    monkeypatch.setenv("AWS_REGION", "us-west-2")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AKIDFROMENV")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")
    return monkeypatch


def test_generated_endpoint_tests_pass(aws_env: pytest.MonkeyPatch) -> None:
    projection = _ROOT / "codegen-output-py/features-client"
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
    assert "17 passed" in result.stdout
    assert "skipped" not in result.stdout


@pytest.fixture(scope="module")
def features() -> Iterator[ModuleType]:
    source = _ROOT / "codegen-output-py/features-client/src"
    name = _PROJECTIONS["features-client"]["package"]
    sys.path.insert(0, str(source))
    try:
        yield importlib.import_module(name)
    finally:
        sys.path.remove(str(source))
        for module in tuple(sys.modules):
            if module == name or module.startswith(name + "."):
                del sys.modules[module]


def _client(
    package: ModuleType, aio: bool, *bodies: bytes | tuple[int, bytes], **overrides: Any
) -> Any:
    # CBOR {"id": "n1"} by default.
    transport = (_AsyncTransport if aio else _Transport)(
        *(bodies or (b"\xa1\x62id\x62n1",))
    )
    config_class = package.AsyncFieldNotesConfig if aio else package.FieldNotesConfig
    config = config_class.resolve(
        transport=transport,
        retry_strategy=SimpleRetryStrategy(max_attempts=1),
        **overrides,
    )
    if aio:
        config = asyncio.run(config)
    client = package.AsyncFieldNotesClient if aio else package.FieldNotesClient
    return client(config), transport


def _call(aio: bool, call: Any) -> Any:
    return asyncio.run(call) if aio else call


_ENDPOINT = "https://notes.example.com"


@pytest.mark.parametrize("aio", [False, True])
def test_api_key_auth_signs_by_operation(
    features: ModuleType, aio: bool, aws_env: pytest.MonkeyPatch
) -> None:
    client, transport = _client(features, aio, endpoint_uri=_ENDPOINT, api_key="key")
    _call(aio, client.get_thing(name="a"))
    _call(aio, client.echo())
    _call(aio, client.ping())
    get_thing, echo, ping = transport.requests
    assert get_thing.fields["Authorization"].values == ["ApiKey key"]
    # @optionalAuth signs with the first supported scheme.
    assert echo.fields["Authorization"].values == ["ApiKey key"]
    # @auth([]) leaves only noAuth, so the request is unsigned.
    assert "Authorization" not in ping.fields


@pytest.mark.parametrize("aio", [False, True])
def test_api_key_auth_requires_a_key(
    features: ModuleType, aio: bool, aws_env: pytest.MonkeyPatch
) -> None:
    client, transport = _client(features, aio, endpoint_uri=_ENDPOINT)
    with pytest.raises(SmithyIdentityError, match="api_key was not set"):
        _call(aio, client.get_thing(name="a"))
    _call(aio, client.ping())
    assert len(transport.requests) == 1


@pytest.mark.parametrize("aio", [False, True])
def test_aws_config_resolves_the_endpoint_from_the_environment(
    features: ModuleType, aio: bool, aws_env: pytest.MonkeyPatch
) -> None:
    aws_env.setenv("AWS_ENDPOINT_URL_FIELD_NOTES", _ENDPOINT)
    client, transport = _client(features, aio, sdk_ua_app_id="jotter")
    output = _call(aio, client.put_note(text="hi"))
    assert output.id == "n1"
    (request,) = transport.requests
    assert request.destination.host == "notes.example.com"
    user_agent = request.fields["User-Agent"].as_string()
    assert "api/Field_Notes#0.0.1" in user_agent
    assert "app/jotter" in user_agent


@pytest.mark.parametrize("aio", [False, True])
def test_aws_config_rejects_unknown_fields(
    features: ModuleType, aio: bool, aws_env: pytest.MonkeyPatch
) -> None:
    config_class = features.AsyncFieldNotesConfig if aio else features.FieldNotesConfig
    with pytest.raises(Exception, match="nope"):
        _call(aio, config_class.resolve(nope=1))
    with pytest.raises(ConfigError, match="cannot be constructed directly"):
        config_class()


def test_aws_client_resolves_its_own_config(
    features: ModuleType, aws_env: pytest.MonkeyPatch
) -> None:
    (Path(os.environ["AWS_CONFIG_FILE"])).write_text(
        "[default]\nendpoint_url = https://profile.example.com\n"
    )
    transport = _Transport(b"\xa0")

    def use_transport(config: Any) -> None:
        config.transport = transport

    client = features.FieldNotesClient(plugins=[use_transport])
    client.put_note(text="hi")
    (request,) = transport.requests
    assert request.destination.host == "profile.example.com"


@pytest.mark.parametrize("aio", [False, True])
def test_snapshot_clients_send_modeled_request_checksums(
    features: ModuleType, aio: bool, aws_env: pytest.MonkeyPatch
) -> None:
    client, transport = _client(
        features,
        aio,
        endpoint_uri=_ENDPOINT,
        aws_access_key_id="AKIDEXAMPLE",
        aws_secret_access_key="secret",
    )
    _call(aio, client.put_note(text="hi", checksum_algorithm="SHA256"))
    (request,) = transport.requests
    assert request.fields["x-amz-checksum-sha256"].as_string()
    # Both settings default to when_supported.
    assert client._config.request_checksum_calculation == "when_supported"
    assert client._config.response_checksum_validation == "when_supported"


@pytest.mark.parametrize("aio", [False, True])
def test_sigv4_signs_with_configured_credentials(
    features: ModuleType, aio: bool, aws_env: pytest.MonkeyPatch
) -> None:
    client, transport = _client(
        features,
        aio,
        endpoint_uri=_ENDPOINT,
        aws_access_key_id="AKIDEXAMPLE",
        aws_secret_access_key="secret",
    )
    _call(aio, client.put_note(text="hi"))
    (request,) = transport.requests
    authorization = request.fields["Authorization"].as_string()
    assert authorization.startswith("AWS4-HMAC-SHA256 Credential=AKIDEXAMPLE/")
    assert "/us-west-2/fieldnotes/aws4_request" in authorization


@pytest.mark.parametrize("aio", [False, True])
def test_sigv4_clients_default_to_the_credentials_chain(
    features: ModuleType, aio: bool, aws_env: pytest.MonkeyPatch
) -> None:
    client, transport = _client(features, aio, endpoint_uri=_ENDPOINT)
    _call(aio, client.put_note(text="hi"))
    (request,) = transport.requests
    authorization = request.fields["Authorization"].as_string()
    assert "Credential=AKIDFROMENV/" in authorization


@pytest.mark.parametrize("aio", [False, True])
def test_bearer_auth_sends_the_configured_token(
    features: ModuleType, aio: bool, aws_env: pytest.MonkeyPatch
) -> None:
    client, transport = _client(features, aio, endpoint_uri=_ENDPOINT, token="t0k3n")
    _call(aio, client.get_note(id="n1"))
    # SigV4 stays the default for operations that do not choose bearer auth.
    _call(aio, client.put_note(text="hi"))
    get_note, put_note = transport.requests
    assert get_note.fields["Authorization"].as_string() == "Bearer t0k3n"
    assert put_note.fields["Authorization"].as_string().startswith("AWS4-HMAC-SHA256")


@pytest.mark.parametrize("aio", [False, True])
def test_bearer_clients_default_to_the_token_chain(
    features: ModuleType, aio: bool, aws_env: pytest.MonkeyPatch
) -> None:
    # No token provider is installed here, so the chain, not the static resolver,
    # reports the miss.
    client, transport = _client(features, aio, endpoint_uri=_ENDPOINT)
    with pytest.raises(IdentityChainError, match="No identity providers"):
        _call(aio, client.get_note(id="n1"))
    assert transport.requests == []
    chain = AsyncIdentityChain if aio else IdentityChain
    assert isinstance(client._config.token_identity_resolver, chain)


@pytest.fixture(scope="module")
def handwritten() -> Iterator[ModuleType]:
    source = _ROOT / "codegen-output/my-handwritten-model/src"
    name = "my_handwritten_model"

    def owned(module: str) -> bool:
        return module == name or module.startswith(name + ".")

    # Another copy may already be imported, such as an installed package.
    saved = {
        module: sys.modules.pop(module)
        for module in tuple(sys.modules)
        if owned(module)
    }
    sys.path.insert(0, str(source))
    try:
        yield importlib.import_module(name)
    finally:
        sys.path.remove(str(source))
        for module in tuple(sys.modules):
            if owned(module):
                del sys.modules[module]
        sys.modules.update(saved)


# CBOR {"items": ["a", "b"], "nextToken": "t1"}, then {"items": ["c"]}.
_PAGES = (
    b"\xa2\x65items\x82\x61a\x61b\x69nextToken\x62t1",
    b"\xa1\x65items\x81\x61c",
)


@pytest.mark.parametrize("items", [False, True], ids=["pages", "items"])
@pytest.mark.parametrize("aio", [False, True])
@pytest.mark.parametrize("generator", ["java", "native"])
def test_snapshot_paginators_follow_tokens_through_the_runtime(
    request: pytest.FixtureRequest,
    generator: str,
    aio: bool,
    items: bool,
    aws_env: pytest.MonkeyPatch,
) -> None:
    if generator == "java":
        package = request.getfixturevalue("handwritten")
        transport = (_AsyncTransport if aio else _Transport)(*_PAGES)
        config = (package.AsyncConfig if aio else package.Config)(
            endpoint_uri=_ENDPOINT,
            transport=transport,
            retry_strategy=SimpleRetryStrategy(max_attempts=1),
        )
        client_class = (
            package.AsyncMyHandwrittenModel if aio else package.MyHandwrittenModel
        )
        paginator = client_class(config).paginate_list_items(page_size=2)
    else:
        features = request.getfixturevalue("features")
        client, transport = _client(features, aio, *_PAGES, endpoint_uri=_ENDPOINT)
        paginator = client.paginate_list_notes(page_size=2)
    assert not transport.requests

    source = paginator.items() if items else paginator

    async def collect() -> list[Any]:
        return [value async for value in source]

    values = asyncio.run(collect()) if aio else list(source)
    if items:
        assert values == ["a", "b", "c"]
    else:
        assert [(page.items, page.next_token) for page in values] == [
            (["a", "b"], "t1"),
            (["c"], None),
        ]
    assert [_body(sent) for sent in transport.requests] == [
        {"pageSize": 2},
        {"pageSize": 2, "nextToken": "t1"},
    ]


def _cbor(value: dict[str, str]) -> bytes:
    """A CBOR map of short strings."""

    def text(item: str) -> bytes:
        data = item.encode()
        return (
            bytes([0x60 | len(data)]) if len(data) < 24 else bytes([0x78, len(data)])
        ) + data

    return bytes([0xA0 | len(value)]) + b"".join(
        text(key) + text(item) for key, item in value.items()
    )


class _Waiters(NamedTuple):
    """A client's waiters, and the names its fixture's model uses."""

    client: Any
    transport: _Transport
    ready: Any
    deleted: Any
    member: str
    error: str


@pytest.fixture
def sleeps(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    """Records the waiters' sleeps instead of sleeping."""
    recorded: list[float] = []

    async def sleep_async(seconds: float) -> None:
        recorded.append(seconds)

    monkeypatch.setattr(sync_waiters, "sleep", recorded.append)
    monkeypatch.setattr(async_waiters, "sleep", sleep_async)
    return recorded


def _waiters(
    request: pytest.FixtureRequest,
    generator: str,
    aio: bool,
    *bodies: Callable[[str, str], bytes | tuple[int, bytes]],
) -> _Waiters:
    if generator == "java":
        package = request.getfixturevalue("handwritten")
        member, error = "status", "smithy.python.tests.handwritten#ItemNotFound"
        transport = (_AsyncTransport if aio else _Transport)(
            *(body(member, error) for body in bodies)
        )
        config = (package.AsyncConfig if aio else package.Config)(
            endpoint_uri=_ENDPOINT,
            transport=transport,
            retry_strategy=SimpleRetryStrategy(max_attempts=1),
        )
        client_class = (
            package.AsyncMyHandwrittenModel if aio else package.MyHandwrittenModel
        )
        client = client_class(config)
        return _Waiters(
            client,
            transport,
            client.wait_until_item_ready,
            client.wait_until_item_deleted,
            member,
            error,
        )
    features = request.getfixturevalue("features")
    member, error = "state", "example.features#NoteNotFound"
    client, transport = _client(
        features,
        aio,
        *(body(member, error) for body in bodies),
        endpoint_uri=_ENDPOINT,
    )
    return _Waiters(
        client,
        transport,
        client.wait_until_note_saved,
        client.wait_until_note_deleted,
        member,
        error,
    )


def _not_found(member: str, error: str) -> tuple[int, bytes]:
    return 400, _cbor({"__type": error, "message": "gone"})


def _pending(member: str, error: str) -> bytes:
    return _cbor({member: "PENDING" if member == "status" else "DRAFT"})


def _ready(member: str, error: str) -> bytes:
    return _cbor({"id": "i1", member: "READY" if member == "status" else "SAVED"})


def _failed(member: str, error: str) -> bytes:
    return _cbor(
        {member: "FAILED" if member == "status" else "REJECTED", "reason": "disk"}
    )


@pytest.mark.parametrize("aio", [False, True])
@pytest.mark.parametrize("generator", ["java", "native"])
def test_snapshot_waiters_poll_through_the_runtime(
    request: pytest.FixtureRequest,
    generator: str,
    aio: bool,
    sleeps: list[float],
    aws_env: pytest.MonkeyPatch,
) -> None:
    waiters = _waiters(request, generator, aio, _not_found, _pending, _ready)

    output = _call(aio, waiters.ready(id="i1", max_wait_time=60))

    assert output.id == "i1"
    assert getattr(output, waiters.member) in ("READY", "SAVED")
    assert [_body(sent) for sent in waiters.transport.requests] == [{"id": "i1"}] * 3
    # Jittered between minDelay and twice it.
    assert sleeps[0] == 1 and 1 <= sleeps[1] <= 2


@pytest.mark.parametrize("aio", [False, True])
@pytest.mark.parametrize("generator", ["java", "native"])
def test_snapshot_waiters_succeed_on_an_error(
    request: pytest.FixtureRequest,
    generator: str,
    aio: bool,
    sleeps: list[float],
    aws_env: pytest.MonkeyPatch,
) -> None:
    waiters = _waiters(request, generator, aio, _ready, _not_found)

    assert _call(aio, waiters.deleted(id="i1", max_wait_time=60)) is None
    assert len(waiters.transport.requests) == 2
    assert sleeps == [2]


@pytest.mark.parametrize("aio", [False, True])
@pytest.mark.parametrize("generator", ["java", "native"])
def test_snapshot_waiters_fail_and_validate(
    request: pytest.FixtureRequest,
    generator: str,
    aio: bool,
    sleeps: list[float],
    aws_env: pytest.MonkeyPatch,
) -> None:
    waiters = _waiters(request, generator, aio, _failed)

    with pytest.raises(ValueError, match="must not be above max_delay"):
        _call(aio, waiters.ready(id="i1", max_wait_time=60, min_delay=10))
    assert waiters.transport.requests == []

    with pytest.raises(WaiterFailureError, match="failed after 1 attempt: disk"):
        _call(aio, waiters.ready({"id": "i1"}, max_wait_time=60))
    assert sleeps == []
