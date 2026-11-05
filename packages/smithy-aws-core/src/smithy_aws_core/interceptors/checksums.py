#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import logging
from dataclasses import replace
from typing import Any

from smithy_core._model_naming import member_field_name
from smithy_core.aio.client import OPERATION
from smithy_core.interceptors import InputContext, Interceptor, ResponseContext
from smithy_core.interfaces import TypedProperties
from smithy_core.schemas import APIOperation
from smithy_core.types import PropertyKey
from smithy_http.aio import HTTPResponse
from smithy_http.aio.interfaces import HTTPRequest
from smithy_http.aio.interfaces import HTTPResponse as HTTPResponseInterface

from .._private.checksums import (
    assert_checksums_installed,
    checksum_header,
    decode_checksum,
    response_validation_order,
)
from ..aio.checksums import AsyncChecksumStream
from ..business_metrics import AwsFeatureId, register_feature_id
from ..traits import HTTPChecksumTrait

__all__ = ["FlexibleChecksumsInterceptor"]

logger = logging.getLogger(__name__)


class FlexibleChecksumsInterceptor(
    Interceptor[Any, Any, HTTPRequest, HTTPResponseInterface]
):
    """Validates response checksums of operations with the ``httpChecksum`` trait.

    When to validate is read from the ``response_checksum_validation`` setting of
    each call's config, so plugins can change it per call. Operations without the
    trait are passed through unchanged.
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

        # The setting is only reported for operations it applies to.
        validation = _response_checksum_validation(context.properties)
        if (feature_id := _FEATURE_IDS.get(validation)) is not None:
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

_FEATURE_IDS = {
    "when_supported": AwsFeatureId.FLEXIBLE_CHECKSUMS_RES_WHEN_SUPPORTED,
    "when_required": AwsFeatureId.FLEXIBLE_CHECKSUMS_RES_WHEN_REQUIRED,
}


def _response_checksum_validation(properties: TypedProperties) -> str:
    config = properties.get("config")
    return getattr(config, "response_checksum_validation", None) or "when_supported"


def _input_field_name(
    operation: APIOperation[Any, Any], member_name: str | None
) -> str | None:
    if member_name is None:
        return None
    member = operation.input_schema.members.get(member_name)
    if member is None:
        return None
    return member_field_name(
        member.expect_member_name(),
        is_error=False,
        carries_response_metadata=False,
        is_enum=False,
    )
