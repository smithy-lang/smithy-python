#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import logging
from copy import copy, deepcopy
from dataclasses import replace
from inspect import iscoroutinefunction
from typing import Any

from smithy_core._model_naming import member_field_name
from smithy_core.aio.client import OPERATION
from smithy_core.aio.interfaces import StreamingBlob
from smithy_core.aio.types import AsyncBytesReader
from smithy_core.exceptions import SmithyError
from smithy_core.interceptors import (
    InputContext,
    Interceptor,
    RequestContext,
    ResponseContext,
)
from smithy_core.interfaces import TypedProperties
from smithy_core.schemas import APIOperation, Schema
from smithy_core.traits import HTTPHeaderTrait
from smithy_core.types import PropertyKey
from smithy_http import Field
from smithy_http.aio import HTTPResponse
from smithy_http.aio.interfaces import HTTPRequest
from smithy_http.aio.interfaces import HTTPResponse as HTTPResponseInterface

from .._private.checksums import (
    DEFAULT_ALGORITHM,
    SUPPORTED_ALGORITHMS,
    assert_checksums_installed,
    checksum_header,
    checksum_header_algorithm,
    create_checksum,
    decode_checksum,
    encode_digest,
    response_validation_order,
)
from ..aio.checksums import AsyncChecksumStream
from ..business_metrics import AwsFeatureId, register_feature_id
from ..checksums import UnsupportedChecksumAlgorithmError
from ..traits import HTTPChecksumTrait

__all__ = ["FlexibleChecksumsInterceptor"]

logger = logging.getLogger(__name__)


class FlexibleChecksumsInterceptor(
    Interceptor[Any, Any, HTTPRequest, HTTPResponseInterface]
):
    """Adds and validates checksums for operations with the ``httpChecksum`` trait.

    Request checksums are sent in a header. When to calculate and validate them is
    read from the ``request_checksum_calculation`` and
    ``response_checksum_validation`` settings of each call's config, so plugins can
    change them per call. Operations without the trait are passed through unchanged.
    """

    def __init__(self) -> None:
        """Initialize the interceptor.

        :raises MissingDependencyError: If smithy-checksums isn't installed.
        """
        assert_checksums_installed()

    def modify_before_serialization(self, context: InputContext[Any]) -> Any:
        operation = context.properties.get(OPERATION)
        if operation is None:
            return context.request
        trait = operation.schema.get_trait(HTTPChecksumTrait)
        if trait is None:
            return context.request
        algorithms = response_validation_order(trait.response_algorithms)
        field_name = _input_field_name(operation, trait.request_validation_mode_member)
        if not algorithms or field_name is None:
            return context.request

        # Feature IDs are only reported for operations the setting applies to.
        validation = _response_setting(context.properties)
        if (feature_id := _RESPONSE_SETTING_FEATURE_IDS.get(validation)) is not None:
            register_feature_id(context.properties, feature_id)

        request = context.request
        mode = getattr(request, field_name, None)
        if mode is None and validation == "when_supported":
            # Replace rather than mutate, so the caller's input isn't changed.
            request = replace(request, **{field_name: _VALIDATION_MODE_ENABLED})
            mode = _VALIDATION_MODE_ENABLED
        if mode is not None and str(mode) == _VALIDATION_MODE_ENABLED:
            context.properties[_RESPONSE_ALGORITHMS] = algorithms
        return request

    def modify_before_signing(
        self, context: RequestContext[Any, HTTPRequest]
    ) -> HTTPRequest:
        request = context.transport_request
        operation = context.properties.get(OPERATION)
        if operation is None:
            return request
        trait = operation.schema.get_trait(HTTPChecksumTrait)
        if trait is None or not (
            trait.request_checksum_required or trait.request_algorithm_member
        ):
            return request

        # Feature IDs are only reported for operations the setting applies to.
        calculation = _request_setting(context.properties)
        if (feature_id := _REQUEST_SETTING_FEATURE_IDS.get(calculation)) is not None:
            register_feature_id(context.properties, feature_id)

        # A checksum set by the caller is sent as is.
        provided = [checksum_header_algorithm(field.name) for field in request.fields]
        if any(provided):
            for algorithm in filter(None, provided):
                _register_algorithm(context.properties, algorithm)
            return request

        # A retry reuses the checksum, so a payload that changed is rejected.
        if (saved := context.properties.get(_REQUEST_CHECKSUM)) is None:
            chosen = _chosen_algorithm(context.request, operation, trait)
            algorithm = chosen
            if algorithm is None and (
                trait.request_checksum_required or calculation == "when_supported"
            ):
                algorithm = DEFAULT_ALGORITHM
            if algorithm is None:
                return request
            source = _payload_source(request.body)
            value = _calculate(algorithm, source)
            if value is None:
                if chosen is not None or trait.request_checksum_required:
                    raise SmithyError(
                        f"A {algorithm} request checksum can't be calculated for a "
                        f"payload of type {type(source).__name__}. Send bytes or a "
                        "seekable file, or set the checksum on the request."
                    )
                logger.debug(
                    "Skipping the request checksum: it can't be calculated for a "
                    "payload of type %s.",
                    type(source),
                )
                return request
            saved = (algorithm, value)
            context.properties[_REQUEST_CHECKSUM] = saved

        algorithm, value = saved
        # The request of each attempt shares its fields with the original, so copy
        # them before changing anything.
        request = copy(request)
        request.fields = deepcopy(request.fields)
        if (header := _algorithm_header(operation, trait)) is not None:
            if header not in request.fields:
                request.fields.set_field(Field(name=header, values=[algorithm]))
        request.fields.set_field(Field(name=checksum_header(algorithm), values=[value]))
        _register_algorithm(context.properties, algorithm)
        return request

    def modify_before_deserialization(
        self, context: ResponseContext[Any, HTTPRequest, HTTPResponseInterface]
    ) -> HTTPResponseInterface:
        response = context.transport_response
        algorithms = context.properties.get(_RESPONSE_ALGORITHMS)
        if not algorithms or not 200 <= response.status < 300:
            return response

        for algorithm in algorithms:
            header = checksum_header(algorithm)
            if header not in response.fields:
                continue
            expected = decode_checksum(response.fields[header].as_string())
            if expected is None:
                # Empty, malformed, and composite (multipart) checksums can't be
                # validated, so try the next algorithm.
                continue
            # Build a new response, since not every transport's response allows
            # its body to be replaced.
            return HTTPResponse(
                status=response.status,
                fields=response.fields,
                reason=response.reason,
                body=AsyncChecksumStream(
                    response.body, checksum_algorithm=algorithm, expected=expected
                ),
            )

        logger.debug(
            "Skipping response checksum validation: the response has no valid "
            "checksum for any of the algorithms %s.",
            algorithms,
        )
        return response


_VALIDATION_MODE_ENABLED = "ENABLED"

_RESPONSE_ALGORITHMS = PropertyKey(
    key="response_checksum_algorithms", value_type=tuple[str, ...]
)
"""The algorithms to validate the response with, fastest first, if it's validated."""

_REQUEST_CHECKSUM = PropertyKey(key="request_checksum", value_type=tuple[str, str])
"""The algorithm and value of the request checksum, kept to be reused on retries."""

_READ_CHUNK_SIZE = 64 * 1024

_REQUEST_SETTING_FEATURE_IDS = {
    "when_supported": AwsFeatureId.FLEXIBLE_CHECKSUMS_REQ_WHEN_SUPPORTED,
    "when_required": AwsFeatureId.FLEXIBLE_CHECKSUMS_REQ_WHEN_REQUIRED,
}

_RESPONSE_SETTING_FEATURE_IDS = {
    "when_supported": AwsFeatureId.FLEXIBLE_CHECKSUMS_RES_WHEN_SUPPORTED,
    "when_required": AwsFeatureId.FLEXIBLE_CHECKSUMS_RES_WHEN_REQUIRED,
}

_ALGORITHM_FEATURE_IDS = {
    "CRC32": AwsFeatureId.FLEXIBLE_CHECKSUMS_REQ_CRC32,
    "CRC32C": AwsFeatureId.FLEXIBLE_CHECKSUMS_REQ_CRC32C,
    "CRC64NVME": AwsFeatureId.FLEXIBLE_CHECKSUMS_REQ_CRC64,
    "SHA1": AwsFeatureId.FLEXIBLE_CHECKSUMS_REQ_SHA1,
    "SHA256": AwsFeatureId.FLEXIBLE_CHECKSUMS_REQ_SHA256,
    "SHA512": AwsFeatureId.FLEXIBLE_CHECKSUMS_REQ_SHA512,
    "MD5": AwsFeatureId.FLEXIBLE_CHECKSUMS_REQ_MD5,
    "XXHASH64": AwsFeatureId.FLEXIBLE_CHECKSUMS_REQ_XXHASH64,
    "XXHASH3": AwsFeatureId.FLEXIBLE_CHECKSUMS_REQ_XXHASH3,
    "XXHASH128": AwsFeatureId.FLEXIBLE_CHECKSUMS_REQ_XXHASH128,
}


def _request_setting(properties: TypedProperties) -> str:
    config = properties.get("config")
    return getattr(config, "request_checksum_calculation", None) or "when_supported"


def _response_setting(properties: TypedProperties) -> str:
    config = properties.get("config")
    return getattr(config, "response_checksum_validation", None) or "when_supported"


def _chosen_algorithm(
    request: Any, operation: APIOperation[Any, Any], trait: HTTPChecksumTrait
) -> str | None:
    field_name = _input_field_name(operation, trait.request_algorithm_member)
    chosen = getattr(request, field_name, None) if field_name else None
    if chosen is None:
        return None
    chosen = str(getattr(chosen, "value", chosen))
    if chosen.upper() not in SUPPORTED_ALGORITHMS:
        raise UnsupportedChecksumAlgorithmError(chosen)
    return chosen.upper()


def _payload_source(body: StreamingBlob) -> object:
    # The serializer wraps payloads in a reader, which may itself wrap one set on
    # the request. Subclasses may transform what they read, such as by compressing
    # it, so only plain readers are unwrapped.
    source: object = body
    while type(source) is AsyncBytesReader:
        source = source.source
    return source


def _calculate(algorithm: str, source: Any) -> str | None:
    """Calculate a checksum of the payload, if it can be read synchronously.

    Interceptor hooks are synchronous, so only bytes and seekable synchronous
    streams can be read here. The stream is returned to where it started.
    """
    if isinstance(source, bytes | bytearray):
        checksum = create_checksum(algorithm)
        checksum.update(source)
        return encode_digest(checksum.digest())

    read = getattr(source, "read", None)
    if read is None or iscoroutinefunction(read) or not _is_seekable(source):
        return None
    checksum = create_checksum(algorithm)
    start = source.tell()
    try:
        while chunk := read(_READ_CHUNK_SIZE):
            checksum.update(chunk)
    finally:
        source.seek(start)
    return encode_digest(checksum.digest())


def _is_seekable(source: Any) -> bool:
    # Streams without seekable() are treated as seekable if they can seek, as the
    # retry of a request does.
    seek = getattr(source, "seek", None)
    tell = getattr(source, "tell", None)
    if seek is None or tell is None or iscoroutinefunction(seek):
        return False
    if (seekable := getattr(source, "seekable", None)) is None:
        return True
    return not iscoroutinefunction(seekable) and bool(seekable())


def _algorithm_header(
    operation: APIOperation[Any, Any], trait: HTTPChecksumTrait
) -> str | None:
    member = _input_member(operation, trait.request_algorithm_member)
    if member is None or (http_header := member.get_trait(HTTPHeaderTrait)) is None:
        return None
    return http_header.key


def _register_algorithm(properties: TypedProperties, algorithm: str) -> None:
    if (feature_id := _ALGORITHM_FEATURE_IDS.get(algorithm)) is not None:
        register_feature_id(properties, feature_id)


def _input_member(
    operation: APIOperation[Any, Any], member_name: str | None
) -> Schema | None:
    if member_name is None:
        return None
    return operation.input_schema.members.get(member_name)


def _input_field_name(
    operation: APIOperation[Any, Any], member_name: str | None
) -> str | None:
    if (member := _input_member(operation, member_name)) is None:
        return None
    return member_field_name(
        member.expect_member_name(),
        is_error=False,
        carries_response_metadata=False,
        is_enum=False,
    )
