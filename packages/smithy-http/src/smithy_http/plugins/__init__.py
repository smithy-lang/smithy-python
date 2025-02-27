#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from smithy_core.interfaces.config import Config
from smithy_http.interceptors.user_agent import UserAgentInterceptor

def user_agent_plugin(config: Config) -> None:
    config.interceptors.append(UserAgentInterceptor())
