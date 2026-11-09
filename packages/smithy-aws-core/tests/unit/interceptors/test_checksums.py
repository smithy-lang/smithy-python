#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from collections.abc import AsyncIterator
from dataclasses import dataclass
from io import BytesIO
from typing import Any, cast
from unittest.mock import Mock

import pytest
from smithy_aws_core.aio.checksums import AsyncChecksumStream
from smithy_aws_core.business_metrics import FEATURE_IDS, AwsFeatureId
from smithy_aws_core.checksums import ChecksumStream, UnsupportedChecksumAlgorithmError
from smithy_aws_core.interceptors.checksums import FlexibleChecksumsInterceptor
from smithy_aws_core.traits import HTTPChecksumTrait
from smithy_core import URI
from smithy_core.aio.types import AsyncBytesReader
from smithy_core.client import OPERATION
from smithy_core.exceptions import SmithyError
from smithy_core.interceptors import InputContext, RequestContext, ResponseContext
from smithy_core.interfaces import TypedProperties as TypedPropertiesInterface
from smithy_core.traits import HTTPHeaderTrait
from smithy_core.types import TypedProperties
from smithy_http import Field, Fields, HTTPRequest, HTTPResponse

ALL_ALGORITHMS = ["CRC64NVME", "CRC32", "CRC32C", "SHA256", "SHA1", "MD5"]
DATA = b"hello world"
CRC32 = "DUoRhQ=="
CRC32C = "yZRlqg=="


@dataclass(kw_only=True)
class _Input:
    bucket: str | None = None
    checksum_mode: str | None = None


def _operation(trait: dict[str, Any] | None) -> Any:
    member = Mock()
    member.expect_member_name.return_value = "ChecksumMode"
    operation = Mock()
    http_checksum = HTTPChecksumTrait(trait) if trait is not None else None
    operation.schema.get_trait.return_value = http_checksum
    operation.schema.expect_trait.return_value = http_checksum
    operation.input_schema.members = {"ChecksumMode": member}
    return operation


GET_OBJECT = {
    "requestValidationModeMember": "ChecksumMode",
    "responseAlgorithms": ALL_ALGORITHMS,
}


def _input_context(
    trait: dict[str, Any] | None = GET_OBJECT,
    request: _Input | None = None,
    validation: Any = "when_supported",
) -> InputContext[Any]:
    properties = TypedProperties()
    properties[OPERATION] = _operation(trait)
    # The client stores each call's config, after plugins ran, under "config".
    properties["config"] = Mock(
        request_checksum_calculation="when_supported",
        response_checksum_validation=validation,
    )
    return InputContext(
        request=cast(Any, request or _Input(bucket="b")), properties=properties
    )


def _response_context(
    properties: TypedPropertiesInterface,
    *,
    status: int = 200,
    headers: dict[str, str] | None = None,
) -> ResponseContext[Any, Any, Any]:
    fields = Fields([Field(name=k, values=[v]) for k, v in (headers or {}).items()])
    return ResponseContext(
        request=cast(Any, _Input()),
        transport_request=HTTPRequest(
            destination=URI(host="example.com"), method="GET", fields=Fields()
        ),
        transport_response=HTTPResponse(status=status, fields=fields, body=DATA),
        properties=properties,
    )


def _prepared(
    validation: Any = "when_supported",
    request: _Input | None = None,
    interceptor: FlexibleChecksumsInterceptor | None = None,
) -> tuple[FlexibleChecksumsInterceptor, InputContext[Any], Any]:
    interceptor = interceptor or FlexibleChecksumsInterceptor()
    context = _input_context(request=request, validation=validation)
    return interceptor, context, interceptor.modify_before_serialization(context)


def test_when_supported_enables_validation_mode_without_mutating_input() -> None:
    original = _Input(bucket="b")
    _, _, request = _prepared(request=original)

    assert request.checksum_mode == "ENABLED"
    assert request.bucket == "b"
    assert original.checksum_mode is None


def test_defaults_to_when_supported() -> None:
    _, _, request = _prepared(validation=None)

    assert request.checksum_mode == "ENABLED"


def test_when_required_leaves_validation_mode_unset() -> None:
    interceptor, context, request = _prepared(validation="when_required")

    assert request.checksum_mode is None
    response = _response_context(
        context.properties, headers={"x-amz-checksum-crc32": CRC32}
    )
    assert interceptor.modify_before_deserialization(response).body == DATA


def test_when_required_validates_when_caller_enabled_it() -> None:
    interceptor, context, request = _prepared(
        validation="when_required", request=_Input(checksum_mode="ENABLED")
    )

    assert request.checksum_mode == "ENABLED"
    response = _response_context(
        context.properties, headers={"x-amz-checksum-crc32": CRC32}
    )
    assert isinstance(
        interceptor.modify_before_deserialization(response).body,
        ChecksumStream,
    )


@pytest.mark.parametrize(
    "trait",
    [
        None,
        {"requestAlgorithmMember": "ChecksumAlgorithm"},
        # MD5 can't be validated, so validation isn't enabled.
        {"requestValidationModeMember": "ChecksumMode", "responseAlgorithms": ["MD5"]},
        {"requestValidationModeMember": "Missing", "responseAlgorithms": ["CRC32"]},
    ],
)
def test_operations_without_response_checksums_are_unchanged(
    trait: dict[str, Any] | None,
) -> None:
    interceptor = FlexibleChecksumsInterceptor()
    request = _Input(bucket="b")
    context = _input_context(trait, request)

    assert interceptor.modify_before_serialization(context) is request


def test_reads_the_setting_from_each_calls_config() -> None:
    interceptor = FlexibleChecksumsInterceptor()

    for validation, expected in [
        ("when_required", None),
        ("when_supported", "ENABLED"),
    ]:
        context = _input_context(validation=validation)
        assert (
            interceptor.modify_before_serialization(context).checksum_mode == expected
        )


def test_requires_smithy_aws_checksums(monkeypatch: pytest.MonkeyPatch) -> None:
    from smithy_aws_core._private import checksums
    from smithy_core.exceptions import MissingDependencyError

    monkeypatch.setattr(checksums, "_HAS_CHECKSUMS", False)
    with pytest.raises(MissingDependencyError):
        FlexibleChecksumsInterceptor()


def test_calls_without_an_operation_are_unchanged() -> None:
    interceptor = FlexibleChecksumsInterceptor()
    request = _Input()
    context = InputContext(request=cast(Any, request), properties=TypedProperties())

    assert interceptor.modify_before_serialization(context) is request


def test_validates_the_fastest_algorithm_in_the_response() -> None:
    interceptor, context, _ = _prepared()
    response = _response_context(
        context.properties,
        headers={"x-amz-checksum-crc32": CRC32, "x-amz-checksum-crc32c": CRC32C},
    )

    body = interceptor.modify_before_deserialization(response).body
    assert isinstance(body, ChecksumStream)
    assert body.checksum_algorithm == "CRC32C"
    assert body.read() == DATA
    assert body.validated


async def test_async_clients_get_the_stream_they_pass() -> None:
    interceptor, context, _ = _prepared(
        interceptor=FlexibleChecksumsInterceptor(AsyncChecksumStream)
    )
    response = _response_context(
        context.properties, headers={"x-amz-checksum-crc32": CRC32}
    )

    body = interceptor.modify_before_deserialization(response).body
    assert isinstance(body, AsyncChecksumStream)
    assert await body.read() == DATA
    assert body.validated


@pytest.mark.parametrize("crc32c", ["", "yZRlqg==-3", "yZRlqg==,yZRlqg==", "bad!"])
def test_skips_checksums_that_cannot_be_validated(crc32c: str) -> None:
    interceptor, context, _ = _prepared()
    response = _response_context(
        context.properties,
        headers={"x-amz-checksum-crc32c": crc32c, "x-amz-checksum-crc32": CRC32},
    )

    body = interceptor.modify_before_deserialization(response).body
    assert isinstance(body, ChecksumStream)
    assert body.checksum_algorithm == "CRC32"
    assert body.read() == DATA


def test_skips_composite_checksums() -> None:
    interceptor, context, _ = _prepared()
    response = _response_context(
        context.properties,
        headers={"x-amz-checksum-crc32c": "yZRlqg==-3", "x-amz-checksum-crc32": CRC32},
    )

    body = interceptor.modify_before_deserialization(response).body
    assert isinstance(body, ChecksumStream)
    assert body.checksum_algorithm == "CRC32"


@pytest.mark.parametrize(
    "status,headers",
    [
        (200, {}),
        (200, {"x-amz-checksum-md5": "XrY7u+Ae7tCTyyK7j1rNww=="}),
        (200, {"x-amz-checksum-crc32": "DUoRhQ==-2"}),
        (404, {"x-amz-checksum-crc32": CRC32}),
    ],
)
def test_responses_without_a_usable_checksum_are_unchanged(
    status: int, headers: dict[str, str]
) -> None:
    interceptor, context, _ = _prepared()
    response = _response_context(context.properties, status=status, headers=headers)

    assert (
        interceptor.modify_before_deserialization(response)
        is response.transport_response
    )


@pytest.mark.parametrize(
    "validation,feature_id",
    [
        ("when_supported", AwsFeatureId.FLEXIBLE_CHECKSUMS_RES_WHEN_SUPPORTED),
        ("when_required", AwsFeatureId.FLEXIBLE_CHECKSUMS_RES_WHEN_REQUIRED),
    ],
)
def test_registers_the_validation_setting_feature_id(
    validation: Any, feature_id: AwsFeatureId
) -> None:
    interceptor = FlexibleChecksumsInterceptor()
    context = _input_context(validation=validation)

    interceptor.modify_before_serialization(context)
    assert list(context.properties[FEATURE_IDS]) == [feature_id]


@pytest.mark.parametrize(
    "trait",
    [
        None,
        {"requestAlgorithmMember": "ChecksumAlgorithm"},
        {"requestValidationModeMember": "ChecksumMode", "responseAlgorithms": ["MD5"]},
    ],
)
def test_does_not_register_feature_ids_for_operations_without_response_checksums(
    trait: dict[str, Any] | None,
) -> None:
    interceptor = FlexibleChecksumsInterceptor()
    context = _input_context(trait)

    interceptor.read_before_execution(context)
    interceptor.modify_before_serialization(context)
    assert FEATURE_IDS not in context.properties


# Request checksums.

SHA256 = "uU0nuZNNPgilLlLX2n2r+sSE7+N6U4DukIj3rOLvzek="
CRC64NVME = "jSnVw/bqjr4="
ALGORITHM_HEADER = "x-amz-sdk-checksum-algorithm"
PUT_OBJECT = {"requestAlgorithmMember": "ChecksumAlgorithm"}
PUT_BUCKET_POLICY = {
    "requestChecksumRequired": True,
    "requestAlgorithmMember": "ChecksumAlgorithm",
}


@dataclass(kw_only=True)
class _PutInput:
    checksum_algorithm: str | None = None


def _request_operation(trait: dict[str, Any]) -> Any:
    member = Mock()
    member.expect_member_name.return_value = "ChecksumAlgorithm"
    member.get_trait.side_effect = lambda t: (  # pyright: ignore[reportUnknownLambdaType]
        HTTPHeaderTrait(ALGORITHM_HEADER) if t is HTTPHeaderTrait else None
    )
    operation = Mock()
    operation.schema.get_trait.return_value = HTTPChecksumTrait(trait)
    operation.input_schema.members = {"ChecksumAlgorithm": member}
    return operation


def _request_context(
    trait: dict[str, Any] = PUT_OBJECT,
    *,
    body: Any = DATA,
    algorithm: str | None = None,
    headers: dict[str, str] | None = None,
    calculation: str = "when_supported",
    properties: TypedPropertiesInterface | None = None,
) -> RequestContext[Any, Any]:
    if properties is None:
        properties = TypedProperties()
        properties[OPERATION] = _request_operation(trait)
        properties["config"] = Mock(
            request_checksum_calculation=calculation,
            response_checksum_validation="when_supported",
        )
    headers = dict(headers or {})
    if algorithm is not None:
        # The serializer sends the chosen algorithm in its header.
        headers[ALGORITHM_HEADER] = algorithm
    return RequestContext(
        request=cast(Any, _PutInput(checksum_algorithm=algorithm)),
        transport_request=HTTPRequest(
            destination=URI(host="example.com"),
            method="PUT",
            fields=Fields([Field(name=k, values=[v]) for k, v in headers.items()]),
            # The serializer sends bytes payloads in a BytesIO, and other payloads
            # as they were set on the request.
            body=BytesIO(body) if isinstance(body, bytes) else body,
        ),
        properties=properties,
    )


def _sent(context: RequestContext[Any, Any]) -> dict[str, str]:
    request = FlexibleChecksumsInterceptor().modify_before_signing(context)
    return {f.name.lower(): f.as_string() for f in request.fields}


def test_calculates_the_default_algorithm_without_changing_the_original() -> None:
    context = _request_context()

    assert _sent(context) == {
        "x-amz-checksum-crc64nvme": CRC64NVME,
        ALGORITHM_HEADER: "CRC64NVME",
    }
    assert len(context.transport_request.fields) == 0
    assert list(context.properties[FEATURE_IDS]) == [
        AwsFeatureId.FLEXIBLE_CHECKSUMS_REQ_WHEN_SUPPORTED,
        AwsFeatureId.FLEXIBLE_CHECKSUMS_REQ_CRC64,
    ]


def test_calculates_the_chosen_algorithm() -> None:
    context = _request_context(algorithm="SHA256")

    assert _sent(context) == {
        "x-amz-checksum-sha256": SHA256,
        ALGORITHM_HEADER: "SHA256",
    }


@pytest.mark.parametrize("algorithm", ["MD5", "CRC16"])
def test_rejects_algorithms_it_cannot_calculate(algorithm: str) -> None:
    with pytest.raises(UnsupportedChecksumAlgorithmError, match=algorithm):
        _sent(_request_context(algorithm=algorithm))


@pytest.mark.parametrize(
    "header", ["x-amz-checksum-crc32", "x-amz-checksum-md5", "x-amz-checksum-emoji"]
)
def test_sends_a_checksum_set_by_the_caller_as_is(header: str) -> None:
    context = _request_context(algorithm="SHA256", headers={header: "c2V0"})

    assert FlexibleChecksumsInterceptor().modify_before_signing(context) is (
        context.transport_request
    )


def test_when_required_skips_optional_checksums() -> None:
    context = _request_context(calculation="when_required")

    assert _sent(context) == {}


def test_when_required_still_calculates_chosen_and_required_checksums() -> None:
    chosen = _request_context(algorithm="SHA256", calculation="when_required")
    required = _request_context(PUT_BUCKET_POLICY, calculation="when_required")

    assert "x-amz-checksum-sha256" in _sent(chosen)
    assert "x-amz-checksum-crc64nvme" in _sent(required)


def test_operations_without_request_checksums_are_unchanged() -> None:
    context = _request_context(GET_OBJECT)

    assert FlexibleChecksumsInterceptor().modify_before_signing(context) is (
        context.transport_request
    )
    # The request setting isn't reported for operations it doesn't apply to.
    assert FEATURE_IDS not in context.properties


@pytest.mark.parametrize(
    "calculation,feature_id",
    [
        ("when_supported", AwsFeatureId.FLEXIBLE_CHECKSUMS_REQ_WHEN_SUPPORTED),
        ("when_required", AwsFeatureId.FLEXIBLE_CHECKSUMS_REQ_WHEN_REQUIRED),
    ],
)
def test_registers_the_calculation_setting_feature_id(
    calculation: str, feature_id: AwsFeatureId
) -> None:
    context = _request_context(calculation=calculation)

    _sent(context)
    assert next(iter(context.properties[FEATURE_IDS])) == feature_id


def test_retries_reuse_the_first_checksum() -> None:
    first = _request_context()
    _sent(first)
    retry = _request_context(body=b"changed", properties=first.properties)

    assert _sent(retry)["x-amz-checksum-crc64nvme"] == CRC64NVME


def test_calculates_seekable_streams_and_restores_their_position() -> None:
    body = BytesIO(b"xx" + DATA)
    body.seek(2)

    assert _sent(_request_context(body=body))["x-amz-checksum-crc64nvme"] == CRC64NVME
    assert body.tell() == 2


async def _async_chunks() -> AsyncIterator[bytes]:
    yield DATA


def test_skips_optional_checksums_of_async_payloads() -> None:
    assert _sent(_request_context(body=_async_chunks())) == {}


@pytest.mark.parametrize(
    "trait,algorithm", [(PUT_BUCKET_POLICY, None), (PUT_OBJECT, "SHA256")]
)
def test_requires_a_readable_payload_for_required_or_chosen_checksums(
    trait: dict[str, Any], algorithm: str | None
) -> None:
    context = _request_context(trait, body=_async_chunks(), algorithm=algorithm)

    with pytest.raises(SmithyError, match="can't be calculated"):
        _sent(context)


def test_skips_optional_checksums_of_async_readers() -> None:
    # An async reader can't be read from a synchronous hook, even if it holds bytes.
    assert _sent(_request_context(body=AsyncBytesReader(DATA))) == {}


@pytest.mark.parametrize("body", [DATA, bytearray(DATA)])
def test_calculates_raw_bytes_payloads(body: bytes | bytearray) -> None:
    context = _request_context(body=b"")
    context.transport_request.body = body

    assert _sent(context)["x-amz-checksum-crc64nvme"] == CRC64NVME


class _SeekableWithoutSeekableMethod:
    def __init__(self, data: bytes) -> None:
        self._data = BytesIO(data)
        self.read = self._data.read
        self.seek = self._data.seek
        self.tell = self._data.tell


def test_calculates_streams_that_can_seek_without_a_seekable_method() -> None:
    body = _SeekableWithoutSeekableMethod(DATA)

    assert _sent(_request_context(body=body))["x-amz-checksum-crc64nvme"] == CRC64NVME
    assert body.tell() == 0


class _FailingStream(BytesIO):
    def read(self, size: int | None = -1) -> bytes:
        super().read(size)
        raise OSError("read failed")


def test_restores_the_stream_position_when_a_read_fails() -> None:
    body = _FailingStream(DATA)

    with pytest.raises(OSError, match="read failed"):
        _sent(_request_context(body=body))
    assert body.tell() == 0
