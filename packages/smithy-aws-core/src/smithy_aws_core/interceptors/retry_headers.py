#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import uuid
from typing import Any

from smithy_core.interceptors import Interceptor, RequestContext
from smithy_core.retries import RETRY_STRATEGY
from smithy_core.types import PropertyKey
from smithy_http import Field
from smithy_http.interfaces import HTTPRequest

__all__ = ["RetryHeadersInterceptor"]

_ATTEMPT = PropertyKey(key="retry_headers_attempt", value_type=int)


class RetryHeadersInterceptor(Interceptor[Any, Any, HTTPRequest, Any]):
    """Adds the headers that tell a service how a call is retried.

    ``amz-sdk-invocation-id`` holds a random (version 4) UUID that is the same on every
    attempt of a call and different for every call, so a service can tell which
    requests are attempts of the same call.

    ``amz-sdk-request`` holds the number of the attempt, starting at 1, and the most
    attempts the call's retry strategy allows, such as ``attempt=2; max=3``. When that
    number is not known (no retry strategy, or a ``max_attempts`` that is missing or
    not a positive integer), it holds only the attempt number.
    """

    def modify_before_retry_loop(
        self, context: RequestContext[Any, HTTPRequest]
    ) -> HTTPRequest:
        # This hook runs once per call, before the first attempt, so every attempt
        # sends the same ID.
        request = context.transport_request
        request.fields.set_field(
            Field(name="amz-sdk-invocation-id", values=[str(uuid.uuid4())])
        )
        return request

    def read_before_attempt(self, context: RequestContext[Any, HTTPRequest]) -> None:
        # The properties are shared by every attempt of a call, so they hold the count.
        context.properties[_ATTEMPT] = context.properties.get(_ATTEMPT, 0) + 1

    def modify_before_signing(
        self, context: RequestContext[Any, HTTPRequest]
    ) -> HTTPRequest:
        request = context.transport_request
        value = f"attempt={context.properties[_ATTEMPT]}"
        # A custom strategy may not set max_attempts, so it's read with a default.
        max_attempts = getattr(
            context.properties.get(RETRY_STRATEGY), "max_attempts", None
        )
        if (
            isinstance(max_attempts, int)
            and not isinstance(max_attempts, bool)
            and max_attempts >= 1
        ):
            value += f"; max={max_attempts}"
        request.fields.set_field(Field(name="amz-sdk-request", values=[value]))
        return request
