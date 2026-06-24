#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from typing import Any

from smithy_core.interceptors import Interceptor, RequestContext
from smithy_http import Field
from smithy_http.aio.interfaces import HTTPRequest


class ApiGatewayAcceptHeaderInterceptor(Interceptor[Any, Any, HTTPRequest, None]):
    """Sets the Accept header to application/json on API Gateway requests."""

    def modify_before_signing(
        self, context: RequestContext[Any, HTTPRequest]
    ) -> HTTPRequest:
        request = context.transport_request
        request.fields.set_field(Field(name="Accept", values=["application/json"]))
        return request
