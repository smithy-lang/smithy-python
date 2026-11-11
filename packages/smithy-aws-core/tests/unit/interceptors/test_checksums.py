#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import gc
import warnings
from collections.abc import AsyncIterator
from dataclasses import dataclass, replace
from io import BytesIO
from typing import Any, cast
from unittest.mock import MagicMock, Mock

import pytest
from aws_sdk_signers import (
    AWSCredentialIdentity,
    SigV4ChunkSigner,
    SigV4Signer,
    SigV4SigningProperties,
)
from smithy_aws_core._aws_chunked import AwsChunkedReader
from smithy_aws_core.aio._aws_chunked import AsyncAwsChunkedReader
from smithy_aws_core.aio.checksums import AsyncChecksumStream
from smithy_aws_core.aio.interceptors.checksums import (
    AsyncFlexibleChecksumsInterceptor,
)
from smithy_aws_core.auth.sigv4 import SigV4AuthScheme
from smithy_aws_core.business_metrics import FEATURE_IDS, AwsFeatureId
from smithy_aws_core.checksums import ChecksumStream, UnsupportedChecksumAlgorithmError
from smithy_aws_core.identity import AWSCredentialsIdentity
from smithy_aws_core.interceptors.checksums import FlexibleChecksumsInterceptor
from smithy_aws_core.traits import HTTPChecksumTrait
from smithy_core import URI
from smithy_core.aio.types import AsyncBytesReader
from smithy_core.auth import RESOLVED_IDENTITY
from smithy_core.client import AUTH_SCHEME, OPERATION
from smithy_core.exceptions import SmithyError
from smithy_core.interceptors import InputContext, RequestContext, ResponseContext
from smithy_core.interfaces import TypedProperties as TypedPropertiesInterface
from smithy_core.schemas import Schema
from smithy_core.shapes import ShapeID, ShapeType
from smithy_core.traits import HTTPHeaderTrait, StreamingTrait
from smithy_core.types import TypedProperties
from smithy_http import Field, Fields, HTTPRequest, HTTPResponse
from smithy_http.urllib3 import (
    _Urllib3ResponseBody,  # pyright: ignore[reportPrivateUsage]
)

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
    body: Any = DATA,
) -> ResponseContext[Any, Any, Any]:
    fields = Fields([Field(name=k, values=[v]) for k, v in (headers or {}).items()])
    return ResponseContext(
        request=cast(Any, _Input()),
        transport_request=HTTPRequest(
            destination=URI(host="example.com"), method="GET", fields=Fields()
        ),
        transport_response=HTTPResponse(status=status, fields=fields, body=body),
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


async def test_async_interceptor_validates_with_an_async_stream() -> None:
    interceptor, context, _ = _prepared(interceptor=AsyncFlexibleChecksumsInterceptor())
    response = _response_context(
        context.properties, headers={"x-amz-checksum-crc32": CRC32}
    )

    body = interceptor.modify_before_deserialization(response).body
    assert isinstance(body, AsyncChecksumStream)
    assert await body.read() == DATA
    assert body.validated


class _StreamedResponse:
    """Stands in for the urllib3 response the sync transport streams a body from."""

    def __init__(self, data: bytes) -> None:
        self._data = BytesIO(data)
        self.closed = False

    def read(self, amt: int | None = None) -> bytes:
        return self._data.read(-1 if amt is None else amt)

    def close(self) -> None:
        self.closed = True

    def release_conn(self) -> None:
        pass


def _public(obj: object) -> set[str]:
    return {name for name in dir(obj) if not name.startswith("_")}


def test_wraps_streamed_sync_bodies() -> None:
    interceptor, context, _ = _prepared()
    source = _StreamedResponse(DATA)
    response = _response_context(
        context.properties,
        headers={"x-amz-checksum-crc32": CRC32},
        body=_Urllib3ResponseBody(source),  # type: ignore[arg-type]
    )

    body = interceptor.modify_before_deserialization(response).body
    assert isinstance(body, ChecksumStream)
    with body:
        assert b"".join(body.iter_chunks(4)) == DATA
        assert body.validated
    assert source.closed


def test_validated_and_unvalidated_sync_bodies_share_an_interface() -> None:
    interceptor, context, _ = _prepared()
    unvalidated = _Urllib3ResponseBody(_StreamedResponse(DATA))  # type: ignore[arg-type]
    response = _response_context(
        context.properties,
        headers={"x-amz-checksum-crc32": CRC32},
        body=_Urllib3ResponseBody(_StreamedResponse(DATA)),  # type: ignore[arg-type]
    )

    validated = interceptor.modify_before_deserialization(response).body
    assert isinstance(validated, ChecksumStream)
    # Only the checksum details, and a seek that always raises, differ.
    assert _public(validated) - _public(unvalidated) == {
        "checksum_algorithm",
        "validated",
        "seek",
    }
    assert _public(unvalidated) - _public(validated) == set()


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


# Generated input schemas carry the streaming trait of the blob a member targets.
_STREAMING_BODY = Schema.collection(
    id=ShapeID("com.test#PutInput"),
    members={
        "Body": {
            "target": Schema(
                id=ShapeID("com.test#StreamingBlob"),
                shape_type=ShapeType.BLOB,
                traits=[StreamingTrait()],
            )
        }
    },
).members["Body"]


def _request_operation(trait: dict[str, Any], *, streaming: bool = False) -> Any:
    member = MagicMock()
    member.expect_member_name.return_value = "ChecksumAlgorithm"
    member.get_trait.side_effect = lambda t: (  # pyright: ignore[reportUnknownLambdaType]
        HTTPHeaderTrait(ALGORITHM_HEADER) if t is HTTPHeaderTrait else None
    )
    operation = Mock()
    operation.schema.get_trait.return_value = HTTPChecksumTrait(trait)
    members: dict[str, Any] = {"ChecksumAlgorithm": member}
    if streaming:
        members["Body"] = _STREAMING_BODY
    operation.input_schema.members = members
    return operation


def _request_context(
    trait: dict[str, Any] = PUT_OBJECT,
    *,
    body: Any = DATA,
    algorithm: str | None = None,
    headers: dict[str, str] | None = None,
    calculation: str = "when_supported",
    properties: TypedPropertiesInterface | None = None,
    streaming: bool = False,
    scheme: str = "https",
) -> RequestContext[Any, Any]:
    if properties is None:
        properties = TypedProperties()
        properties[OPERATION] = _request_operation(trait, streaming=streaming)
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
            destination=URI(scheme=scheme, host="example.com"),
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


@pytest.mark.parametrize(
    "interceptor,advises_length",
    [
        pytest.param(AsyncFlexibleChecksumsInterceptor(), True, id="async-client"),
        pytest.param(FlexibleChecksumsInterceptor(), False, id="sync-client"),
    ],
)
@pytest.mark.parametrize("scheme", ["https", "http"])
def test_suggests_a_content_length_only_where_it_helps(
    interceptor: FlexibleChecksumsInterceptor, advises_length: bool, scheme: str
) -> None:
    # A content length lets an async client encode an async payload, which a sync
    # client can't read.
    context = _streaming_context(
        body=_async_chunks(), length=None, algorithm="SHA256", scheme=scheme
    )

    with pytest.raises(SmithyError) as error:
        interceptor.modify_before_signing(context)
    assert ("content length" in str(error.value)) is advises_length


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


# Trailing checksums of streaming payloads.


class _UnreadableBody(BytesIO):
    """Fails if it's read before it's sent."""

    def read(self, size: int | None = -1) -> bytes:
        raise AssertionError("The payload was read before it was sent.")


# What the generated plugin of an async client builds.
_ASYNC_CLIENT_INTERCEPTOR = AsyncFlexibleChecksumsInterceptor()


def _streaming_context(
    body: Any = DATA,
    *,
    length: int | None = len(DATA),
    headers: dict[str, str] | None = None,
    **kwargs: Any,
) -> RequestContext[Any, Any]:
    headers = dict(headers or {})
    if length is not None:
        headers["content-length"] = str(length)
    return _request_context(body=body, headers=headers, streaming=True, **kwargs)


def _transmitted(
    context: RequestContext[Any, Any],
    interceptor: FlexibleChecksumsInterceptor | None = None,
) -> RequestContext[Any, Any]:
    """Sign, then transmit the request, as an attempt does."""
    interceptor = interceptor or FlexibleChecksumsInterceptor()
    signed = replace(
        context, transport_request=interceptor.modify_before_signing(context)
    )
    return replace(signed, transport_request=interceptor.modify_before_transmit(signed))


def _read(body: Any) -> bytes:
    return body.read()


async def _read_async(body: Any) -> bytes:
    return await body.read()


def _encoded(data: bytes, checksum: str) -> bytes:
    return (
        f"{len(data):x}\r\n".encode()
        + data
        + f"\r\n0\r\nx-amz-checksum-crc64nvme:{checksum}\r\n\r\n".encode()
    )


def test_streaming_payloads_send_a_trailing_checksum() -> None:
    context = _streaming_context(body=_UnreadableBody(DATA))

    sent = _sent(context)

    assert sent["x-amz-trailer"] == "x-amz-checksum-crc64nvme"
    assert sent["x-amz-content-sha256"] == "STREAMING-UNSIGNED-PAYLOAD-TRAILER"
    assert sent["content-encoding"] == "aws-chunked"
    assert sent["x-amz-decoded-content-length"] == str(len(DATA))
    assert sent[ALGORITHM_HEADER] == "CRC64NVME"
    assert "x-amz-checksum-crc64nvme" not in sent
    # The encoded payload is sent with chunked transfer encoding, as botocore does.
    assert sent["transfer-encoding"] == "chunked"
    assert "content-length" not in sent
    assert list(context.properties[FEATURE_IDS])[-1] == (
        AwsFeatureId.FLEXIBLE_CHECKSUMS_REQ_CRC64
    )


def test_trailing_checksum_requests_sign_without_reading_the_payload() -> None:
    context = _streaming_context(
        body=_UnreadableBody(DATA), headers={"content-encoding": "gzip"}
    )
    request = FlexibleChecksumsInterceptor().modify_before_signing(context)

    canonical = (
        SigV4Signer()
        .canonical_request(
            signing_properties=SigV4SigningProperties(
                region="us-west-2", service="s3", date="20250101T000000Z"
            ),
            request=cast(Any, request),
        )
        .splitlines()
    )

    # The headers are signed as the service rebuilds them, and the payload hash is
    # the trailer's, so the payload isn't read to sign it.
    assert "content-encoding:gzip,aws-chunked" in canonical
    assert "x-amz-trailer:x-amz-checksum-crc64nvme" in canonical
    assert f"x-amz-decoded-content-length:{len(DATA)}" in canonical
    assert {"content-encoding", "x-amz-decoded-content-length", "x-amz-trailer"} <= set(
        canonical[-2].split(";")
    )
    assert canonical[-1] == "STREAMING-UNSIGNED-PAYLOAD-TRAILER"
    SigV4Signer().sign(
        properties=SigV4SigningProperties(region="us-west-2", service="s3"),
        request=cast(Any, request),
        identity=AWSCredentialIdentity(
            access_key_id="AKIDEXAMPLE", secret_access_key="secret"
        ),
    )


_IDENTITY = AWSCredentialsIdentity(
    access_key_id="AKIDEXAMPLE", secret_access_key="secret"
)


def _sigv4_context(body: Any = DATA, **kwargs: Any) -> RequestContext[Any, Any]:
    context = _streaming_context(body=body, **kwargs)
    context.properties[AUTH_SCHEME] = SigV4AuthScheme(service="s3")
    context.properties[RESOLVED_IDENTITY] = _IDENTITY
    return context


def _signed_and_transmitted(
    context: RequestContext[Any, Any],
    interceptor: FlexibleChecksumsInterceptor | None = None,
    date: str = "20250101T000000Z",
) -> RequestContext[Any, Any]:
    """Sign with SigV4, then transmit the request, as an attempt does."""
    interceptor = interceptor or FlexibleChecksumsInterceptor()
    request = interceptor.modify_before_signing(context)
    signed = SigV4Signer().sign(
        request=cast(Any, request),
        identity=_IDENTITY,
        properties=SigV4SigningProperties(region="us-west-2", service="s3", date=date),
    )
    context = replace(context, transport_request=cast(Any, signed))
    return replace(
        context, transport_request=interceptor.modify_before_transmit(context)
    )


def _signed_encoding(request: Any, data: bytes, checksum: str) -> bytes:
    """Encode ``data`` as a request signed as it's sent should be."""
    signer = SigV4ChunkSigner.from_signed_request(request, _IDENTITY)
    trailer = f"x-amz-checksum-crc64nvme:{checksum}"
    return (
        f"{len(data):x};chunk-signature={signer.sign_chunk(data)}\r\n".encode()
        + data
        + f"\r\n0;chunk-signature={signer.sign_chunk(b'')}\r\n{trailer}\r\n".encode()
        + f"x-amz-trailer-signature:{signer.sign_trailer(trailer + chr(10))}".encode()
        + b"\r\n\r\n"
    )


@pytest.mark.parametrize("sigv4", [True, False], ids=["sigv4", "anonymous"])
def test_payloads_over_https_or_without_sigv4_are_unsigned(sigv4: bool) -> None:
    for scheme in ("https",) if sigv4 else ("https", "http"):
        context = (_sigv4_context if sigv4 else _streaming_context)(scheme=scheme)

        sent = _sent(context)

        assert sent["x-amz-content-sha256"] == "STREAMING-UNSIGNED-PAYLOAD-TRAILER"


def test_sigv4_payloads_over_http_are_signed_as_they_are_sent() -> None:
    context = _sigv4_context(body=_UnreadableBody(DATA), scheme="http")

    sent = _sent(context)

    assert sent["x-amz-content-sha256"] == "STREAMING-AWS4-HMAC-SHA256-PAYLOAD-TRAILER"
    assert sent["x-amz-trailer"] == "x-amz-checksum-crc64nvme"
    assert sent["content-encoding"] == "aws-chunked"
    assert sent["x-amz-decoded-content-length"] == str(len(DATA))
    assert sent["transfer-encoding"] == "chunked"
    assert "x-amz-checksum-crc64nvme" not in sent


@pytest.mark.parametrize("client", ["sync", "async"])
async def test_sigv4_payloads_over_http_sign_each_chunk_and_the_trailer(
    client: str,
) -> None:
    if client == "sync":
        context, interceptor = _sigv4_context(scheme="http"), None
    else:
        context = _sigv4_context(body=_async_chunks(), scheme="http")
        interceptor = _ASYNC_CLIENT_INTERCEPTOR
    request = _signed_and_transmitted(context, interceptor).transport_request

    # The payload isn't read to sign the request, only to send it.
    assert request.fields["Authorization"].as_string().startswith("AWS4-HMAC-SHA256 ")
    encoded = (
        await _read_async(request.body)
        if isinstance(request.body, AsyncAwsChunkedReader)
        else _read(request.body)
    )
    assert encoded == _signed_encoding(request, DATA, CRC64NVME)


def test_signed_retries_sign_again_and_reuse_the_checksum() -> None:
    first = _signed_and_transmitted(_sigv4_context(scheme="http"))
    _read(first.transport_request.body)

    # The retry signs the changed payload's chunks again, from its new signature,
    # with the first attempt's checksum.
    retry = _signed_and_transmitted(
        _sigv4_context(body=b"changed!!!!", scheme="http", properties=first.properties),
        date="20250101T000001Z",
    ).transport_request

    assert _read(retry.body) == _signed_encoding(retry, b"changed!!!!", CRC64NVME)
    assert (
        retry.fields["Authorization"] != first.transport_request.fields["Authorization"]
    )


def test_streaming_payloads_are_encoded_when_sent() -> None:
    request = _transmitted(_streaming_context()).transport_request

    assert _read(request.body) == _encoded(DATA, CRC64NVME)


async def test_async_streaming_payloads_are_encoded_when_sent() -> None:
    async def chunks() -> AsyncIterator[bytes]:
        yield DATA

    request = _transmitted(
        _streaming_context(body=chunks()), _ASYNC_CLIENT_INTERCEPTOR
    ).transport_request

    assert isinstance(request.body, AsyncAwsChunkedReader)
    assert await _read_async(request.body) == _encoded(DATA, CRC64NVME)


async def test_async_payloads_use_a_header_without_an_async_reader() -> None:
    # An interceptor built without AsyncAwsChunkedReader can't encode the payload,
    # so it falls back to a header, which can't be calculated for an async iterable.
    async def chunks() -> AsyncIterator[bytes]:
        yield DATA

    body = chunks()
    context = _transmitted(_streaming_context(body=body))
    request = context.transport_request

    assert request.body is body
    assert "x-amz-trailer" not in request.fields
    assert request.fields["content-length"].as_string() == str(len(DATA))


class _AwaitableReader:
    """A reader whose plain read() returns an awaitable, like an AwaitableBytesReader."""

    def __init__(self, data: bytes) -> None:
        self._data = BytesIO(data)

    def read(self, size: int = -1) -> Any:
        async def read() -> bytes:
            return self._data.read(size)

        return read()

    def seekable(self) -> bool:
        return True

    def seek(self, offset: int, whence: int = 0) -> int:
        return self._data.seek(offset, whence)

    def tell(self) -> int:
        return self._data.tell()


class _SyncReader:
    """A synchronous reader that isn't an io stream."""

    def __init__(self, data: bytes) -> None:
        self._data = BytesIO(data)

    def read(self, size: int = -1) -> bytes:
        return self._data.read(size)


async def test_async_clients_encode_awaitable_readers() -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        request = _transmitted(
            _streaming_context(body=_AwaitableReader(DATA)), _ASYNC_CLIENT_INTERCEPTOR
        ).transport_request

        assert isinstance(request.body, AsyncAwsChunkedReader)
        assert await _read_async(request.body) == _encoded(DATA, CRC64NVME)
        gc.collect()
    assert not [w for w in caught if issubclass(w.category, RuntimeWarning)]


@pytest.mark.parametrize("algorithm", [pytest.param("SHA256", id="chosen"), None])
def test_awaitable_readers_without_a_trailer_skip_or_fail_cleanly(
    algorithm: str | None,
) -> None:
    # Without a content length the checksum goes in a header, which a hook can't
    # calculate from an awaitable read(). The read's coroutine is closed rather than
    # left unawaited.
    context = _streaming_context(
        body=_AwaitableReader(DATA), length=None, algorithm=algorithm
    )

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        if algorithm is None:
            sent = _ASYNC_CLIENT_INTERCEPTOR.modify_before_signing(context).fields
            assert not [f for f in sent if f.name.startswith("x-amz-checksum-")]
        else:
            with pytest.raises(SmithyError, match="can't be calculated"):
                _ASYNC_CLIENT_INTERCEPTOR.modify_before_signing(context)
        gc.collect()
    assert not [w for w in caught if issubclass(w.category, RuntimeWarning)]


async def test_async_clients_encode_sync_readers_that_arent_io_streams() -> None:
    request = _transmitted(
        _streaming_context(body=_SyncReader(DATA)), _ASYNC_CLIENT_INTERCEPTOR
    ).transport_request

    assert isinstance(request.body, AsyncAwsChunkedReader)
    assert await _read_async(request.body) == _encoded(DATA, CRC64NVME)


def test_sync_clients_keep_a_sync_reader_for_any_sync_reader() -> None:
    request = _transmitted(_streaming_context(body=_SyncReader(DATA))).transport_request

    assert isinstance(request.body, AwsChunkedReader)
    assert _read(request.body) == _encoded(DATA, CRC64NVME)


def test_async_clients_keep_a_sync_reader_for_sync_payloads() -> None:
    # Every HTTP client can stream a synchronous reader, such as an open file.
    request = _transmitted(
        _streaming_context(), _ASYNC_CLIENT_INTERCEPTOR
    ).transport_request

    assert isinstance(request.body, AwsChunkedReader)
    assert _read(request.body) == _encoded(DATA, CRC64NVME)


def test_retries_reuse_a_trailing_checksum() -> None:
    first = _transmitted(_streaming_context())
    _read(first.transport_request.body)

    # The retry reads the same length from a payload that changed.
    retry = _transmitted(
        _streaming_context(body=b"changed!!!!", properties=first.properties)
    )

    assert _read(retry.transport_request.body).endswith(
        f"x-amz-checksum-crc64nvme:{CRC64NVME}\r\n\r\n".encode()
    )


def test_retries_that_use_a_header_send_the_payload_unencoded() -> None:
    # Each attempt signs again, so a retry whose request can't send a trailer uses
    # a header after an attempt that used a trailer.
    first = _transmitted(_streaming_context())
    _read(first.transport_request.body)

    retry = _transmitted(
        _streaming_context(length=None, properties=first.properties)
    ).transport_request

    assert "x-amz-trailer" not in retry.fields
    assert retry.fields["x-amz-checksum-crc64nvme"].as_string() == CRC64NVME
    assert _read(retry.body) == DATA


def test_retries_recalculate_a_trailing_checksum_that_was_not_finished() -> None:
    payload = b"x" * (200 * 1024)
    first = _transmitted(_streaming_context(body=payload, length=len(payload)))
    first.transport_request.body.read(10)

    retry = _transmitted(
        _streaming_context(
            body=payload, length=len(payload), properties=first.properties
        )
    )

    encoded = _read(retry.transport_request.body)
    expected = _read(
        _transmitted(
            _streaming_context(body=payload, length=len(payload))
        ).transport_request.body
    )
    assert encoded == expected


def test_trailing_checksum_body_sends_only_its_content_length() -> None:
    # A payload longer than its content length is cut off at that length.
    context = _transmitted(_streaming_context(body=BytesIO(DATA + b" and more")))

    assert _read(context.transport_request.body) == _encoded(DATA, CRC64NVME)


def test_trailing_checksum_fails_a_payload_shorter_than_its_content_length() -> None:
    first = _transmitted(_streaming_context(body=BytesIO(DATA[:5])))

    with pytest.raises(SmithyError, match=r"after 5 bytes.*length is 11"):
        _read(first.transport_request.body)

    # The short payload's checksum isn't saved for a retry to reuse.
    retry = _transmitted(_streaming_context(properties=first.properties))
    assert _read(retry.transport_request.body) == _encoded(DATA, CRC64NVME)


@pytest.mark.parametrize("scheme", ["https", "http"])
def test_streaming_payloads_of_unknown_length_use_a_header(scheme: str) -> None:
    context = _streaming_context(length=None, scheme=scheme)

    sent = _sent(context)

    assert "x-amz-trailer" not in sent
    assert sent["x-amz-checksum-crc64nvme"] == CRC64NVME
    # The payload is sent as is, not encoded.
    assert _transmitted(context).transport_request.body is (
        context.transport_request.body
    )


def test_checksums_set_by_the_caller_are_not_trailed() -> None:
    context = _streaming_context(headers={"x-amz-checksum-crc32": "c2V0"})

    assert "x-amz-trailer" not in _sent(context)
    assert FlexibleChecksumsInterceptor().modify_before_transmit(context) is (
        context.transport_request
    )


def test_aws_chunked_follows_other_content_encodings() -> None:
    context = _streaming_context(headers={"content-encoding": "gzip"})

    assert _sent(context)["content-encoding"] == "gzip,aws-chunked"
