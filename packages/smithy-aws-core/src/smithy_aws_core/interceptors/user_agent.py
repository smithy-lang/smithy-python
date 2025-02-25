# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
from smithy_core.interceptors import Interceptor, InterceptorContext, Request, TransportRequest
from smithy_http.aio import HTTPRequest


class UserAgentInterceptor(Interceptor):
    """Adds UserAgent header to the Request before signing.
    """
    def modify_before_signing(
            self, context: InterceptorContext[Request, None, HTTPRequest, None]
    ) -> HTTPRequest:
        print("Oh Hello here I am!")
        return context.transport_request