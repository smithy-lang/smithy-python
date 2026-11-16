# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import uuid
from typing import Any
from unittest.mock import Mock

from smithy_aws_core.interceptors.retry_headers import RetryHeadersInterceptor
from smithy_core import URI
from smithy_core.interceptors import RequestContext
from smithy_core.types import TypedProperties
from smithy_http import Field, Fields, HTTPRequest


def _invocation_id() -> str:
    context = RequestContext[Any, HTTPRequest](
        request=Mock(),
        transport_request=HTTPRequest(
            method="POST", destination=URI(host="example.com"), fields=Fields()
        ),
        properties=TypedProperties(),
    )
    request = RetryHeadersInterceptor().modify_before_retry_loop(context)
    return request.fields["amz-sdk-invocation-id"].as_string()


def test_invocation_id_is_a_version_4_uuid() -> None:
    assert uuid.UUID(_invocation_id()).version == 4


def test_invocation_id_is_the_same_on_every_attempt() -> None:
    interceptor = RetryHeadersInterceptor()
    context = RequestContext[Any, HTTPRequest](
        request=Mock(),
        transport_request=HTTPRequest(
            method="POST", destination=URI(host="example.com"), fields=Fields()
        ),
        properties=TypedProperties(),
    )
    request = interceptor.modify_before_retry_loop(context)
    invocation_id = request.fields["amz-sdk-invocation-id"].as_string()
    for _ in range(3):
        interceptor.read_before_attempt(context)
        request = interceptor.modify_before_signing(context)
        assert request.fields["amz-sdk-invocation-id"].as_string() == invocation_id


def test_invocation_id_differs_between_calls() -> None:
    assert _invocation_id() != _invocation_id()


def test_invocation_id_replaces_a_callers_value() -> None:
    context = RequestContext[Any, HTTPRequest](
        request=Mock(),
        transport_request=HTTPRequest(
            method="POST", destination=URI(host="example.com"), fields=Fields()
        ),
        properties=TypedProperties(),
    )
    context.transport_request.fields.set_field(
        Field(name="amz-sdk-invocation-id", values=["from-the-caller"])
    )
    request = RetryHeadersInterceptor().modify_before_retry_loop(context)
    invocation_id = request.fields["amz-sdk-invocation-id"].as_string()
    assert uuid.UUID(invocation_id).version == 4
