#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""How the RPCv2 protocols report an error response's code in its metadata."""

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Self, cast
from unittest.mock import Mock

import pytest
from smithy_core.deserializers import ShapeDeserializer
from smithy_core.documents import TypeRegistry
from smithy_core.exceptions import CallError, ModeledError
from smithy_core.interfaces import ProtocolSettings
from smithy_core.program import run_program
from smithy_core.response import ErrorResponseMetadata
from smithy_core.schemas import APIOperation, Schema
from smithy_core.shapes import ShapeID, ShapeType
from smithy_core.traits import Trait
from smithy_core.types import TypedProperties
from smithy_core.utils import read_streaming_blob
from smithy_http import HTTPRequest, HTTPResponse, tuples_to_fields
from smithy_http.protocols import RpcV2CborClientProtocol, RpcV2JsonClientProtocol


def _cbor_body(error_type: str) -> bytes:
    # {"__type": "<error_type>"}, with a one-byte string length.
    value = error_type.encode()
    assert len(value) < 256
    return b"\xa1\x66__type\x78" + bytes([len(value)]) + value


def _json_body(error_type: str) -> bytes:
    return json.dumps({"__type": error_type}).encode()


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


class _ModeledTestError(ModeledError):
    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> Self:
        return cls("modeled error")


def _operation() -> APIOperation[Any, Any]:
    operation = Mock(spec=APIOperation)
    operation.schema = Schema(
        id=ShapeID("com.test#Operation"), shape_type=ShapeType.OPERATION
    )
    operation.output_schema = Schema.collection(id=ShapeID("com.test#Output"))
    operation.error_schemas = []
    operation.input_stream_member = None
    operation.output_stream_member = None
    return cast("APIOperation[Any, Any]", operation)


def _error_metadata(
    case: _Case,
    body: bytes,
    *,
    fields: tuple[tuple[str, str], ...] = (),
    query_compatible: bool = False,
    error_registry: TypeRegistry | None = None,
    raises: type[CallError] = CallError,
) -> ErrorResponseMetadata:
    protocol = case.protocol(_settings(query_compatible=query_compatible))
    response = HTTPResponse(
        status=400, fields=tuples_to_fields([*case.fields, *fields]), body=body
    )
    with pytest.raises(raises) as exc_info:
        run_program(
            protocol.deserialize_response_program(
                operation=_operation(),
                request=cast(HTTPRequest, Mock()),
                response=response,
                error_registry=error_registry or TypeRegistry({}),
                context=TypedProperties(),
                read_body=read_streaming_blob,
            )
        )
    return exc_info.value.response_metadata


@pytest.mark.parametrize("case", _CASES)
def test_error_code_is_reported(case: _Case) -> None:
    metadata = _error_metadata(case, case.body("com.test#SomeError"))
    assert metadata.error_code == "SomeError"


@pytest.mark.parametrize("case", _CASES)
def test_query_compatible_service_reports_the_query_error_code(case: _Case) -> None:
    metadata = _error_metadata(
        case,
        case.body("com.test#QueueDoesNotExist"),
        fields=(
            ("x-amzn-query-error", "AWS.SimpleQueueService.NonExistentQueue;Sender"),
        ),
        query_compatible=True,
    )
    assert metadata.error_code == "AWS.SimpleQueueService.NonExistentQueue"


@pytest.mark.parametrize("case", [p for p in _CASES if p.id == "rpcv2Json"])
def test_modeled_error_reports_its_code(case: _Case) -> None:
    metadata = _error_metadata(
        case,
        case.body("com.test#ModeledTestError"),
        error_registry=TypeRegistry(
            {ShapeID("com.test#ModeledTestError"): _ModeledTestError}
        ),
        raises=_ModeledTestError,
    )
    assert metadata.error_code == "ModeledTestError"
