# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from typing import Any, cast
from unittest.mock import Mock

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


READ_HOOKS = [
    "read_before_execution",
    "read_before_serialization",
    "read_after_serialization",
    "read_before_attempt",
    "read_before_signing",
    "read_after_signing",
    "read_before_transmit",
    "read_after_transmit",
    "read_before_deserialization",
    "read_after_deserialization",
    "read_after_attempt",
    "read_after_execution",
]

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


def _raising(name: str, calls: list[str]) -> Any:
    """An interceptor whose every hook records its name and raises."""

    def raise_error(context: Any) -> None:
        calls.append(name)
        raise RuntimeError(name)

    interceptor = Mock()
    for hook in READ_HOOKS + MODIFY_HOOKS:
        getattr(interceptor, hook).side_effect = raise_error
    return interceptor


@pytest.mark.parametrize("hook", READ_HOOKS)
def test_read_hook_runs_every_interceptor_and_raises_the_last_error(
    hook: str, caplog: pytest.LogCaptureFixture
) -> None:
    calls: list[str] = []
    chain = InterceptorChain([_raising(name, calls) for name in ("1", "2", "3")])

    with pytest.raises(RuntimeError, match="3"):
        getattr(chain, hook)(_context())

    assert calls == ["1", "2", "3"]
    dropped = [str(record.exc_info[1]) for record in caplog.records if record.exc_info]
    assert dropped == ["1", "2"]


@pytest.mark.parametrize("hook", MODIFY_HOOKS)
def test_modify_hook_stops_at_the_first_error(hook: str) -> None:
    calls: list[str] = []
    chain = InterceptorChain([_raising(name, calls) for name in ("1", "2")])

    with pytest.raises(RuntimeError, match="1"):
        getattr(chain, hook)(_context())

    assert calls == ["1"]
