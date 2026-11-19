#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""How the RPCv2 protocols classify error responses for retries."""

import json
from collections.abc import Callable
from dataclasses import dataclass, replace
from typing import Any, ClassVar, Self, cast
from unittest.mock import Mock

import pytest
from smithy_core.deserializers import ShapeDeserializer
from smithy_core.documents import TypeRegistry
from smithy_core.exceptions import CallError, ModeledError
from smithy_core.interfaces import ProtocolSettings
from smithy_core.prelude import STRING
from smithy_core.program import run_program
from smithy_core.schemas import APIOperation, Schema
from smithy_core.shapes import ShapeID, ShapeType
from smithy_core.traits import Trait
from smithy_core.types import TypedProperties
from smithy_core.utils import read_streaming_blob
from smithy_http import HTTPRequest, HTTPResponse, tuples_to_fields
from smithy_http.protocols import RpcV2CborClientProtocol, RpcV2JsonClientProtocol

_THROTTLING_ERROR_CODES = [
    "Throttling",
    "ThrottlingException",
    "ThrottledException",
    "RequestThrottledException",
    "TooManyRequestsException",
    "ProvisionedThroughputExceededException",
    "TransactionInProgressException",
    "RequestLimitExceeded",
    "BandwidthLimitExceeded",
    "LimitExceededException",
    "RequestThrottled",
    "SlowDown",
    "PriorRequestNotComplete",
    "EC2ThrottledException",
]

_TRANSIENT_ERROR_CODES = ["RequestTimeout", "InternalError", "RequestTimeoutException"]


def _cbor_body(code: str) -> bytes:
    # {"__type": "com.test#<code>"}, with a one-byte string length.
    value = f"com.test#{code}".encode()
    assert len(value) < 256
    return b"\xa1\x66__type\x78" + bytes([len(value)]) + value


def _json_body(code: str) -> bytes:
    return json.dumps({"__type": f"com.test#{code}"}).encode()


@dataclass(frozen=True)
class _Case:
    protocol: Callable[[ProtocolSettings], Any]
    fields: tuple[tuple[str, str], ...]
    body: Callable[[str], bytes]


_CASES = [
    pytest.param(
        _Case(
            RpcV2CborClientProtocol,
            (("smithy-protocol", "rpc-v2-cbor"), ("content-type", "application/cbor")),
            _cbor_body,
        ),
        id="rpcv2Cbor",
    ),
    pytest.param(
        _Case(
            RpcV2JsonClientProtocol,
            (("smithy-protocol", "rpc-v2-json"), ("content-type", "application/json")),
            _json_body,
        ),
        id="rpcv2Json",
    ),
]


def _settings(*, query_compatible: bool = False) -> ProtocolSettings:
    traits = (
        [Trait.new(id=ShapeID("aws.protocols#awsQueryCompatible"))]
        if query_compatible
        else []
    )
    return ProtocolSettings(
        namespace="com.test",
        service_target="Service",
        version="2020-01-08",
        service_schema=Schema.collection(
            id=ShapeID("com.test#Service"), shape_type=ShapeType.SERVICE, traits=traits
        ),
    )


def _error_schema(name: str) -> Schema:
    return Schema.collection(
        id=ShapeID(f"com.test#{name}"),
        traits=[Trait.new(id=ShapeID("smithy.api#error"), value="server")],
        members={"message": {"target": STRING}},
    )


class _MessageError(ModeledError):
    schema: ClassVar[Schema]

    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> Self:
        kwargs: dict[str, Any] = {}

        def _consumer(member: Schema, de: ShapeDeserializer) -> None:
            kwargs["message"] = de.read_string(member)

        deserializer.read_struct(cls.schema, consumer=_consumer)
        return cls(**kwargs)


@dataclass(kw_only=True)
class _UndecidedError(_MessageError):
    schema = _error_schema("UndecidedError")


@dataclass(kw_only=True)
class _RetryableError(_MessageError):
    schema = _error_schema("RetryableError")
    is_retry_safe: bool | None = True


@dataclass(kw_only=True)
class _NotRetryableError(_MessageError):
    schema = _error_schema("NotRetryableError")
    is_retry_safe: bool | None = False


@dataclass(kw_only=True)
class _ThrottlingException(_MessageError):
    schema = _error_schema("ThrottlingException")


_MODELED_ERRORS: list[type[_MessageError]] = [
    _UndecidedError,
    _RetryableError,
    _NotRetryableError,
]


def _operation(modeled_errors: list[type[_MessageError]]) -> APIOperation[Any, Any]:
    operation = Mock(spec=APIOperation)
    operation.schema = Schema(
        id=ShapeID("com.test#Operation"), shape_type=ShapeType.OPERATION
    )
    operation.output_schema = Schema.collection(id=ShapeID("com.test#Output"))
    operation.error_schemas = [error.schema for error in modeled_errors]
    operation.input_stream_member = None
    operation.output_stream_member = None
    return cast("APIOperation[Any, Any]", operation)


def _raise(
    case: _Case,
    status: int,
    body: bytes,
    *,
    fields: tuple[tuple[str, str], ...] = (),
    query_compatible: bool = False,
    modeled_errors: list[type[_MessageError]] = _MODELED_ERRORS,
) -> CallError:
    protocol = case.protocol(_settings(query_compatible=query_compatible))
    response = HTTPResponse(
        status=status,
        fields=tuples_to_fields([*case.fields, *fields]),
        body=body,
    )
    with pytest.raises(CallError) as exc_info:
        run_program(
            protocol.deserialize_response_program(
                operation=_operation(modeled_errors),
                request=cast(HTTPRequest, Mock()),
                response=response,
                error_registry=TypeRegistry(
                    {error.schema.id: error for error in modeled_errors}
                ),
                context=TypedProperties(),
                read_body=read_streaming_blob,
            )
        )
    return exc_info.value


@pytest.mark.parametrize("case", _CASES)
@pytest.mark.parametrize("status", [500, 502, 503, 504])
def test_unmodeled_transient_status_is_retry_safe(case: _Case, status: int) -> None:
    error = _raise(case, status, case.body("SomeError"))
    assert type(error) is CallError
    assert error.is_retry_safe is True
    assert error.is_throttling_error is False
    assert error.fault == "server"


@pytest.mark.parametrize("case", _CASES)
@pytest.mark.parametrize("status", [500, 503])
def test_transient_status_without_a_body_is_retry_safe(
    case: _Case, status: int
) -> None:
    error = _raise(case, status, b"")
    assert error.is_retry_safe is True


@pytest.mark.parametrize("case", _CASES)
@pytest.mark.parametrize("status", [400, 403, 501, 505])
def test_other_status_leaves_retry_safety_undecided(case: _Case, status: int) -> None:
    error = _raise(case, status, case.body("SomeError"))
    assert error.is_retry_safe is None


@pytest.mark.parametrize("case", _CASES)
def test_unmodeled_429_is_a_throttling_error(case: _Case) -> None:
    error = _raise(case, 429, case.body("SomeError"))
    assert error.is_retry_safe is True
    assert error.is_throttling_error is True


@pytest.mark.parametrize("case", _CASES)
def test_unmodeled_408_is_a_timeout(case: _Case) -> None:
    error = _raise(case, 408, case.body("SomeError"))
    assert error.is_retry_safe is True
    assert error.is_timeout_error is True


@pytest.mark.parametrize("case", _CASES)
@pytest.mark.parametrize("code", _THROTTLING_ERROR_CODES)
def test_throttling_error_code_is_a_throttling_error(case: _Case, code: str) -> None:
    error = _raise(case, 400, case.body(code))
    assert error.is_retry_safe is True
    assert error.is_throttling_error is True


@pytest.mark.parametrize("case", _CASES)
@pytest.mark.parametrize("code", _TRANSIENT_ERROR_CODES)
def test_transient_error_code_is_retry_safe(case: _Case, code: str) -> None:
    error = _raise(case, 400, case.body(code))
    assert error.is_retry_safe is True
    assert error.is_throttling_error is False


@pytest.mark.parametrize("case", _CASES)
def test_throttling_error_code_takes_precedence_over_a_transient_status(
    case: _Case,
) -> None:
    error = _raise(case, 503, case.body("SlowDown"))
    assert error.is_retry_safe is True
    assert error.is_throttling_error is True


@pytest.mark.parametrize("case", _CASES)
def test_service_specific_error_code_is_not_retry_safe(case: _Case) -> None:
    # The SDK retry behavior retries it for STS clients only.
    error = _raise(case, 400, case.body("IDPCommunicationError"))
    assert error.is_retry_safe is None


@pytest.mark.parametrize("case", _CASES)
def test_modeled_error_with_a_throttling_error_code_is_a_throttling_error(
    case: _Case,
) -> None:
    error = _raise(
        case,
        400,
        case.body("ThrottlingException"),
        modeled_errors=[_ThrottlingException],
    )
    assert type(error) is _ThrottlingException
    assert error.is_retry_safe is True
    assert error.is_throttling_error is True


@pytest.mark.parametrize("case", _CASES)
def test_query_error_code_of_a_query_compatible_service_is_classified(
    case: _Case,
) -> None:
    error = _raise(
        case,
        400,
        case.body("SomeError"),
        fields=(("x-amzn-query-error", "Throttling;Sender"),),
        query_compatible=True,
    )
    assert error.is_retry_safe is True
    assert error.is_throttling_error is True


@pytest.mark.parametrize("case", _CASES)
@pytest.mark.parametrize(
    ("status", "retry_safe", "throttling", "timeout"),
    [
        (500, True, False, False),
        (503, True, False, False),
        (429, True, True, False),
        (408, True, False, True),
        (400, None, False, False),
        (200, None, False, False),
    ],
)
def test_malformed_response_is_classified_by_status(
    case: _Case, status: int, retry_safe: bool | None, throttling: bool, timeout: bool
) -> None:
    # Such as a load balancer's response, which has no Smithy-Protocol header.
    fields = tuple(f for f in case.fields if f[0] != "smithy-protocol")
    malformed = replace(case, fields=fields)
    error = _raise(malformed, status, case.body("NotRetryableError"))
    assert type(error) is CallError
    assert error.is_retry_safe is retry_safe
    assert error.is_throttling_error is throttling
    assert error.is_timeout_error is timeout


@pytest.mark.parametrize("case", _CASES)
@pytest.mark.parametrize(
    ("error_type", "status", "expected"),
    [
        (_UndecidedError, 503, True),
        (_UndecidedError, 500, True),
        (_UndecidedError, 429, None),
        (_UndecidedError, 408, None),
        (_UndecidedError, 400, None),
        (_RetryableError, 400, True),
        (_NotRetryableError, 503, False),
    ],
)
def test_modeled_error_retry_safety(
    case: _Case, error_type: type[_MessageError], status: int, expected: bool | None
) -> None:
    error = _raise(case, status, case.body(error_type.schema.id.name))
    assert type(error) is error_type
    assert error.is_retry_safe is expected
    assert error.is_throttling_error is False
