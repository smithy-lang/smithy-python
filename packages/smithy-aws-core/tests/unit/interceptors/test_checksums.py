#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
from io import BytesIO
from typing import Any, cast
from unittest.mock import Mock

import pytest
from smithy_aws_core.aio.checksums import AsyncChecksumStream
from smithy_aws_core.business_metrics import FEATURE_IDS, AwsFeatureId
from smithy_aws_core.checksums import ChecksumStream
from smithy_aws_core.interceptors.checksums import FlexibleChecksumsInterceptor
from smithy_aws_core.traits import HTTPChecksumTrait
from smithy_core import URI
from smithy_core.client import OPERATION
from smithy_core.interceptors import InputContext, ResponseContext
from smithy_core.interfaces import TypedProperties as TypedPropertiesInterface
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
    properties["config"] = Mock(response_checksum_validation=validation)
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


def test_requires_smithy_checksums(monkeypatch: pytest.MonkeyPatch) -> None:
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
