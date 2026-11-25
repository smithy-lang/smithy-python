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
from decimal import Decimal
from pathlib import Path
from types import ModuleType
from typing import Any, cast
from urllib.parse import parse_qsl

import pytest
from smithy_aws_core.aio.identity.static import AsyncStaticCredentialsResolver
from smithy_aws_core.identity.components import AWSCredentialsIdentity
from smithy_aws_core.identity.static import StaticCredentialsResolver
from smithy_cbor import loads as cbor_loads
from smithy_core.aio.types import AsyncBytesReader
from smithy_core.documents import Document
from smithy_core.retries import SimpleRetryStrategy
from smithy_core.schemas import Schema
from smithy_core.shapes import ShapeType
from smithy_core.traits import EnumValueTrait, HTTPHeaderTrait
from smithy_http import HTTPResponse, tuples_to_fields
from smithy_http.interfaces import HTTPRequest, HTTPRequestConfiguration
from smithy_http.utils import split_header
from smithy_python import aws
from smithy_python.clients import ClientPlan
from smithy_python.generation import ClientSettings
from smithy_python.integrations import ClientNames
from smithy_python.model import load_model
from smithy_test import deep_equal, xml_equal

_ROOT = Path(__file__).resolve().parents[3]
_INPUTS = _ROOT / "scripts/codegen-output-py"
_PROJECTIONS: dict[str, Any] = json.loads(
    (_INPUTS / "client-projections.json").read_text()
)

# Vectors the Java-generated clients also fail, by case ID. A defaulted member is a
# plain field carrying its default, so the client cannot tell an unset member from
# one set to its default, and it always serializes top-level defaults. Clients don't
# support the httpChecksumRequired or requestCompression traits yet.
_EXPECTED_FAILURES = frozenset(
    {
        "AwsJson10ClientPopulatesDefaultValuesInInput",
        "AwsJson10ClientSkipsTopLevelDefaultValuesInInput",
        "AwsJson10ClientUsesExplicitlyProvidedMemberValuesOverDefaults",
        "AwsJson10ClientIgnoresNonTopLevelDefaultsOnMembersWithClientOptional",
        "SDKAppliedContentEncoding_awsJson1_0",
        "SDKAppendsGzipAndIgnoresHttpProvidedEncoding_awsJson1_0",
        "SDKAppliedContentEncoding_awsJson1_1",
        "SDKAppendsGzipAndIgnoresHttpProvidedEncoding_awsJson1_1",
        "RestJsonClientPopulatesDefaultValuesInInput",
        "RestJsonClientSkipsTopLevelDefaultValuesInInput",
        "RestJsonClientUsesExplicitlyProvidedMemberValuesOverDefaults",
        "RestJsonClientIgnoresNonTopLevelDefaultsOnMembersWithClientOptional",
        "RestJsonHttpChecksumRequired",
        "SDKAppliedContentEncoding_restJson1",
        "SDKAppendedGzipAfterProvidedEncoding_restJson1",
        "SDKAppliedContentEncoding_restXml",
        "SDKAppendedGzipAfterProvidedEncoding_restXml",
        "SDKAppliedContentEncoding_awsQuery",
        "SDKAppendsGzipAndIgnoresHttpProvidedEncoding_awsQuery",
        "SDKAppliedContentEncoding_ec2Query",
        "SDKAppendsGzipAndIgnoresHttpProvidedEncoding_ec2Query",
        "RpcV2CborClientPopulatesDefaultValuesInInput",
        "RpcV2CborClientSkipsTopLevelDefaultValuesInInput",
        "RpcV2CborClientUsesExplicitlyProvidedMemberValuesOverDefaults",
        "RpcV2CborClientIgnoresNonTopLevelDefaultsOnMembersWithClientOptional",
        "RpcV2JsonRequestClientPopulatesDefaultValuesInInput",
        "RpcV2JsonRequestClientSkipsTopLevelDefaultValuesInInput",
        "RpcV2JsonRequestClientUsesExplicitlyProvidedMemberValuesOverDefaults",
        "RpcV2JsonRequestClientIgnoresNonTopLevelDefaultsOnMembersWithClientOptional",
    }
)

# Response vectors that share a case ID with a passing request vector. The client
# reads an empty blob payload as b"", not as unset. The Java tests expect b"".
_EXPECTED_RESPONSE_FAILURES = frozenset(
    {"RestJsonHttpPayloadTraitsWithNoBlobBody", "HttpPayloadTraitsWithNoBlobBody"}
)

# How request bodies of each media type are decoded for comparison. Other bodies
# compare as bytes, except XML, which is compared parsed. JSON numbers are read as
# Decimal, so big numbers compare exactly.
_BODY_DECODERS: dict[str, Any] = {
    "application/cbor": cbor_loads,
    "application/json": lambda body: json.loads(body, parse_float=Decimal),
}


_CREDENTIALS = AWSCredentialsIdentity(
    access_key_id="test-access-key-id", secret_access_key="test-secret-access-key"
)


def _projection_model(settings: dict[str, Any]) -> dict[str, Any]:
    """The projection's model without the operations it omits, as generate.py
    generates it."""
    model: dict[str, Any] = json.loads((_INPUTS / settings["model"]).read_text())
    omitted = set(settings.get("omitOperations", ()))
    service = model["shapes"][settings["service"]]
    service["operations"] = [
        operation
        for operation in service.get("operations", ())
        if operation["target"] not in omitted
    ]
    return model


def _vector_body(case: dict[str, Any]) -> bytes:
    """A vector's body as bytes. Binary media types are written in base64."""
    body = case.get("body", "")
    if case.get("bodyMediaType") == "application/cbor":
        return base64.b64decode(body)
    return body.encode()


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
        vectors = json.loads(path.read_text(), parse_float=Decimal)
        omitted = set(settings.get("omitOperations", ()))
        for shape_id, kinds in vectors.items():
            if shape_id in omitted:
                continue
            for kind, cases in sorted(kinds.items()):
                for case in cases:
                    failing = case["id"] in _EXPECTED_FAILURES or (
                        kind == "responses"
                        and case["id"] in _EXPECTED_RESPONSE_FAILURES
                    )
                    marks = [pytest.mark.xfail(strict=True)] if failing else []
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
    names: ClientNames
    aws: bool
    """Whether the configs resolve from the environment, with AWS credentials."""


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
        load_model(_projection_model(settings)),
        ClientSettings(package_name, settings["version"], None),
        service_id=settings["service"],
    )
    methods = {str(o.operation.id): o.method_name for o in plan.operations}
    error_operations: dict[str, str] = {}
    for operation in plan.operations:
        for error in operation.operation.errors:
            error_operations.setdefault(str(error), str(operation.operation.id))
    service = plan.selection.service
    assert service is not None
    names = ClientNames(
        client=plan.symbols.service_name,
        config="Config",
        async_client=plan.symbols.aio_service_name,
        async_config="AsyncConfig",
    )
    integrations = [i for i in aws.AWS_INTEGRATIONS if i.matches(service)]
    for integration in integrations:
        names = integration.client_names(service, names)
    client = _Client(
        package,
        models,
        models._registry,
        methods,
        error_operations,
        names,
        aws=bool(integrations),
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
    host: str = "example.com",
) -> Any:
    names = client.names
    config_type = getattr(client.package, names.async_config if aio else names.config)
    service = getattr(client.package, names.async_client if aio else names.client)
    fields: dict[str, Any] = {
        "endpoint_uri": f"https://{host}",
        "transport": (_AsyncTransport if aio else _Transport)(response),
        "retry_strategy": SimpleRetryStrategy(max_attempts=1),
    }
    new_config = config_type
    if client.aws:
        # An AWS config resolves from the environment, so it gets a region and
        # credentials.
        new_config = config_type.resolve
        fields["region"] = "us-east-1"
        fields["aws_credentials_identity_resolver"] = (
            AsyncStaticCredentialsResolver if aio else StaticCredentialsResolver
        )(_CREDENTIALS)
    if not aio:
        return getattr(service(new_config(**fields)), client.methods[operation])(
            request
        )

    async def run() -> Any:
        config = new_config(**fields)
        if client.aws:
            config = await config
        return await getattr(service(config), client.methods[operation])(request)

    return asyncio.run(run())


def _operation_schema(client: _Client, operation: str) -> Any:
    name = client.methods[operation].upper()
    return getattr(client.models, name)


def _scalar(schema: Schema, value: Any) -> Any:
    match schema.shape_type:
        case ShapeType.BLOB:
            return value.encode() if isinstance(value, str) else value
        case ShapeType.TIMESTAMP:
            # Split exactly, so fractional seconds don't round through a float.
            seconds = Decimal(value)
            whole = int(seconds)
            micros = int((seconds - whole) * 1_000_000)
            return datetime.fromtimestamp(whole, UTC).replace(microsecond=micros)
        case ShapeType.FLOAT | ShapeType.DOUBLE:
            return float(value)
        case ShapeType.BIG_DECIMAL:
            return Decimal(value)
        case ShapeType.DOCUMENT:
            return Document(value)
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


def _placeholder(registry: Any, schema: Schema) -> Any:
    """The smallest input the client accepts, as a response vector's request."""
    match schema.shape_type:
        case ShapeType.STRUCTURE:
            members, required, _ = schema.get_extension(registry._input_plan)
            return {
                key: _placeholder(registry, _target(members[key])) for key in required
            }
        case ShapeType.UNION:
            member = schema.members_by_index[0]
            key = registry._field_names(schema)[member.expect_member_index()]
            return {key: _placeholder(registry, _target(member))}
        case ShapeType.LIST:
            return []
        case ShapeType.MAP:
            return {}
        case ShapeType.ENUM | ShapeType.INT_ENUM:
            trait = schema.members_by_index[0].get_trait(EnumValueTrait)
            assert trait is not None
            return trait.value
        case ShapeType.BOOLEAN:
            return False
        case ShapeType.STRING:
            return "x"
        case ShapeType.BLOB:
            return b""
        case ShapeType.TIMESTAMP:
            return datetime.fromtimestamp(0, UTC)
        case ShapeType.DOCUMENT:
            return Document(None)
        case _:
            return _scalar(schema, 0)


def _output(registry: Any, schema: Schema, value: Any) -> Any:
    """A vector's params as the model a client method returns."""
    if value is None:
        return None
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


def _decoded(media_type: str, body: bytes) -> Any:
    return _BODY_DECODERS[media_type](body) if body else {}


@pytest.mark.parametrize("aio", [False, True], ids=["sync-client", "async-client"])
@pytest.mark.parametrize("vector", list(_vectors()))
def test_protocol_vector(
    vector: _Vector, aio: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Vectors expect this token when the client fills an idempotency token.
    monkeypatch.setattr(
        "smithy_core._pipeline._default_idempotency_token",
        lambda: "00000000-0000-4000-8000-000000000000",
    )
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
    # A vector's host may have a path, which prefixes the request's path.
    host = case.get("host", "example.com")
    with pytest.raises(Exception) as raised:
        _call(client, operation, request, None, aio=aio, host=host)
    # The pipeline may wrap the transport's exception.
    error: BaseException | None = raised.value
    while error is not None and not isinstance(error, _Sent):
        error = error.__cause__ or error.__context__
    assert isinstance(error, _Sent), raised.value
    actual = error.request

    assert actual.method == case["method"]
    assert actual.destination.path == case["uri"]
    assert actual.destination.host == case.get("resolvedHost", host).split("/")[0]
    query = actual.destination.query
    segments = query.split("&") if query else []
    for segment in case.get("queryParams", ()):
        assert segment in segments, (segment, segments)
        segments.remove(segment)
    keys = [key.lower() for key, _ in parse_qsl(query or "", keep_blank_values=True)]
    for key in case.get("forbidQueryParams", ()):
        assert key.lower() not in keys
    for key in case.get("requireQueryParams", ()):
        assert key.lower() in keys
    lists = _list_headers(schema)
    for key, value in case.get("headers", {}).items():
        # A vector joins a list header's values, and an empty list sends none.
        expected = (
            split_header(value, handle_unquoted_http_date=lists[key.lower()])
            if key.lower() in lists
            else [value]
        )
        for item in expected:
            assert item in actual.fields[key].values, (key, item)
    for key in case.get("forbidHeaders", ()):
        with pytest.raises(KeyError):
            actual.fields[key]
    for key in case.get("requireHeaders", ()):
        assert actual.fields[key].values
    if "body" in case:
        media_type = case.get("bodyMediaType")
        actual_body, expected_body = _body(actual), _vector_body(case)
        if media_type == "application/xml":
            assert xml_equal(actual_body, expected_body)
        elif media_type in _BODY_DECODERS:
            assert deep_equal(
                _decoded(media_type, actual_body), _decoded(media_type, expected_body)
            )
        else:
            assert actual_body == expected_body


def _list_headers(schema: Schema) -> dict[str, bool]:
    """Whether each list-bound header, by lowercase name, lists timestamps."""
    return {
        trait.key.lower(): _target(_target(member).members["member"]).shape_type
        is ShapeType.TIMESTAMP
        for member in schema.members.values()
        if (trait := member.get_trait(HTTPHeaderTrait)) is not None
        and _target(member).shape_type is ShapeType.LIST
    }


def _check_response(
    client: _Client, shape_id: str, case: dict[str, Any], *, aio: bool
) -> None:
    body = _vector_body(case)
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
        request = _placeholder(
            client.registry, _operation_schema(client, operation).input_schema
        )
        with pytest.raises(error_type) as raised:
            _call(client, operation, request, response, aio=aio)
        for name in params:
            field = client.registry._field_names(error_schema)[
                error_schema.members[name].expect_member_index()
            ]
            assert deep_equal(getattr(raised.value, field), getattr(expected, field))
        return

    schema = _operation_schema(client, shape_id)
    expected = _output(client.registry, schema.output_schema, params)
    request = _placeholder(client.registry, schema.input_schema)
    actual = _call(client, shape_id, request, response, aio=aio)
    assert deep_equal(actual, expected), (actual, expected)


def test_vectors_match_their_provenance() -> None:
    provenance = json.loads((_INPUTS / "models/provenance.json").read_text())
    for path in sorted((_INPUTS / "models/vectors").iterdir()):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert provenance[path.stem]["vectors_sha256"] == digest


def test_every_client_vector_is_collected() -> None:
    # The Java clients run the same vectors: rpcv2Cbor has 29 request and 43
    # response vectors, and rpcv2Json has 34 and 39. restJson1 has 244, less the 8
    # of the streaming operations the client omits. awsJson1_0 has 67, awsJson1_1
    # has 118, and the query-compatible awsJson1_0 service has 3. restXml has
    # 178, and the restXml service with a namespace has 2. awsQuery has 77, and
    # ec2Query has 59.
    assert len(list(_vectors())) == (72 + 73 + 236 + 67 + 118 + 3 + 178 + 2 + 77 + 59)
