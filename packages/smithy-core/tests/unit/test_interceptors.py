# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from typing import Any, cast

import pytest
from smithy_core.interceptors import (
    InputContext,
    Interceptor,
    InterceptorChain,
    OutputContext,
    RequestContext,
    ResponseContext,
)
from smithy_core.types import TypedProperties


def _context() -> OutputContext[Any, Any, Any, Any]:
    return OutputContext(
        request=cast(Any, ""),
        transport_request="",
        transport_response="",
        response=cast(Any, ""),
        properties=TypedProperties(),
    )


MODIFY_HOOKS = [
    "modify_before_serialization",
    "modify_before_retry_loop",
    "modify_before_signing",
    "modify_before_transmit",
    "modify_before_deserialization",
    "modify_before_attempt_completion",
    "modify_before_completion",
]


class _Appender(Interceptor[Any, Any, Any, Any]):
    """Appends a suffix to the value each modify hook receives."""

    def __init__(self, suffix: str) -> None:
        self._suffix = suffix

    def modify_before_serialization(self, context: InputContext[Any]) -> Any:
        return context.request + self._suffix

    def modify_before_retry_loop(self, context: RequestContext[Any, Any]) -> Any:
        return context.transport_request + self._suffix

    def modify_before_signing(self, context: RequestContext[Any, Any]) -> Any:
        return context.transport_request + self._suffix

    def modify_before_transmit(self, context: RequestContext[Any, Any]) -> Any:
        return context.transport_request + self._suffix

    def modify_before_deserialization(
        self, context: ResponseContext[Any, Any, Any]
    ) -> Any:
        return context.transport_response + self._suffix

    def modify_before_attempt_completion(
        self, context: OutputContext[Any, Any, Any, Any]
    ) -> Any:
        return cast(str, context.response) + self._suffix

    def modify_before_completion(
        self, context: OutputContext[Any, Any, Any, Any]
    ) -> Any:
        return cast(str, context.response) + self._suffix


@pytest.mark.parametrize("hook", MODIFY_HOOKS)
def test_chain_passes_each_modification_to_the_next_interceptor(hook: str) -> None:
    chain = InterceptorChain([_Appender("a"), _Appender("b")])

    assert getattr(chain, hook)(_context()) == "ab"


@pytest.mark.parametrize("hook", MODIFY_HOOKS)
def test_chain_keeps_modifications_from_earlier_interceptors(hook: str) -> None:
    # The base interceptor returns what it was given, which must be the value the
    # interceptor before it returned, not the original.
    chain = InterceptorChain([_Appender("a"), Interceptor()])

    assert getattr(chain, hook)(_context()) == "a"
