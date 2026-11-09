# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import logging
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
    # Each field holds its own name, so a hook that returns the wrong field shows up.
    return OutputContext(
        request=cast(Any, "request"),
        transport_request="transport_request",
        transport_response="transport_response",
        response=cast(Any, "response"),
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

# Each modify hook mapped to the context field it replaces.
MODIFY_HOOKS = {
    "modify_before_serialization": "request",
    "modify_before_retry_loop": "transport_request",
    "modify_before_signing": "transport_request",
    "modify_before_transmit": "transport_request",
    "modify_before_deserialization": "transport_response",
    "modify_before_attempt_completion": "response",
    "modify_before_completion": "response",
}


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


@pytest.mark.parametrize("hook,field", MODIFY_HOOKS.items())
def test_chain_passes_each_modification_to_the_next_interceptor(
    hook: str, field: str
) -> None:
    # This also covers a default interceptor undoing earlier changes, since the base
    # hooks return the context's value just as _Appender reads it.
    chain = InterceptorChain([_Appender("a"), _Appender("b")])

    assert getattr(chain, hook)(_context()) == f"{field}ab"


@pytest.mark.parametrize("hook", MODIFY_HOOKS)
def test_chain_reuses_the_context_when_nothing_changes(hook: str) -> None:
    context = _context()
    later = Mock(spec=Interceptor)

    getattr(InterceptorChain([Interceptor(), later]), hook)(context)

    assert getattr(later, hook).call_args.args[0] is context


@pytest.mark.parametrize("hook", READ_HOOKS + list(MODIFY_HOOKS))
def test_chain_calls_only_the_matching_hook(hook: str) -> None:
    interceptors = [Mock(spec=Interceptor), Mock(spec=Interceptor)]

    getattr(InterceptorChain(interceptors), hook)(_context())

    for interceptor in interceptors:
        assert [name for name, *_ in interceptor.method_calls] == [hook]


@pytest.mark.parametrize("hook", MODIFY_HOOKS)
def test_modify_hook_returning_none_raises(hook: str) -> None:
    forgot_to_return = Mock(spec=Interceptor)
    getattr(forgot_to_return, hook).return_value = None
    after = Mock(spec=Interceptor)

    with pytest.raises(TypeError, match=hook):
        getattr(InterceptorChain([forgot_to_return, after]), hook)(_context())

    assert not after.method_calls


def _raising(name: str, calls: list[str]) -> Any:
    """An interceptor whose every hook records its name and raises."""

    def raise_error(context: Any) -> None:
        calls.append(name)
        raise RuntimeError(name)

    interceptor = Mock()
    for hook in READ_HOOKS + list(MODIFY_HOOKS):
        getattr(interceptor, hook).side_effect = raise_error
    return interceptor


@pytest.mark.parametrize("hook", READ_HOOKS)
def test_read_hook_runs_every_interceptor_and_raises_the_last_error(
    hook: str, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG, logger="smithy_core.interceptors")
    calls: list[str] = []
    chain = InterceptorChain([_raising(name, calls) for name in ("1", "2", "3")])

    with pytest.raises(RuntimeError, match="3"):
        getattr(chain, hook)(_context())

    assert calls == ["1", "2", "3"]
    dropped = [str(record.exc_info[1]) for record in caplog.records if record.exc_info]
    assert dropped == ["1", "2"]


@pytest.mark.parametrize("hook", READ_HOOKS)
def test_read_hook_raises_when_a_later_interceptor_succeeds(hook: str) -> None:
    calls: list[str] = []
    succeeds = Mock(spec=Interceptor)
    chain = InterceptorChain([_raising("1", calls), succeeds])

    with pytest.raises(RuntimeError, match="1"):
        getattr(chain, hook)(_context())

    assert [name for name, *_ in succeeds.method_calls] == [hook]


@pytest.mark.parametrize("hook", ["read_after_attempt", "read_after_execution"])
def test_completion_read_hook_passes_the_error_to_later_interceptors(
    hook: str,
) -> None:
    later = Mock(spec=Interceptor)
    chain = InterceptorChain([_raising("1", []), later])

    with pytest.raises(RuntimeError):
        getattr(chain, hook)(_context())

    response = getattr(later, hook).call_args.args[0].response
    assert isinstance(response, RuntimeError)
    assert str(response) == "1"


@pytest.mark.parametrize("hook", MODIFY_HOOKS)
def test_modify_hook_stops_at_the_first_error(hook: str) -> None:
    calls: list[str] = []
    chain = InterceptorChain([_raising(name, calls) for name in ("1", "2")])

    with pytest.raises(RuntimeError, match="1"):
        getattr(chain, hook)(_context())

    assert calls == ["1"]
