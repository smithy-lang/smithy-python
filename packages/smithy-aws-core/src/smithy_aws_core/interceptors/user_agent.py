#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
# pyright: reportMissingTypeStubs=false
from typing import Any

import smithy_core
from smithy_core.interceptors import Interceptor, RequestContext
from smithy_http.interceptors.user_agent import USER_AGENT
from smithy_http.user_agent import RawStringUserAgentComponent, UserAgentComponent

from .. import __version__

_USERAGENT_SDK_NAME = "aws-sdk-python"


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

    def read_after_serialization(self, context: RequestContext[Any, Any]) -> None:
        if USER_AGENT in context.properties:
            user_agent = context.properties[USER_AGENT]
            user_agent.sdk_metadata = self._build_sdk_metadata()
            user_agent.api_metadata.append(
                UserAgentComponent("api", self._service_id, self._sdk_version)
            )

            if self._ua_app_id is not None:
                user_agent.additional_metadata.append(
                    UserAgentComponent("app", self._ua_app_id)
                )

            if self._ua_suffix is not None:
                user_agent.additional_metadata.append(
                    RawStringUserAgentComponent(self._ua_suffix)
                )

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
