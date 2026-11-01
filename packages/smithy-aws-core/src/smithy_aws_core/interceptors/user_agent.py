#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
# pyright: reportMissingTypeStubs=false
import os
from typing import Any

import smithy_core
from smithy_core.aio.retries import (
    RETRY_STRATEGY,
    AsyncAdaptiveRetryStrategy,
    AsyncStandardRetryStrategy,
)
from smithy_core.interceptors import Interceptor, RequestContext
from smithy_core.interfaces import TypedProperties
from smithy_core.types import PropertyKey
from smithy_http import Field
from smithy_http.aio.interfaces import HTTPRequest
from smithy_http.interceptors.user_agent import USER_AGENT
from smithy_http.user_agent import RawStringUserAgentComponent, UserAgentComponent

from .. import __version__
from ..business_metrics import (
    FEATURE_IDS,
    AwsFeatureId,
    encode_feature_ids,
    register_feature_id,
)

__all__ = ["UserAgentInterceptor"]

_USERAGENT_SDK_NAME = "aws-sdk-python"

_WRITTEN_USER_AGENT = PropertyKey(
    key="aws_written_user_agent", value_type=tuple[str, str]
)
"""
The User-Agent this attempt started with (without m/) and the one it wrote (with m/).

The next attempt uses them, if there is one, so that m/ isn't added twice.
"""


class UserAgentInterceptor(Interceptor[Any, Any, Any, Any]):
    """Adds AWS fields to the UserAgent."""

    def __init__(
        self,
        *,
        ua_suffix: str | None,
        ua_app_id: str | None,
        sdk_version: str,
        service_id: str,
    ) -> None:
        """Initialize the UserAgentInterceptor.

        :param ua_suffix: Additional suffix to be added to the UserAgent header.
        :param ua_app_id: User defined and opaque application ID to be added to the
            UserAgent header.
        :param sdk_version: SDK version to be added to the UserAgent header.
        :param service_id: ServiceId to be added to the UserAgent header.
        """
        super().__init__()
        self._ua_suffix = ua_suffix
        self._ua_app_id = ua_app_id
        self._sdk_version = sdk_version
        self._service_id = service_id
        self._execution_env = os.environ.get("AWS_EXECUTION_ENV")

    def read_after_serialization(self, context: RequestContext[Any, Any]) -> None:
        if USER_AGENT in context.properties:
            user_agent = context.properties[USER_AGENT]
            user_agent.sdk_metadata = self._build_sdk_metadata()
            user_agent.api_metadata.append(
                UserAgentComponent("api", self._service_id, self._sdk_version)
            )

            if self._execution_env:
                user_agent.env_metadata.append(
                    UserAgentComponent("exec-env", self._execution_env)
                )

            if self._ua_app_id is not None:
                user_agent.additional_metadata.append(
                    UserAgentComponent("app", self._ua_app_id)
                )

            if self._ua_suffix is not None:
                user_agent.additional_metadata.append(
                    RawStringUserAgentComponent(self._ua_suffix)
                )

        self._register_retry_mode(context.properties)

    def modify_before_transmit(
        self, context: RequestContext[Any, HTTPRequest]
    ) -> HTTPRequest:
        # Runs on every attempt, after identity resolution and signing, so features
        # registered up to that point are included. User-Agent isn't signed by AWS
        # auth schemes, so changing it after signing doesn't affect the signature.
        request = context.transport_request
        encoded = encode_feature_ids(context.properties.get(FEATURE_IDS, {}))
        if encoded and "User-Agent" in request.fields:
            current = request.fields["User-Agent"].as_string()
            # In generated clients each attempt gets a fresh User-Agent. The signer
            # copies the headers and the generic interceptor rewrites them. As a
            # fallback, for example with a signer that doesn't copy them, if a retry
            # still has the header written here, start from its value before m/ was
            # added, so m/ is never added twice and nothing else is removed.
            previous = context.properties.get(_WRITTEN_USER_AGENT)
            base = previous[0] if previous and current == previous[1] else current
            written = f"{base} m/{encoded}"
            request.fields.set_field(Field(name="User-Agent", values=[written]))
            context.properties[_WRITTEN_USER_AGENT] = (base, written)
        return request

    def _register_retry_mode(self, properties: TypedProperties) -> None:
        # Adaptive is a subclass of standard, so it's checked first. Other
        # strategies have no feature ID and aren't reported.
        strategy = properties.get(RETRY_STRATEGY)
        if isinstance(strategy, AsyncAdaptiveRetryStrategy):
            register_feature_id(properties, AwsFeatureId.RETRY_MODE_ADAPTIVE)
        elif isinstance(strategy, AsyncStandardRetryStrategy):
            register_feature_id(properties, AwsFeatureId.RETRY_MODE_STANDARD)

    def _build_sdk_metadata(self) -> list[UserAgentComponent]:
        return [
            UserAgentComponent(_USERAGENT_SDK_NAME, __version__),
            UserAgentComponent("md", "smithy-core", smithy_core.__version__),
            *self._crt_version(),
        ]

    def _crt_version(self) -> list[UserAgentComponent]:
        try:
            import awscrt

            return [UserAgentComponent("md", "awscrt", awscrt.__version__)]
        except (ImportError, AttributeError):
            return []
