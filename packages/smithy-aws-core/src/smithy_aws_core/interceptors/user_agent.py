#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from smithy_core.interceptors import Interceptor, Request
from smithy_http.aio.interfaces import HTTPRequest


class UserAgentInterceptor(Interceptor[Request, None, HTTPRequest, None]):
    """Adds UserAgent header to the Request before signing."""