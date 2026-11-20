# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import uuid
from types import SimpleNamespace
from typing import Any
from unittest.mock import Mock

import pytest
from smithy_aws_core.interceptors.retry_headers import RetryHeadersInterceptor
from smithy_core import URI
from smithy_core.interceptors import RequestContext
from smithy_core.retries import RETRY_STRATEGY
from smithy_core.types import TypedProperties
from smithy_http import Field, Fields, HTTPRequest


def _context() -> RequestContext[Any, HTTPRequest]:
    return RequestContext[Any, HTTPRequest](
        request=Mock(),
        transport_request=HTTPRequest(
            method="POST", destination=URI(host="example.com"), fields=Fields()
        ),
        properties=TypedProperties(),
    )


def _invocation_id() -> str:
    request = RetryHeadersInterceptor().modify_before_retry_loop(_context())
    return request.fields["amz-sdk-invocation-id"].as_string()


def test_invocation_id_is_a_version_4_uuid() -> None:
    assert uuid.UUID(_invocation_id()).version == 4


def test_invocation_id_is_the_same_on_every_attempt() -> None:
    interceptor = RetryHeadersInterceptor()
    context = _context()
    request = interceptor.modify_before_retry_loop(context)
    invocation_id = request.fields["amz-sdk-invocation-id"].as_string()
    for _ in range(3):
        interceptor.read_before_attempt(context)
        request = interceptor.modify_before_signing(context)
        assert request.fields["amz-sdk-invocation-id"].as_string() == invocation_id


def test_invocation_id_differs_between_calls() -> None:
    assert _invocation_id() != _invocation_id()


def test_invocation_id_replaces_a_callers_value() -> None:
    context = _context()
    context.transport_request.fields.set_field(
        Field(name="amz-sdk-invocation-id", values=["from-the-caller"])
    )
    request = RetryHeadersInterceptor().modify_before_retry_loop(context)
    invocation_id = request.fields["amz-sdk-invocation-id"].as_string()
    assert uuid.UUID(invocation_id).version == 4


_NO_STRATEGY = object()


def _request_header(strategy: Any) -> str:
    interceptor = RetryHeadersInterceptor()
    context = _context()
    if strategy is not _NO_STRATEGY:
        context.properties[RETRY_STRATEGY] = strategy
    interceptor.read_before_attempt(context)
    request = interceptor.modify_before_signing(context)
    return request.fields["amz-sdk-request"].as_string()


@pytest.mark.parametrize(
    "strategy",
    [
        _NO_STRATEGY,
        SimpleNamespace(),
        SimpleNamespace(max_attempts=None),
        SimpleNamespace(max_attempts=0),
        SimpleNamespace(max_attempts=True),
    ],
    ids=["no strategy", "no attribute", "None", "0", "True"],
)
def test_request_header_omits_unknown_max(strategy: Any) -> None:
    assert _request_header(strategy) == "attempt=1"


def test_request_header_sends_max_attempts() -> None:
    assert _request_header(SimpleNamespace(max_attempts=3)) == "attempt=1; max=3"


def test_request_header_replaces_a_callers_value() -> None:
    interceptor = RetryHeadersInterceptor()
    context = _context()
    context.transport_request.fields.set_field(
        Field(name="amz-sdk-request", values=["from-the-caller"])
    )
    interceptor.read_before_attempt(context)
    request = interceptor.modify_before_signing(context)
    assert request.fields["amz-sdk-request"].as_string() == "attempt=1"
