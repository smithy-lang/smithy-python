# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from copy import copy
from typing import Any
from unittest.mock import Mock

import pytest
from smithy_aws_core.business_metrics import (
    FEATURE_IDS,
    AwsFeatureId,
    register_feature_id,
)
from smithy_aws_core.interceptors.user_agent import UserAgentInterceptor
from smithy_core import URI
from smithy_core.aio.retries import (
    RETRY_STRATEGY,
    AsyncAdaptiveRetryStrategy,
    AsyncSimpleRetryStrategy,
    AsyncStandardRetryStrategy,
)
from smithy_core.interceptors import InputContext, RequestContext
from smithy_core.types import TypedProperties
from smithy_http import Field, Fields
from smithy_http.aio import HTTPRequest
from smithy_http.interceptors.user_agent import USER_AGENT
from smithy_http.interceptors.user_agent import (
    UserAgentInterceptor as GenericUserAgentInterceptor,
)
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


_BASE_USER_AGENT = "aws-sdk-python/1.0.0 ua/2.1 lang/python#3.12"


def _interceptor() -> UserAgentInterceptor:
    return UserAgentInterceptor(
        ua_suffix=None, ua_app_id=None, sdk_version="1.0.0", service_id="svc"
    )


def _request(user_agent: str = _BASE_USER_AGENT) -> HTTPRequest:
    # The generic user agent interceptor writes the header before signing.
    return HTTPRequest(
        method="POST",
        destination=URI(host="example.com"),
        fields=Fields([Field(name="User-Agent", values=[user_agent])]),
        body=b"",
    )


def _transmit(
    interceptor: UserAgentInterceptor,
    properties: TypedProperties,
    request: HTTPRequest | None = None,
) -> str:
    context = RequestContext[Any, HTTPRequest](
        request=Mock(),
        transport_request=request if request is not None else _request(),
        properties=properties,
    )
    return interceptor.modify_before_transmit(context).fields["User-Agent"].as_string()


def test_appends_business_metrics() -> None:
    properties = TypedProperties()
    register_feature_id(properties, AwsFeatureId.RETRY_MODE_STANDARD)
    register_feature_id(properties, AwsFeatureId.ENDPOINT_OVERRIDE)
    assert _transmit(_interceptor(), properties) == f"{_BASE_USER_AGENT} m/E,N"


def test_skips_business_metrics_without_user_agent_header() -> None:
    properties = TypedProperties()
    register_feature_id(properties, AwsFeatureId.ENDPOINT_OVERRIDE)
    request = HTTPRequest(
        method="POST", destination=URI(host="example.com"), fields=Fields(), body=b""
    )
    context = RequestContext[Any, HTTPRequest](
        request=Mock(), transport_request=request, properties=properties
    )

    result = _interceptor().modify_before_transmit(context)

    assert "User-Agent" not in result.fields


def test_leaves_header_unchanged_without_features() -> None:
    assert _transmit(_interceptor(), TypedProperties()) == _BASE_USER_AGENT


def test_retry_does_not_duplicate_business_metrics() -> None:
    # A retry shallow-copies the request, so it starts with the previous attempt's
    # User-Agent, m/ included. The header must not have duplicate m/.
    interceptor = _interceptor()
    properties = TypedProperties()
    register_feature_id(properties, AwsFeatureId.ENDPOINT_OVERRIDE)
    request = _request()
    _transmit(interceptor, properties, request)
    retry = copy(request)

    user_agent = _transmit(interceptor, properties, retry)

    assert user_agent == f"{_BASE_USER_AGENT} m/N"


def test_retry_with_more_features_replaces_previous_business_metrics() -> None:
    interceptor = _interceptor()
    properties = TypedProperties()
    register_feature_id(properties, AwsFeatureId.ENDPOINT_OVERRIDE)
    request = _request()
    _transmit(interceptor, properties, request)
    register_feature_id(properties, AwsFeatureId.RETRY_MODE_STANDARD)

    user_agent = _transmit(interceptor, properties, copy(request))

    assert user_agent == f"{_BASE_USER_AGENT} m/N,E"


def test_keeps_m_prefixed_text_from_the_user() -> None:
    interceptor = _interceptor()
    properties = TypedProperties()
    register_feature_id(properties, AwsFeatureId.ENDPOINT_OVERRIDE)
    request = _request(f"{_BASE_USER_AGENT} myframework m/legacy-tag")

    user_agent = _transmit(interceptor, properties, request)

    assert user_agent == f"{_BASE_USER_AGENT} myframework m/legacy-tag m/N"


def test_retry_with_generic_interceptor_sends_business_metrics_once() -> None:
    # Mirrors a generated client, which runs both interceptors on every attempt.
    # A retried call must send the same User-Agent each time, with m/ only once,
    # and without removing anything the user added, such as the m/legacy-tag in
    # this test's suffix.
    generic = GenericUserAgentInterceptor()
    interceptor = UserAgentInterceptor(
        ua_suffix="myframework m/legacy-tag",
        ua_app_id=None,
        sdk_version="1.0.0",
        service_id="svc",
    )
    properties = TypedProperties()
    generic.read_before_execution(InputContext(request=Mock(), properties=properties))
    request: Any = _request()
    interceptor.read_after_serialization(
        RequestContext[Any, Any](
            request=Mock(), transport_request=request, properties=properties
        )
    )
    register_feature_id(properties, AwsFeatureId.ENDPOINT_OVERRIDE)

    user_agents: list[str] = []
    for _ in range(2):
        # Each attempt starts from a shallow copy, as retries do.
        context = RequestContext[Any, Any](
            request=Mock(), transport_request=copy(request), properties=properties
        )
        generic.modify_before_signing(context)
        request = interceptor.modify_before_transmit(context)
        user_agents.append(request.fields["User-Agent"].as_string())

    assert user_agents[0] == user_agents[1]
    assert user_agents[0].endswith(" myframework m/legacy-tag m/N")
    assert user_agents[0].count(" m/N") == 1


@pytest.mark.parametrize(
    ("retry_strategy", "expected"),
    [
        (AsyncStandardRetryStrategy(), [AwsFeatureId.RETRY_MODE_STANDARD]),
        (AsyncAdaptiveRetryStrategy(), [AwsFeatureId.RETRY_MODE_ADAPTIVE]),
        (AsyncSimpleRetryStrategy(), []),
        (None, []),
    ],
)
def test_registers_retry_mode(
    retry_strategy: Any, expected: list[AwsFeatureId]
) -> None:
    properties = TypedProperties()
    properties[USER_AGENT] = UserAgent()
    if retry_strategy is not None:
        properties[RETRY_STRATEGY] = retry_strategy
    context = RequestContext[Any, Any](
        request=Mock(), transport_request=Mock(), properties=properties
    )
    _interceptor().read_after_serialization(context)
    assert list(properties.get(FEATURE_IDS, {})) == expected


def test_registers_retry_mode_without_user_agent() -> None:
    properties = TypedProperties()
    properties[RETRY_STRATEGY] = AsyncStandardRetryStrategy()
    context = RequestContext[Any, Any](
        request=Mock(), transport_request=Mock(), properties=properties
    )
    _interceptor().read_after_serialization(context)
    assert list(properties[FEATURE_IDS]) == [AwsFeatureId.RETRY_MODE_STANDARD]
