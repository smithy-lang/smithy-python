# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
# pyright: reportPrivateUsage=false
"""Smithy protocol test vectors run against the Python-generated client snapshots.

Vectors come from ``models/vectors``, extracted from the same assembled ASTs as the
model inputs. Each request vector calls a client method and checks the request it
sends. Each response vector feeds a response to a client method and checks the
output or error it returns.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import importlib
import json
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType
from typing import Any, cast

import pytest
from smithy_cbor import loads
from smithy_core.aio.types import AsyncBytesReader
from smithy_core.retries import SimpleRetryStrategy
from smithy_core.schemas import Schema
from smithy_core.shapes import ShapeType
from smithy_http import HTTPResponse, tuples_to_fields
from smithy_http.interfaces import HTTPRequest, HTTPRequestConfiguration
from smithy_python.clients import ClientPlan
from smithy_python.generation import ClientSettings
from smithy_python.model import load_model
from smithy_test import deep_equal

_ROOT = Path(__file__).resolve().parents[3]
_INPUTS = _ROOT / "scripts/codegen-output-py"
_PROJECTIONS: dict[str, Any] = json.loads(
    (_INPUTS / "client-projections.json").read_text()
)

# Vectors the Java-generated clients also fail. A defaulted member is a plain field
# carrying its default, so the client cannot tell an unset member from one set to
# its default, and it always serializes top-level defaults.
_EXPECTED_FAILURES = frozenset(
    {
        "RpcV2CborClientPopulatesDefaultValuesInInput",
        "RpcV2CborClientSkipsTopLevelDefaultValuesInInput",
        "RpcV2CborClientUsesExplicitlyProvidedMemberValuesOverDefaults",
        "RpcV2CborClientIgnoresNonTopLevelDefaultsOnMembersWithClientOptional",
    }
)


@dataclass(frozen=True)
class _Vector:
    projection: str
    shape_id: str
    kind: str
    case: dict[str, Any]


def _vectors() -> Iterator[Any]:
    for projection, settings in sorted(_PROJECTIONS.items()):
        path = _INPUTS / "models/vectors" / Path(settings["model"]).name
        if not path.exists():
            continue
        for shape_id, kinds in json.loads(path.read_text()).items():
            for kind, cases in sorted(kinds.items()):
                for case in cases:
                    marks = (
                        [pytest.mark.xfail(strict=True)]
                        if case["id"] in _EXPECTED_FAILURES
                        else []
                    )
                    yield pytest.param(
                        _Vector(projection, shape_id, kind, case),
                        id=f"{projection}-{case['id']}",
                        marks=marks,
                    )


@dataclass(frozen=True)
class _Client:
    package: ModuleType
    models: ModuleType
    registry: Any
    methods: dict[str, str]
    """Client method name by operation shape ID."""
    error_operations: dict[str, str]
    """The first operation, in model order, that returns each error."""
    services: tuple[str, str]
    """The sync and async client class names."""


_CLIENTS: dict[str, _Client] = {}


def _client(projection: str) -> _Client:
    if (client := _CLIENTS.get(projection)) is not None:
        return client
    settings = _PROJECTIONS[projection]
    package_name = settings["package"]
    sys.path.insert(0, str(_ROOT / "codegen-output-py" / projection / "src"))
    try:
        package = importlib.import_module(package_name)
        models = importlib.import_module(f"{package_name}.models")
    finally:
        sys.path.pop(0)
    plan = ClientPlan.from_model(
        load_model(json.loads((_INPUTS / settings["model"]).read_text())),
        ClientSettings(package_name, settings["version"], None),
        service_id=settings["service"],
    )
    methods = {str(o.operation.id): o.method_name for o in plan.operations}
    error_operations: dict[str, str] = {}
    for operation in plan.operations:
        for error in operation.operation.errors:
            error_operations.setdefault(str(error), str(operation.operation.id))
    services = (plan.symbols.service_name, plan.symbols.aio_service_name)
    client = _Client(
        package, models, models._registry, methods, error_operations, services
    )
    _CLIENTS[projection] = client
    return client


class _Sent(Exception):
    """Raised by the request transport to stop the call once it is sent."""

    def __init__(self, request: HTTPRequest) -> None:
        self.request = request


class _Transport:
    TIMEOUT_EXCEPTIONS = ()

    def __init__(self, response: HTTPResponse | None) -> None:
        self.response = response

    def __deepcopy__(self, memo: dict[int, Any]) -> _Transport:
        return self

    def send(
        self,
        request: HTTPRequest,
        *,
        request_config: HTTPRequestConfiguration | None = None,
    ) -> HTTPResponse:
        if self.response is None:
            raise _Sent(request)
        return self.response


class _AsyncTransport(_Transport):
    async def send(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        request: HTTPRequest,
        *,
        request_config: HTTPRequestConfiguration | None = None,
    ) -> HTTPResponse:
        response = _Transport.send(self, request)
        body: Any = response.body
        return HTTPResponse(
            status=response.status,
            fields=response.fields,
            body=AsyncBytesReader(body),
        )


def _call(
    client: _Client,
    operation: str,
    request: dict[str, Any],
    response: HTTPResponse | None,
    *,
    aio: bool,
) -> Any:
    config = (client.package.AsyncConfig if aio else client.package.Config)(
        endpoint_uri="https://example.com",
        transport=(_AsyncTransport if aio else _Transport)(response),
        retry_strategy=SimpleRetryStrategy(max_attempts=1),
    )
    service = client.services[1 if aio else 0]
    method = getattr(
        getattr(client.package, service)(config), client.methods[operation]
    )
    result = method(request)
    return asyncio.run(result) if aio else result


def _operation_schema(client: _Client, operation: str) -> Any:
    name = client.methods[operation].upper()
    return getattr(client.models, name)


def _scalar(schema: Schema, value: Any) -> Any:
    match schema.shape_type:
        case ShapeType.BLOB:
            return value.encode() if isinstance(value, str) else value
        case ShapeType.TIMESTAMP:
            return datetime.fromtimestamp(value, UTC)
        case ShapeType.FLOAT | ShapeType.DOUBLE:
            return float(value)
        case _:
            return value


def _target(member: Schema) -> Schema:
    return member.expect_member_target()


def _input(registry: Any, schema: Schema, value: Any) -> Any:
    """A vector's params as the dictionary form a client method takes."""
    match schema.shape_type:
        case ShapeType.STRUCTURE:
            members, _, _ = schema.get_extension(registry._input_plan)
            keys = {m.expect_member_name(): key for key, m in members.items()}
            return {
                keys[name]: _input(registry, _target(members[keys[name]]), item)
                for name, item in value.items()
            }
        case ShapeType.UNION:
            ((name, item),) = value.items()
            member = schema.members[name]
            key = registry._field_names(schema)[member.expect_member_index()]
            return {key: _input(registry, _target(member), item)}
        case ShapeType.LIST:
            element = _target(schema.members["member"])
            return [None if v is None else _input(registry, element, v) for v in value]
        case ShapeType.MAP:
            entry = _target(schema.members["value"])
            return {
                k: None if v is None else _input(registry, entry, v)
                for k, v in value.items()
            }
        case _:
            return _scalar(schema, value)


def _output(registry: Any, schema: Schema, value: Any) -> Any:
    """A vector's params as the model a client method returns."""
    match schema.shape_type:
        case ShapeType.STRUCTURE:
            names = registry._field_names(schema)
            kwargs = {
                names[member.expect_member_index()]: _output(
                    registry, _target(member), value[name]
                )
                for name, member in schema.members.items()
                if name in value
            }
            return registry.build(registry._target_name(schema))(**kwargs)
        case ShapeType.UNION:
            ((name, item),) = value.items()
            variant = registry._union_variant_name(registry._target_name(schema), name)
            return registry.build(variant)(
                _output(registry, _target(schema.members[name]), item)
            )
        case ShapeType.LIST:
            element = _target(schema.members["member"])
            return [None if v is None else _output(registry, element, v) for v in value]
        case ShapeType.MAP:
            entry = _target(schema.members["value"])
            return {
                k: None if v is None else _output(registry, entry, v)
                for k, v in value.items()
            }
        case _:
            return _scalar(schema, value)


def _body(request: HTTPRequest) -> bytes:
    body: Any = request.body
    if isinstance(body, bytes | bytearray):
        return bytes(body)
    data = body.read() if body is not None else b""
    return asyncio.run(data) if asyncio.iscoroutine(data) else data


def _decoded(body: bytes) -> Any:
    return loads(body) if body else {}


@pytest.mark.parametrize("aio", [False, True], ids=["sync-client", "async-client"])
@pytest.mark.parametrize("vector", list(_vectors()))
def test_protocol_vector(vector: _Vector, aio: bool) -> None:
    client = _client(vector.projection)
    case = vector.case
    if vector.kind == "requests":
        _check_request(client, vector.shape_id, case, aio=aio)
    else:
        _check_response(client, vector.shape_id, case, aio=aio)


def _check_request(
    client: _Client, operation: str, case: dict[str, Any], *, aio: bool
) -> None:
    schema = _operation_schema(client, operation).input_schema
    request = _input(client.registry, schema, case.get("params", {}))
    with pytest.raises(Exception) as raised:
        _call(client, operation, request, None, aio=aio)
    # The pipeline may wrap the transport's exception.
    error: BaseException | None = raised.value
    while error is not None and not isinstance(error, _Sent):
        error = error.__cause__ or error.__context__
    assert isinstance(error, _Sent), raised.value
    actual = error.request

    assert actual.method == case["method"]
    assert actual.destination.path == case["uri"]
    for key, value in case.get("headers", {}).items():
        assert value in actual.fields[key].values
    for key in case.get("forbidHeaders", ()):
        with pytest.raises(KeyError):
            actual.fields[key]
    for key in case.get("requireHeaders", ()):
        assert actual.fields[key].values
    if "body" in case:
        expected = base64.b64decode(case["body"])
        assert deep_equal(_decoded(_body(actual)), _decoded(expected))


def _check_response(
    client: _Client, shape_id: str, case: dict[str, Any], *, aio: bool
) -> None:
    body = base64.b64decode(case["body"]) if case.get("body") else b""
    response = HTTPResponse(
        status=case["code"],
        fields=tuples_to_fields(list(case.get("headers", {}).items())),
        body=body,
    )
    params = case.get("params", {})
    if shape_id not in client.methods:
        # A response vector on an error shape is returned by an operation.
        operation = client.error_operations[shape_id]
        error_schema = next(
            schema
            for schema in _operation_schema(client, operation).error_schemas
            if str(schema.id) == shape_id
        )
        expected = _output(client.registry, error_schema, params)
        error_type = cast("type[Exception]", type(expected))
        with pytest.raises(error_type) as raised:
            _call(client, operation, {}, response, aio=aio)
        for name in params:
            field = client.registry._field_names(error_schema)[
                error_schema.members[name].expect_member_index()
            ]
            assert deep_equal(getattr(raised.value, field), getattr(expected, field))
        return

    output_schema = _operation_schema(client, shape_id).output_schema
    expected = _output(client.registry, output_schema, params)
    actual = _call(client, shape_id, {}, response, aio=aio)
    assert deep_equal(actual, expected), (actual, expected)


def test_vectors_match_their_provenance() -> None:
    provenance = json.loads((_INPUTS / "models/provenance.json").read_text())
    for path in sorted((_INPUTS / "models/vectors").iterdir()):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert provenance[path.stem]["vectors_sha256"] == digest


def test_every_client_vector_is_collected() -> None:
    # 29 request and 43 response vectors; the Java client runs the same 72.
    assert len(list(_vectors())) == 72
