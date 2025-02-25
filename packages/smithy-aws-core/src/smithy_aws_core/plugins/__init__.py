#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from typing import Any

from smithy_aws_core.interceptors.user_agent import UserAgentInterceptor


# TODO: Define a Protocol for Config w/ interceptor method?
def user_agent_plugin(config: Any) -> None:
    config.interceptors.append(
        UserAgentInterceptor(
            ua_suffix=config.user_agent_extra,
            ua_app_id=config.sdk_ua_app_id,
        )
    )
