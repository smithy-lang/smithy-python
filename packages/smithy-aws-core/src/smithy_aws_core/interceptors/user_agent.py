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

from smithy_aws_core.user_agent import UserAgent
from smithy_core.interceptors import Interceptor, InterceptorContext, Request
from smithy_http import Field
from smithy_http.aio import HTTPRequest


class UserAgentInterceptor(Interceptor[Request, None, HTTPRequest, None]):
    """Adds UserAgent header to the Request before signing."""

    def __init__(
        self,
        ua_suffix: str | None = None,
        ua_app_id: str | None = None,
        sdk_version: str | None = "0.0.1",
    ) -> None:
        """Initialize the UserAgentInterceptor.

        :ua_suffix: Additional suffix to be added to the UserAgent header. :ua_app_id:
        User defined and opaque application ID to be added to the UserAgent header.
        """
        super().__init__()
        self._ua_suffix = ua_suffix
        self._ua_app_id = ua_app_id
        self._sdk_version = sdk_version

    def modify_before_signing(
        self, context: InterceptorContext[Request, None, HTTPRequest, None]
    ) -> HTTPRequest:
        user_agent = UserAgent.from_environment().with_config(
            ua_suffix=self._ua_suffix,
            ua_app_id=self._ua_app_id,
            sdk_version=self._sdk_version,
        )
        request = context.transport_request
        request.fields.set_field(
            Field(name="User-Agent", values=[user_agent.to_string()])
        )
        return context.transport_request
