# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from typing import Any
from unittest.mock import Mock

import pytest
from smithy_aws_core.interceptors.user_agent import UserAgentInterceptor
from smithy_core.interceptors import RequestContext
from smithy_core.types import TypedProperties
from smithy_http.interceptors.user_agent import USER_AGENT
from smithy_http.user_agent import UserAgent, UserAgentComponent


def _user_agent_string() -> str:
    interceptor = UserAgentInterceptor(
        ua_suffix=None, ua_app_id=None, sdk_version="1.0.0", service_id="svc"
    )
    properties = TypedProperties()
    properties[USER_AGENT] = UserAgent(
        language_metadata=[UserAgentComponent("lang", "python", "3.12")]
    )
    context = RequestContext[Any, Any](
        request=Mock(), transport_request=Mock(), properties=properties
    )
    interceptor.read_after_serialization(context)
    return str(properties[USER_AGENT])


def test_adds_execution_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AWS_EXECUTION_ENV", "AWS_Lambda_python3.12")
    assert "lang/python#3.12 exec-env/AWS_Lambda_python3.12" in _user_agent_string()


def test_omits_execution_env_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AWS_EXECUTION_ENV", raising=False)
    assert "exec-env/" not in _user_agent_string()
