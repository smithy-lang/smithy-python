#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, ClassVar, Self, cast
from unittest.mock import Mock

import pytest
from smithy_aws_core.protocols import AwsJson10ClientProtocol
from smithy_core import URI as _URI
from smithy_core.deserializers import ShapeDeserializer
from smithy_core.documents import TypeRegistry
from smithy_core.exceptions import CallError, ModeledError
from smithy_core.interfaces import ProtocolSettings
from smithy_core.prelude import STRING
from smithy_core.program import run_program
from smithy_core.schemas import APIOperation, Schema
from smithy_core.serializers import ShapeSerializer
from smithy_core.shapes import ShapeID, ShapeType
from smithy_core.traits import Trait
from smithy_core.types import TypedProperties
from smithy_core.utils import read_streaming_blob
from smithy_http import HTTPRequest, HTTPResponse, tuples_to_fields
from smithy_http.protocols import RpcClientProtocol, RpcV2CborClientProtocol

_QUERY_COMPATIBLE = Trait.new(id=ShapeID("aws.protocols#awsQueryCompatible"))

_INPUT_SCHEMA = Schema.collection(id=ShapeID("com.test#Input"))
_CUSTOM_CODE_ERROR_SCHEMA = Schema.collection(
    id=ShapeID("com.test#CustomCodeError"),
    traits=[
        Trait.new(id=ShapeID("smithy.api#error"), value="client"),
        Trait.new(
            id=ShapeID("aws.protocols#awsQueryError"),
            value={"code": "Customized", "httpResponseCode": 402},
        ),
    ],
    members={"message": {"target": STRING}},
)
_NAMED_ERROR_SCHEMA = Schema.collection(
    id=ShapeID("com.test#NamedError"),
    traits=[Trait.new(id=ShapeID("smithy.api#error"), value="client")],
    members={"message": {"target": STRING}},
)


@dataclass
class _Input:
    def serialize(self, serializer: ShapeSerializer) -> None:
        serializer.write_struct(_INPUT_SCHEMA, self)

    def serialize_members(self, serializer: ShapeSerializer) -> None:
        pass


class _MessageError(ModeledError):
    schema: ClassVar[Schema]

    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> Self:
        kwargs: dict[str, Any] = {}

        def _consumer(member: Schema, de: ShapeDeserializer) -> None:
            kwargs["message"] = de.read_string(member)

        deserializer.read_struct(cls.schema, consumer=_consumer)
        return cls(**kwargs)


class _CustomCodeError(_MessageError):
    schema = _CUSTOM_CODE_ERROR_SCHEMA


class _NamedError(_MessageError):
    schema = _NAMED_ERROR_SCHEMA


_ERROR_REGISTRY = TypeRegistry(
    {
        _CUSTOM_CODE_ERROR_SCHEMA.id: _CustomCodeError,
        _NAMED_ERROR_SCHEMA.id: _NamedError,
    }
)


def _settings(query_compatible: bool) -> ProtocolSettings:
    return ProtocolSettings(
        namespace="com.test",
        service_target="Service",
        service_schema=Schema.collection(
            id=ShapeID("com.test#Service"),
            shape_type=ShapeType.SERVICE,
            traits=[_QUERY_COMPATIBLE] if query_compatible else [],
        ),
    )


@dataclass(frozen=True)
class _Case:
    protocol: Callable[[ProtocolSettings], RpcClientProtocol]
    response_fields: tuple[tuple[str, str], ...]


_CASES = [
    pytest.param(
        _Case(
            AwsJson10ClientProtocol, (("content-type", "application/x-amz-json-1.0"),)
        ),
        id="awsJson1_0",
    ),
    pytest.param(
        _Case(
            RpcV2CborClientProtocol,
            (("smithy-protocol", "rpc-v2-cbor"), ("content-type", "application/cbor")),
        ),
        id="rpcv2Cbor",
    ),
]


def _operation() -> APIOperation[Any, Any]:
    operation = Mock(spec=APIOperation)
    operation.schema = Schema(
        id=ShapeID("com.test#Operation"), shape_type=ShapeType.OPERATION
    )
    operation.input_schema = _INPUT_SCHEMA
    operation.output_schema = Schema.collection(id=ShapeID("com.test#Output"))
    operation.error_schemas = [_CUSTOM_CODE_ERROR_SCHEMA, _NAMED_ERROR_SCHEMA]
    operation.input_stream_member = None
    operation.output_stream_member = None
    return cast("APIOperation[Any, Any]", operation)


def _raise_error(case: _Case, query_compatible: bool, query_error: str) -> Exception:
    protocol = case.protocol(_settings(query_compatible))
    response = HTTPResponse(
        status=400,
        fields=tuples_to_fields(
            [*case.response_fields, ("x-amzn-query-error", query_error)]
        ),
        body=b"",
    )
    with pytest.raises(CallError) as exc_info:
        run_program(
            protocol.deserialize_response_program(
                operation=_operation(),
                request=cast(HTTPRequest, Mock()),
                response=response,
                error_registry=_ERROR_REGISTRY,
                context=TypedProperties(),
                read_body=read_streaming_blob,
            )
        )
    return exc_info.value


@pytest.mark.parametrize("case", _CASES)
@pytest.mark.parametrize("query_compatible", [True, False])
def test_sends_query_mode_header_only_when_query_compatible(
    case: _Case, query_compatible: bool
) -> None:
    protocol = case.protocol(_settings(query_compatible))
    request = protocol.serialize_request(
        operation=_operation(),
        input=_Input(),
        endpoint=_URI(host="example.com"),
        context=TypedProperties(),
    )
    if query_compatible:
        assert request.fields["x-amzn-query-mode"].as_string() == "true"
    else:
        assert "x-amzn-query-mode" not in request.fields


@pytest.mark.parametrize("case", _CASES)
@pytest.mark.parametrize(
    ("query_error", "expected"),
    [
        ("Customized;Sender", _CustomCodeError),
        ("NamedError;Sender", _NamedError),
    ],
)
def test_resolves_error_from_query_error_header(
    case: _Case, query_error: str, expected: type[ModeledError]
) -> None:
    assert type(_raise_error(case, True, query_error)) is expected


@pytest.mark.parametrize("case", _CASES)
def test_ignores_query_error_header_when_not_query_compatible(case: _Case) -> None:
    error = _raise_error(case, False, "Customized;Sender")
    assert type(error) is CallError


@pytest.mark.parametrize("case", _CASES)
@pytest.mark.parametrize(
    ("query_error", "fault"),
    [("Unknown;Receiver", "server"), ("Unknown;Sender", "client")],
)
def test_unmodeled_error_takes_fault_from_query_error_type(
    case: _Case, query_error: str, fault: str
) -> None:
    error = _raise_error(case, True, query_error)
    assert type(error) is CallError
    assert error.fault == fault
