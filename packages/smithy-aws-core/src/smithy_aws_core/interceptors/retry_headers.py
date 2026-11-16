#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import uuid
from typing import Any

from smithy_core.interceptors import Interceptor, RequestContext
from smithy_http import Field
from smithy_http.interfaces import HTTPRequest

__all__ = ["RetryHeadersInterceptor"]


class RetryHeadersInterceptor(Interceptor[Any, Any, HTTPRequest, Any]):
    """Adds the ``amz-sdk-invocation-id`` header to every attempt of a call.

    The header holds a random (version 4) UUID that is the same on every attempt of a
    call and different for every call, so a service can tell which requests are
    attempts of the same call.
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
