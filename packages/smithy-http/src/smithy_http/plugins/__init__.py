#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from typing import Any, Protocol

from smithy_core.interceptors import Interceptor

from smithy_http.interceptors.user_agent import UserAgentInterceptor


class _InterceptorConfig(Protocol):
    interceptors: list[Interceptor[Any, Any, Any, Any]]


def user_agent_plugin(config: _InterceptorConfig) -> None:
    config.interceptors.append(UserAgentInterceptor())
