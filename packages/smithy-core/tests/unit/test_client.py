#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from collections.abc import Sequence
from dataclasses import replace
from typing import Any, cast
from unittest.mock import Mock, patch

import pytest
from smithy_core.client import Client, ClientCall, RequestPipeline
from smithy_core.exceptions import CallError, ClientTimeoutError, SmithyError
from smithy_core.interceptors import Interceptor, InterceptorChain
from smithy_core.program import Program
from smithy_core.retries import (
    RETRY_STRATEGY,
    SimpleRetryStrategy,
    StandardRetryStrategy,
)

from .aio._pipeline_harness import (
    TOKEN_OPERATION,
    StubOutput,
    StubProtocol,
    StubResponse,
    TokenInput,
    retryable_client_call,
)


def test_build_call_adds_retry_strategy_to_request_properties() -> None:
    retry_strategy = StandardRetryStrategy()
    _, call = Client()._build_call(  # pyright: ignore[reportPrivateUsage]
        cast(Any, Mock()),
        cast(Any, Mock()),
        config=Mock(interceptors=[]),
        retry_strategy=retry_strategy,
    )

    assert call.context[RETRY_STRATEGY] is retry_strategy
    assert call.retry_strategy is retry_strategy


# The sync pipeline closes the response bodies callers never see. A streamed body
# holds its connection until it's read to the end or closed.


class _TrackedBody:
    def __init__(self) -> None:
        self.closed = False

    def read(self, size: int = -1) -> bytes:
        return b""

    def close(self) -> None:
        self.closed = True


class _TrackedResponse:
    def __init__(self) -> None:
        self.body = _TrackedBody()


class _TrackedBodyTransport:
    TIMEOUT_EXCEPTIONS: tuple[type[Exception], ...] = ()

    def __init__(self) -> None:
        self.responses: list[_TrackedResponse] = []

    def send(self, request: Any) -> _TrackedResponse:
        response = _TrackedResponse()
        self.responses.append(response)
        return response

    @property
    def bodies(self) -> list[_TrackedBody]:
        return [response.body for response in self.responses]


class _SyncStubProtocol(StubProtocol):
    """Deserializes synchronously, failing the first ``failures`` attempts."""

    def __init__(self, failures: Sequence[Exception] = ()) -> None:
        super().__init__()
        self.failures = list(failures)

    def deserialize_response_program(self, **kwargs: Any) -> Program[StubOutput]:
        return (yield lambda: self.deserialize_response_sync())

    def deserialize_response_sync(self) -> StubOutput:
        self.deserialize_response_calls += 1
        if self.failures:
            raise self.failures.pop(0)
        return StubOutput()


class _NoBackoff:
    def compute_next_backoff_delay(self, retry_attempt: int) -> float:
        return 0


def _call(
    *interceptors: Interceptor[Any, Any, Any, Any], max_attempts: int = 3
) -> ClientCall[Any, Any]:
    return replace(
        retryable_client_call(
            SimpleRetryStrategy(
                backoff_strategy=_NoBackoff(), max_attempts=max_attempts
            )
        ),
        interceptor=InterceptorChain(list(interceptors)),
    )


def _pipeline(
    transport: _TrackedBodyTransport, protocol: _SyncStubProtocol
) -> RequestPipeline[Any, Any]:
    return RequestPipeline(protocol=cast(Any, protocol), transport=cast(Any, transport))


def test_retried_attempts_close_their_bodies() -> None:
    transport = _TrackedBodyTransport()
    protocol = _SyncStubProtocol(
        [CallError("Rate exceeded", is_retry_safe=True), ClientTimeoutError()]
    )

    _pipeline(transport, protocol)(_call())

    # Two failed attempts, then the success the caller gets back, still open.
    assert [body.closed for body in transport.bodies] == [True, True, False]


def test_failed_calls_close_their_last_body() -> None:
    transport = _TrackedBodyTransport()
    protocol = _SyncStubProtocol([CallError("Rate exceeded", is_retry_safe=True)] * 2)

    with pytest.raises(CallError, match="Rate exceeded"):
        _pipeline(transport, protocol)(_call(max_attempts=2))

    assert [body.closed for body in transport.bodies] == [True, True]


class _Fail(Interceptor[Any, Any, Any, Any]):
    def __init__(self, hook: str) -> None:
        def fail(context: Any) -> Any:
            raise RuntimeError(f"{hook} failed")

        setattr(self, hook, fail)


@pytest.mark.parametrize(
    "hook",
    [
        "read_after_deserialization",
        "modify_before_attempt_completion",
        "modify_before_completion",
        "read_after_execution",
    ],
)
def test_bodies_are_closed_when_a_hook_fails_after_a_response(hook: str) -> None:
    transport = _TrackedBodyTransport()

    with pytest.raises(SmithyError, match=f"{hook} failed"):
        _pipeline(transport, _SyncStubProtocol())(_call(_Fail(hook)))

    assert [body.closed for body in transport.bodies] == [True]


def test_failure_closing_a_body_does_not_hide_the_error() -> None:
    transport = _TrackedBodyTransport()
    protocol = _SyncStubProtocol([CallError("original")])

    def fail_close() -> None:
        raise OSError("already gone")

    original_send = transport.send

    def send(request: Any) -> _TrackedResponse:
        response = original_send(request)
        response.body.close = fail_close  # type: ignore[method-assign]
        return response

    transport.send = send  # type: ignore[method-assign]

    with pytest.raises(CallError, match="original"):
        _pipeline(transport, protocol)(_call(max_attempts=1))


class _SyncProtocol(StubProtocol):
    def deserialize_response_program(self, **kwargs: Any) -> Program[StubOutput]:
        self.deserialize_response_calls += 1
        return (yield lambda: StubOutput())


class _SyncTransport:
    TIMEOUT_EXCEPTIONS: tuple[type[Exception], ...] = ()

    def send(self, request: Any) -> StubResponse:
        return StubResponse()


def test_sync_pipeline_fills_unset_idempotency_token() -> None:
    protocol = _SyncProtocol()
    pipeline: RequestPipeline[Any, Any] = RequestPipeline(
        protocol=cast(Any, protocol), transport=cast(Any, _SyncTransport())
    )
    input = TokenInput()
    call = replace(retryable_client_call(), input=input, operation=TOKEN_OPERATION)

    with patch(
        "smithy_core._pipeline._default_idempotency_token", new=lambda: "sync-token"
    ):
        pipeline(call)

    [serialized] = protocol.serialized_inputs
    assert serialized.client_token == "sync-token"
    assert input.client_token is None
