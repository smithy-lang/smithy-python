#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""Unit tests for the smithy.protocols#rpcv2Json client protocol.

Schemas and shapes are built by hand so the tests exercise the protocol's HTTP/RPC
framing, codec configuration, and error resolution without generated code.
"""

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, ClassVar, Self

import pytest

pytest.importorskip("smithy_json")

from smithy_core import URI
from smithy_core.aio.interfaces import ProtocolSettings
from smithy_core.aio.types import AsyncBytesReader
from smithy_core.deserializers import ShapeDeserializer
from smithy_core.documents import TypeRegistry
from smithy_core.exceptions import (
    CallError,
    Fault,
    MissingDependencyError,
    ModeledError,
    SerializationError,
)
from smithy_core.prelude import (
    BIG_DECIMAL,
    BIG_INTEGER,
    INTEGER,
    STRING,
    TIMESTAMP,
    UNIT,
)
from smithy_core.schemas import APIOperation, Schema
from smithy_core.serializers import ShapeSerializer
from smithy_core.shapes import ShapeID, ShapeType
from smithy_core.traits import (
    ORIGINAL_SHAPE_ID,
    DynamicTrait,
    ErrorTrait,
    JSONNameTrait,
    RpcV2JsonTrait,
    StreamingTrait,
    TimestampFormatTrait,
)
from smithy_core.types import TypedProperties
from smithy_http import Fields, tuples_to_fields
from smithy_http.aio import HTTPRequest, HTTPResponse
from smithy_http.aio import interfaces as http_interfaces
from smithy_http.aio import protocols as protocols_module
from smithy_http.aio.protocols import AsyncRpcV2JsonClientProtocol
from smithy_json import JSONCodec

_NAMESPACE = "smithy.example"
_SERVICE_NAME = "JsonService"

# --- Schemas ---------------------------------------------------------------------

_INPUT_SCHEMA = Schema.collection(
    id=ShapeID("smithy.example#OpInput"),
    members={
        "name": {"target": STRING},
        "bigInt": {"target": BIG_INTEGER},
        "bigDec": {"target": BIG_DECIMAL},
        # @timestampFormat MUST NOT be respected: this still writes epoch-seconds.
        "when": {
            "target": TIMESTAMP,
            "traits": [TimestampFormatTrait("date-time")],
        },
        # @jsonName is not part of rpcv2Json: the member name is used on the wire.
        "renamed": {"target": STRING, "traits": [JSONNameTrait("otherName")]},
    },
)

_OUTPUT_SCHEMA = Schema.collection(
    id=ShapeID("smithy.example#OpOutput"),
    members={
        "name": {"target": STRING},
        "count": {"target": INTEGER},
        "bigInt": {"target": BIG_INTEGER},
    },
)

_MY_ERROR_SCHEMA = Schema.collection(
    id=ShapeID("smithy.example#MyError"),
    traits=[ErrorTrait("client")],
    members={"message": {"target": STRING}},
)

_OTHER_ERROR_SCHEMA = Schema.collection(
    id=ShapeID("smithy.example#OtherError"),
    traits=[ErrorTrait("server")],
    members={"message": {"target": STRING}},
)

# Codegen synthesizes a wrapper struct for a unit input/output, tagged with
# smithy.synthetic#originalShapeId = smithy.api#Unit.
_SYNTHETIC_UNIT_SCHEMA = Schema.collection(
    id=ShapeID("smithy.example#OpSyntheticUnit"),
    traits=[DynamicTrait(id=ORIGINAL_SHAPE_ID, document_value=str(UNIT.id))],
    members={},
)

_EVENT = Schema.collection(
    id=ShapeID("smithy.example#Event"),
    members={"body": {"target": STRING}},
)
_EVENT_STREAM = Schema.collection(
    id=ShapeID("smithy.example#EventStream"),
    shape_type=ShapeType.UNION,
    traits=[StreamingTrait()],
    members={"event": {"target": _EVENT}},
)
_STREAM_OUTPUT_SCHEMA = Schema.collection(
    id=ShapeID("smithy.example#StreamOutput"),
    members={"stream": {"target": _EVENT_STREAM}},
)

_UNION_SCHEMA = Schema.collection(
    id=ShapeID("smithy.example#MyUnion"),
    shape_type=ShapeType.UNION,
    members={
        "str": {"target": STRING},
        "num": {"target": INTEGER},
    },
)

# --- Shapes ----------------------------------------------------------------------


class OpInput:
    def __init__(
        self,
        *,
        name: str | None = None,
        big_int: int | None = None,
        big_dec: Decimal | None = None,
        when: datetime | None = None,
        renamed: str | None = None,
    ) -> None:
        self.name = name
        self.big_int = big_int
        self.big_dec = big_dec
        self.when = when
        self.renamed = renamed

    def serialize(self, serializer: ShapeSerializer) -> None:
        with serializer.begin_struct(_INPUT_SCHEMA) as s:
            members = _INPUT_SCHEMA.members
            if self.name is not None:
                s.write_string(members["name"], self.name)
            if self.big_int is not None:
                s.write_big_integer(members["bigInt"], self.big_int)
            if self.big_dec is not None:
                s.write_big_decimal(members["bigDec"], self.big_dec)
            if self.when is not None:
                s.write_timestamp(members["when"], self.when)
            if self.renamed is not None:
                s.write_string(members["renamed"], self.renamed)

    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> Self:
        raise NotImplementedError


class OpOutput:
    def __init__(
        self, *, name: str | None = None, count: int = 0, big_int: int | None = None
    ) -> None:
        self.name = name
        # Codegen fills defaults in the constructor; absent members keep them.
        self.count = count
        self.big_int = big_int

    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> Self:
        kwargs: dict[str, Any] = {}

        def _consume(schema: Schema, de: ShapeDeserializer) -> None:
            match schema.expect_member_index():
                case 0:
                    kwargs["name"] = de.read_string(schema)
                case 1:
                    kwargs["count"] = de.read_integer(schema)
                case 2:
                    kwargs["big_int"] = de.read_big_integer(schema)
                case _:
                    raise AssertionError(f"unexpected member {schema.id}")

        deserializer.read_struct(_OUTPUT_SCHEMA, _consume)
        return cls(**kwargs)

    def serialize(self, serializer: ShapeSerializer) -> None:
        raise NotImplementedError


class UnitShape:
    """Stands in for a unit input/output; serializes as an empty struct."""

    def __init__(self, schema: Schema = UNIT) -> None:
        self._schema = schema

    def serialize(self, serializer: ShapeSerializer) -> None:
        with serializer.begin_struct(self._schema):
            pass

    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> Self:
        deserializer.read_struct(UNIT, lambda schema, de: None)
        return cls()


def _error_deserializer(schema: Schema):  # type: ignore[no-untyped-def]
    def _deserialize(cls: type[Any], deserializer: ShapeDeserializer) -> Any:
        kwargs: dict[str, Any] = {}

        def _consume(member: Schema, de: ShapeDeserializer) -> None:
            if member.expect_member_index() == 0:
                kwargs["message"] = de.read_string(member)

        deserializer.read_struct(schema, _consume)
        return cls(**kwargs)

    return _deserialize


@dataclass(kw_only=True)
class MyError(ModeledError):
    fault: Fault = "client"

    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> Self:
        return _error_deserializer(_MY_ERROR_SCHEMA)(cls, deserializer)


@dataclass(kw_only=True)
class OtherError(ModeledError):
    fault: Fault = "server"

    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> Self:
        return _error_deserializer(_OTHER_ERROR_SCHEMA)(cls, deserializer)


_ERROR_REGISTRY = TypeRegistry(
    {_MY_ERROR_SCHEMA.id: MyError, _OTHER_ERROR_SCHEMA.id: OtherError}
)


# Union deserializer following the pattern UnionGenerator emits: one variant per
# member index, an Unknown fallback for unrecognized members, and a hard failure if
# more than one member (or none) is seen.
@dataclass
class MyUnionStr:
    value: str


@dataclass
class MyUnionNum:
    value: int


@dataclass
class MyUnionUnknown:
    tag: str


type MyUnion = MyUnionStr | MyUnionNum | MyUnionUnknown


class _MyUnionDeserializer:
    _result: MyUnion | None = None

    def deserialize(self, deserializer: ShapeDeserializer) -> MyUnion:
        self._result = None
        deserializer.read_struct(_UNION_SCHEMA, self._consumer)
        if self._result is None:
            raise SerializationError(
                "Unions must have exactly one value, but found none."
            )
        return self._result

    def _consumer(self, schema: Schema, de: ShapeDeserializer) -> None:
        match schema.expect_member_index():
            case 0:
                self._set_result(MyUnionStr(de.read_string(schema)))
            case 1:
                self._set_result(MyUnionNum(de.read_integer(schema)))
            case _:
                self._set_result(MyUnionUnknown(tag=schema.expect_member_name()))

    def _set_result(self, value: MyUnion) -> None:
        if self._result is not None:
            raise SerializationError(
                "Unions must have exactly one value, but found more than one."
            )
        self._result = value


# --- Helpers ---------------------------------------------------------------------


class _Registry:
    _TYPES: ClassVar[dict[str, type[Any]]] = {
        "OpInput": OpInput,
        "OpOutput": OpOutput,
        "Unit": UnitShape,
        "OpSyntheticUnit": UnitShape,
    }

    def build(self, name: str) -> type[Any]:
        return self._TYPES[name]


def _operation(
    *,
    name: str = "DoThing",
    input_schema: Schema = _INPUT_SCHEMA,
    output_schema: Schema = _OUTPUT_SCHEMA,
    errors: tuple[Schema, ...] = (_MY_ERROR_SCHEMA, _OTHER_ERROR_SCHEMA),
) -> APIOperation[Any, Any]:
    return APIOperation(
        static_schema=(
            ShapeType.OPERATION.value,
            _NAMESPACE,
            name,
            {},
            input_schema,
            output_schema,
            errors,
        ),
        model_registry=_Registry(),
        error_ids=tuple(e.id for e in errors),
        effective_auth_schemes=[],
    )


def _service_schema(trait: RpcV2JsonTrait | None = None) -> Schema:
    return Schema.collection(
        id=ShapeID(f"{_NAMESPACE}#{_SERVICE_NAME}"),
        shape_type=ShapeType.SERVICE,
        traits=[trait or RpcV2JsonTrait()],
    )


def _protocol(service_schema: Schema | None = None) -> AsyncRpcV2JsonClientProtocol:
    return AsyncRpcV2JsonClientProtocol(
        ProtocolSettings(
            namespace=_NAMESPACE,
            service_target=_SERVICE_NAME,
            service_schema=service_schema or _service_schema(),
        )
    )


def _serialize(
    input: Any, operation: APIOperation[Any, Any] | None = None
) -> http_interfaces.HTTPRequest:
    return _protocol().serialize_request(
        operation=operation or _operation(),
        input=input,
        endpoint=URI(host="example.com"),
        context=TypedProperties(),
    )


def _response(
    status: int,
    body: bytes = b"",
    *,
    smithy_protocol: str | None = "rpc-v2-json",
) -> HTTPResponse:
    fields: list[tuple[str, str]] = [("content-type", "application/json")]
    if smithy_protocol is not None:
        fields.append(("smithy-protocol", smithy_protocol))
    return HTTPResponse(
        status=status, fields=tuples_to_fields(fields), body=AsyncBytesReader(body)
    )


async def _deserialize(
    response: HTTPResponse, operation: APIOperation[Any, Any] | None = None
) -> Any:
    return await _protocol().deserialize_response(
        operation=operation or _operation(),
        request=HTTPRequest(
            destination=URI(host="example.com"), method="POST", fields=Fields()
        ),
        response=response,
        error_registry=_ERROR_REGISTRY,
        context=TypedProperties(),
    )


def _header(request: http_interfaces.HTTPRequest, name: str) -> str | None:
    return request.fields[name].as_string() if name in request.fields else None


# --- Protocol settings -----------------------------------------------------------


def test_protocol_identity() -> None:
    protocol = _protocol()
    assert protocol.id == ShapeID("smithy.protocols#rpcv2Json")
    assert protocol.id == RpcV2JsonTrait.id
    assert protocol.content_type == "application/json"
    assert isinstance(protocol.payload_codec, JSONCodec)


def test_payload_codec_configuration() -> None:
    codec = _protocol().payload_codec
    payload = codec.serialize(
        OpInput(
            big_int=2**80,
            big_dec=Decimal("1.0000000000000000000001"),
            when=datetime(2024, 1, 2, 3, 4, 5, tzinfo=UTC),
            renamed="x",
        )
    )
    assert json.loads(payload) == {
        "bigInt": str(2**80),
        "bigDec": "1.0000000000000000000001",
        "when": 1704164645,
        "renamed": "x",
    }


def test_payload_codec_reads_big_numbers_from_strings() -> None:
    codec = _protocol().payload_codec
    output = codec.deserialize(
        source=b'{"bigInt": "1208925819614629174706176"}', shape=OpOutput
    )
    assert output.big_int == 2**80


def test_missing_dependency(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(protocols_module, "_HAS_JSON", False)
    with pytest.raises(MissingDependencyError, match="smithy-json is not installed"):
        _protocol()


@pytest.mark.parametrize(
    "trait, expected",
    [
        (RpcV2JsonTrait(), ()),
        (RpcV2JsonTrait({"http": ["h2", "http/1.1"]}), ()),
        (RpcV2JsonTrait({"eventStreamHttp": ["http/1.1"]}), ("http/1.1",)),
        (RpcV2JsonTrait({"http": ["http/1.1"], "eventStreamHttp": ["h2"]}), ("h2",)),
    ],
)
def test_event_stream_http_resolved_from_rpcv2_json_trait(
    trait: RpcV2JsonTrait, expected: tuple[str, ...]
) -> None:
    protocol = _protocol(_service_schema(trait))
    assert protocol._event_stream_http == expected  # type: ignore[reportPrivateUsage]


def test_event_stream_http_ignores_other_protocol_traits() -> None:
    # A service that carries rpcv2Cbor's trait must not leak it into rpcv2Json.
    from smithy_core.traits import RpcV2CborTrait

    service = Schema.collection(
        id=ShapeID(f"{_NAMESPACE}#{_SERVICE_NAME}"),
        shape_type=ShapeType.SERVICE,
        traits=[RpcV2CborTrait({"eventStreamHttp": ["http/1.1"]})],
    )
    assert _protocol(service)._event_stream_http == ()  # type: ignore[reportPrivateUsage]


# --- Request framing -------------------------------------------------------------


def test_request_framing() -> None:
    request = _serialize(
        OpInput(
            name="hi",
            big_int=12345678901234567890123,
            big_dec=Decimal("-0.000000000000000000001"),
            when=datetime(2024, 1, 2, 3, 4, 5, 500000, tzinfo=UTC),
        )
    )
    assert request.method == "POST"
    assert request.destination.path == f"/service/{_SERVICE_NAME}/operation/DoThing"
    assert _header(request, "Smithy-Protocol") == "rpc-v2-json"
    assert _header(request, "Accept") == "application/json"
    assert _header(request, "Content-Type") == "application/json"
    assert "X-Amz-Target" not in request.fields


async def test_request_body_and_content_length() -> None:
    request = _serialize(
        OpInput(
            name="hi",
            big_int=12345678901234567890123,
            big_dec=Decimal("-0.000000000000000000001"),
            when=datetime(2024, 1, 2, 3, 4, 5, 500000, tzinfo=UTC),
        )
    )
    body = await request.consume_body_async()
    assert _header(request, "Content-Length") == str(len(body))
    assert json.loads(body) == {
        "name": "hi",
        "bigInt": "12345678901234567890123",
        "bigDec": "-1E-21",
        "when": 1704164645.5,
    }


async def test_request_uses_service_name_without_namespace() -> None:
    request = _serialize(OpInput(), _operation(name="OtherOp"))
    assert request.destination.path == f"/service/{_SERVICE_NAME}/operation/OtherOp"
    assert _NAMESPACE not in (request.destination.path or "")


@pytest.mark.parametrize("unit_schema", [UNIT, _SYNTHETIC_UNIT_SCHEMA])
async def test_unit_input_has_no_body_or_content_type(unit_schema: Schema) -> None:
    request = _serialize(UnitShape(unit_schema), _operation(input_schema=unit_schema))
    assert await request.consume_body_async() == b""
    assert "Content-Type" not in request.fields
    # The base class omits Content-Length alongside the body.
    assert "Content-Length" not in request.fields
    assert _header(request, "Smithy-Protocol") == "rpc-v2-json"
    assert _header(request, "Accept") == "application/json"


async def test_empty_structure_input_serializes_empty_object() -> None:
    request = _serialize(OpInput())
    assert await request.consume_body_async() == b"{}"
    assert _header(request, "Content-Type") == "application/json"
    assert _header(request, "Content-Length") == "2"


# --- Responses -------------------------------------------------------------------


async def test_response_with_body() -> None:
    output = await _deserialize(
        _response(200, b'{"name": "x", "count": 3, "bigInt": "99999999999999999999"}')
    )
    assert isinstance(output, OpOutput)
    assert output.name == "x"
    assert output.count == 3
    assert output.big_int == 99999999999999999999


async def test_response_ignores_unknown_members() -> None:
    output = await _deserialize(_response(200, b'{"name": "x", "extra": [1, 2]}'))
    assert output.name == "x"


async def test_response_empty_body_uses_defaults() -> None:
    output = await _deserialize(_response(200, b""))
    assert isinstance(output, OpOutput)
    assert output.name is None
    assert output.count == 0


@pytest.mark.parametrize("body", [b"", b"{}"])
@pytest.mark.parametrize("unit_schema", [UNIT, _SYNTHETIC_UNIT_SCHEMA])
async def test_unit_output(body: bytes, unit_schema: Schema) -> None:
    output = await _deserialize(
        _response(200, body), _operation(output_schema=unit_schema)
    )
    assert isinstance(output, UnitShape)


async def test_smithy_protocol_header_lookup_is_case_insensitive() -> None:
    response = HTTPResponse(
        status=200,
        fields=tuples_to_fields([("SMITHY-PROTOCOL", "rpc-v2-json")]),
        body=AsyncBytesReader(b'{"name": "x"}'),
    )
    assert (await _deserialize(response)).name == "x"


@pytest.mark.parametrize("smithy_protocol", [None, "rpc-v2-cbor", "RPC-V2-JSON", ""])
@pytest.mark.parametrize(
    "status, fault", [(200, "client"), (400, "client"), (500, "server")]
)
async def test_malformed_smithy_protocol_header(
    smithy_protocol: str | None, status: int, fault: str
) -> None:
    # The body would be a valid modeled error (or output) if it were interpreted;
    # the malformed header must short-circuit on the status code alone.
    response = _response(
        status,
        b'{"__type": "smithy.example#MyError", "message": "nope"}',
        smithy_protocol=smithy_protocol,
    )
    with pytest.raises(CallError) as exc_info:
        await _deserialize(response)
    error = exc_info.value
    assert type(error) is CallError
    assert error.fault == fault
    assert "rpc-v2-json" in error.message
    assert repr(smithy_protocol) in error.message
    assert f"status: {status}" in error.message


@pytest.mark.parametrize("status", [200, 400, 500])
async def test_malformed_response_does_not_parse_body(status: int) -> None:
    response = _response(status, b"{not json", smithy_protocol=None)
    with pytest.raises(CallError) as exc_info:
        await _deserialize(response)
    assert type(exc_info.value) is CallError
    # The bounded body is drained (not parsed) so the connection can be reused.
    assert await response.consume_body_async() == b""


class _StreamBody:
    """A live stream body: reading would block, so it must be closed, not drained."""

    def __init__(self) -> None:
        self.closed = False

    async def read(self, size: int = -1) -> bytes:
        raise AssertionError("malformed event-stream response body must not be read")

    async def close(self) -> None:
        self.closed = True


async def test_malformed_event_stream_response_closes_body() -> None:
    body = _StreamBody()
    response = HTTPResponse(status=200, fields=Fields(), body=body)
    with pytest.raises(CallError):
        await _deserialize(response, _operation(output_schema=_STREAM_OUTPUT_SCHEMA))
    assert body.closed


# --- Errors ----------------------------------------------------------------------


@pytest.mark.parametrize(
    "type_value",
    [
        # Absolute shape id, as the spec requires.
        "smithy.example#MyError",
        # Looser forms servers emit in practice.
        "MyError",
        "aws.protocoltests#MyError",
        "smithy.example#MyError:http://internal.amazon.com/coral/com.amazon.coral.validate/",
        "MyError:http://internal.amazon.com/coral/com.amazon.coral.validate/",
    ],
)
async def test_error_resolved_from_type(type_value: str) -> None:
    body = json.dumps({"__type": type_value, "message": "bad input"}).encode()
    with pytest.raises(MyError) as exc_info:
        await _deserialize(_response(400, body))
    assert exc_info.value.message == "bad input"


async def test_error_selects_correct_modeled_error() -> None:
    body = b'{"__type": "smithy.example#OtherError", "message": "boom"}'
    with pytest.raises(OtherError) as exc_info:
        await _deserialize(_response(500, body))
    assert exc_info.value.message == "boom"
    assert exc_info.value.fault == "server"


async def test_error_type_may_follow_members() -> None:
    body = b'{"message": "late", "__type": "smithy.example#MyError"}'
    with pytest.raises(MyError) as exc_info:
        await _deserialize(_response(400, body))
    assert exc_info.value.message == "late"


@pytest.mark.parametrize(
    "type_value, expected_id",
    [
        ("smithy.example#UnknownError", "smithy.example#UnknownError"),
        ("UnknownError", "UnknownError"),
        ("other.ns#UnknownError:http://x", "other.ns#UnknownError"),
    ],
)
async def test_unknown_error_type(type_value: str, expected_id: str) -> None:
    body = json.dumps({"__type": type_value}).encode()
    with pytest.raises(CallError) as exc_info:
        await _deserialize(_response(400, body))
    error = exc_info.value
    assert type(error) is CallError
    assert error.fault == "client"
    assert f"id: {expected_id}" in error.message


@pytest.mark.parametrize(
    "body",
    [
        b"",
        b"{}",
        b'{"message": "no type"}',
        b'{"__type": 5}',
        b"[]",
        b'"MyError"',
        b"null",
        b"{not json",
    ],
)
@pytest.mark.parametrize("status, fault", [(400, "client"), (503, "server")])
async def test_error_without_usable_type(body: bytes, status: int, fault: str) -> None:
    with pytest.raises(CallError) as exc_info:
        await _deserialize(_response(status, body))
    error = exc_info.value
    assert type(error) is CallError
    assert error.fault == fault
    assert f"status: {status}" in error.message


# --- Unions and __type -----------------------------------------------------------


@pytest.mark.parametrize(
    "body, expected",
    [
        (b'{"__type": "smithy.example#MyUnion", "str": "a"}', MyUnionStr("a")),
        (b'{"num": 7, "__type": "smithy.example#MyUnion"}', MyUnionNum(7)),
    ],
)
def test_union_ignores_type_member(body: bytes, expected: MyUnion) -> None:
    # The spec requires deserializers to ignore an unrecognized __type in a union.
    # The JSON deserializer skips non-member keys, so the union consumer never sees
    # __type and does not count it as a second variant.
    deserializer = _protocol().payload_codec.create_deserializer(body)
    assert _MyUnionDeserializer().deserialize(deserializer) == expected
