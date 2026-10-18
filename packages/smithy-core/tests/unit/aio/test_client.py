# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from collections.abc import AsyncIterator
from dataclasses import replace
from io import BytesIO, UnsupportedOperation
from typing import Any, cast
from unittest.mock import AsyncMock, Mock, patch

import pytest
from smithy_core.aio.client import AsyncClient
from smithy_core.aio.eventstream import DuplexEventStream, InputEventStream
from smithy_core.aio.interfaces import ClientTransport
from smithy_core.aio.retries import AdaptiveRetryStrategy, SimpleRetryStrategy
from smithy_core.aio.types import AsyncBytesReader
from smithy_core.auth import AuthOption
from smithy_core.exceptions import CallError, SmithyError, UnsupportedTransportError
from smithy_core.interceptors import (
    InputContext,
    Interceptor,
    InterceptorChain,
    OutputContext,
)
from smithy_core.response import EMPTY_RESPONSE_METADATA
from smithy_core.retries import ExponentialRetryBackoffStrategy
from smithy_core.shapes import ShapeID
from smithy_core.types import TypedProperties

from ._pipeline_harness import (
    DuplexTransport,
    NonDuplexTransport,
    StubEndpointResolver,
    StubEvent,
    StubEventReceiver,
    StubInput,
    StubOutput,
    StubRequest,
    UndeclaredTransport,
    client_call,
    pipeline_harness,
    retryable_client_call,
)


async def test_duplex_stream_raises_for_undeclared_transport() -> None:
    harness = pipeline_harness(UndeclaredTransport())

    with pytest.raises(UnsupportedTransportError) as exc_info:
        await harness.pipeline.duplex_stream(
            client_call(), StubEvent, StubEvent, StubEvent.deserialize
        )

    assert "UndeclaredTransport" in str(exc_info.value)
    assert "com.example#StreamingOperation" in str(exc_info.value)
    assert harness.protocol.serialize_request_calls == 0
    assert harness.transport.send_calls == 0


async def test_duplex_stream_raises_for_non_duplex_transport() -> None:
    harness = pipeline_harness(NonDuplexTransport())

    with pytest.raises(UnsupportedTransportError):
        await harness.pipeline.duplex_stream(
            client_call(), StubEvent, StubEvent, StubEvent.deserialize
        )

    assert harness.protocol.serialize_request_calls == 0
    assert harness.transport.send_calls == 0


async def test_duplex_stream_proceeds_for_duplex_transport() -> None:
    harness = pipeline_harness(DuplexTransport())

    stream = await harness.pipeline.duplex_stream(
        client_call(), StubEvent, StubEvent, StubEvent.deserialize
    )

    assert isinstance(stream, DuplexEventStream)
    output, output_stream = await stream.await_output()
    assert isinstance(output, StubOutput)
    assert isinstance(output_stream, StubEventReceiver)


async def test_input_stream_does_not_require_duplex_support() -> None:
    harness = pipeline_harness(NonDuplexTransport())

    stream = await harness.pipeline.input_stream(client_call(), StubEvent)

    assert isinstance(stream, InputEventStream)
    assert isinstance(await stream.await_output(), StubOutput)


async def test_response_metadata_attached_to_output() -> None:
    harness = pipeline_harness(NonDuplexTransport())

    output = await harness.pipeline(client_call())

    assert harness.protocol.extract_response_metadata_calls == 1
    assert output.response_metadata.request_id == "stub-request-id"
    assert output.response_metadata.extended_request_id == "stub-extended-request-id"
    assert output.response_metadata.http_status_code == 200


async def test_response_metadata_attached_to_error() -> None:
    harness = pipeline_harness(NonDuplexTransport())

    async def raise_modeled_error(**kwargs: Any) -> StubOutput:
        raise CallError("Rate exceeded")

    harness.protocol.deserialize_response = raise_modeled_error  # type: ignore[method-assign]

    with pytest.raises(CallError) as exc_info:
        await harness.pipeline(client_call())

    assert exc_info.value.response_metadata.request_id == "stub-request-id"
    assert exc_info.value.response_metadata.http_status_code == 200


async def test_response_metadata_kept_when_retry_times_out_waiting_for_send_token() -> (
    None
):
    # Adaptive mode: the first attempt is throttled, then the retry can't get a send
    # token. The caller should still get the throttle with its response metadata.
    harness = pipeline_harness(NonDuplexTransport())

    async def throttle(**kwargs: Any) -> StubOutput:
        raise CallError("Rate exceeded", is_retry_safe=True, is_throttling_error=True)

    harness.protocol.deserialize_response = throttle  # type: ignore[method-assign]
    strategy = AdaptiveRetryStrategy(max_attempts=3)
    timeout = TimeoutError("Failed to acquire 1.0 tokens within 30.0s")

    with (
        patch.object(
            strategy,
            "acquire_from_token_bucket",
            AsyncMock(side_effect=[None, timeout]),
        ),
        patch("smithy_core.aio.client.sleep", AsyncMock()),
    ):
        with pytest.raises(CallError, match="Rate exceeded") as exc_info:
            await harness.pipeline(retryable_client_call(strategy))

    assert harness.transport.send_calls == 1
    assert exc_info.value.response_metadata.request_id == "stub-request-id"
    assert exc_info.value.response_metadata.http_status_code == 200
    assert exc_info.value.__notes__ == [f"Retry not attempted: {timeout}"]


async def test_response_metadata_empty_when_no_response_received() -> None:
    harness = pipeline_harness(NonDuplexTransport())

    async def fail_to_send(**kwargs: Any) -> Any:
        raise CallError("Connection failed")

    harness.transport.send = fail_to_send  # type: ignore[method-assign]

    with pytest.raises(CallError) as exc_info:
        await harness.pipeline(client_call())

    assert exc_info.value.response_metadata is EMPTY_RESPONSE_METADATA
    assert exc_info.value.response_metadata.http_status_code is None
    assert harness.protocol.extract_response_metadata_calls == 0


async def test_failed_metadata_extraction_does_not_fail_the_call() -> None:
    harness = pipeline_harness(NonDuplexTransport())
    harness.protocol.extract_response_metadata_error = RuntimeError("boom")

    output = await harness.pipeline(client_call())

    assert output.response_metadata is EMPTY_RESPONSE_METADATA


async def test_response_metadata_attached_when_retries_are_exhausted() -> None:
    # Throttling and 5xx failures exit through the retry loop, which must carry
    # the response out with the error or they report no request ID.
    harness = pipeline_harness(NonDuplexTransport())

    async def raise_retryable_error(**kwargs: Any) -> StubOutput:
        raise CallError("Rate exceeded", is_retry_safe=True)

    harness.protocol.deserialize_response = raise_retryable_error  # type: ignore[method-assign]

    with pytest.raises(CallError) as exc_info:
        await harness.pipeline(retryable_client_call())

    assert exc_info.value.response_metadata.request_id == "stub-request-id"
    assert exc_info.value.response_metadata.http_status_code == 200


async def test_auth_option_signer_properties_override_scheme_defaults() -> None:
    harness = pipeline_harness(NonDuplexTransport())
    scheme = Mock()
    scheme.identity_resolver.return_value.get_identity = AsyncMock()
    scheme.signer_properties.return_value = {
        "region": "us-west-2",
        "service": "default",
    }
    sign = scheme.signer.return_value.sign = AsyncMock()
    option = AuthOption(
        scheme_id=ShapeID("com.example#auth"),
        identity_properties=TypedProperties({"identity_only": True}),
        signer_properties=TypedProperties({"service": "override"}),
    )
    call = replace(
        client_call(),
        auth_scheme_resolver=Mock(resolve_auth_scheme=Mock(return_value=[option])),
        supported_auth_schemes={option.scheme_id: scheme},
    )

    await harness.pipeline(call)

    assert sign.call_args.kwargs["properties"] == {
        "region": "us-west-2",
        "service": "override",
    }


class _ReplaceInput(Interceptor[Any, Any, Any, Any]):
    """Replaces the input before serialization and records what later hooks see."""

    def __init__(self, fail_after_modifying: bool = False) -> None:
        self.replacement = StubInput()
        self.fail_after_modifying = fail_after_modifying
        self.completion_request: Any = None

    def modify_before_serialization(self, context: InputContext[Any]) -> Any:
        return self.replacement

    def read_before_serialization(self, context: InputContext[Any]) -> None:
        if self.fail_after_modifying:
            raise RuntimeError("boom")

    def modify_before_completion(
        self, context: OutputContext[Any, Any, Any, Any]
    ) -> Any:
        self.completion_request = context.request
        return context.response


async def test_modified_input_is_serialized_and_used_to_resolve_endpoint() -> None:
    harness = pipeline_harness(NonDuplexTransport())
    interceptor = _ReplaceInput()
    resolver = StubEndpointResolver()
    call = replace(
        client_call(),
        interceptor=InterceptorChain([interceptor]),
        endpoint_resolver=resolver,
    )

    await harness.pipeline(call)

    assert harness.protocol.serialized_inputs == [interceptor.replacement]
    assert resolver.resolved_inputs == [interceptor.replacement]


async def test_modified_input_reaches_completion_when_serialization_fails() -> None:
    harness = pipeline_harness(NonDuplexTransport())
    interceptor = _ReplaceInput(fail_after_modifying=True)
    call = replace(client_call(), interceptor=InterceptorChain([interceptor]))

    with pytest.raises(SmithyError):
        await harness.pipeline(call)

    assert interceptor.completion_request is interceptor.replacement


class _CountingTransport:
    def __init__(self) -> None:
        self.close_calls = 0

    async def close(self) -> None:
        self.close_calls += 1


class _StubClient(AsyncClient):
    """Simulates a generated client's post-setup state via the public ctor."""

    def __init__(self, *, setup: bool = True) -> None:
        super().__init__()
        self.transport = _CountingTransport()
        if setup:
            self._transport = cast(ClientTransport[Any, Any], self.transport)
            self._setup_done = True

    @property
    def closed(self) -> bool:
        return self._closed


async def test_close_is_idempotent() -> None:
    client = _StubClient()

    await client.close()
    await client.close()

    assert client.closed is True
    assert client.transport.close_calls == 1


async def test_close_without_setup_does_not_touch_transport() -> None:
    client = _StubClient(setup=False)

    await client.close()

    assert client.closed is True
    assert client.transport.close_calls == 0


async def test_aenter_raises_on_closed_client() -> None:
    client = _StubClient()
    await client.close()

    with pytest.raises(RuntimeError):
        await client.__aenter__()


async def test_aexit_closes_client() -> None:
    client = _StubClient()

    async with client:
        pass

    assert client.closed is True
    assert client.transport.close_calls == 1


class BodyRecordingTransport(NonDuplexTransport):
    def __init__(self) -> None:
        super().__init__()
        self.bodies: list[bytes] = []

    async def send(self, request: Any) -> Any:
        self.bodies.append(await AsyncBytesReader(request.body).read())
        return await super().send(request)


async def _chunks() -> AsyncIterator[bytes]:
    yield b"foobar"


def _streaming_call_failing_once(
    harness: Any, body: Any, *, max_attempts: int = 2
) -> Any:
    request = StubRequest()
    request.body = body
    harness.protocol.serialize_request = lambda **kwargs: request  # type: ignore[method-assign]

    async def fail_first_attempt(**kwargs: Any) -> StubOutput:
        if harness.protocol.deserialize_response_calls == 0:
            harness.protocol.deserialize_response_calls += 1
            raise CallError("Service unavailable", is_retry_safe=True)
        return StubOutput()

    harness.protocol.deserialize_response = fail_first_attempt  # type: ignore[method-assign]
    return replace(
        client_call(),
        retry_strategy=SimpleRetryStrategy(
            backoff_strategy=ExponentialRetryBackoffStrategy(backoff_scale_value=0),
            max_attempts=max_attempts,
        ),
    )


async def test_seekable_data_stream_is_retried_from_its_start() -> None:
    harness = pipeline_harness(BodyRecordingTransport())
    body = BytesIO(b"foobar")
    body.seek(2)
    call = _streaming_call_failing_once(harness, AsyncBytesReader(body))

    await harness.pipeline(call)

    # The caller's position is where the body starts, so retries don't resend 'fo'.
    assert cast(BodyRecordingTransport, harness.transport).bodies == [b"obar", b"obar"]


async def test_non_seekable_data_stream_is_not_retried() -> None:
    harness = pipeline_harness(BodyRecordingTransport())
    call = _streaming_call_failing_once(harness, AsyncBytesReader(_chunks()))

    with pytest.raises(CallError, match="Service unavailable"):
        await harness.pipeline(call)

    assert cast(BodyRecordingTransport, harness.transport).bodies == [b"foobar"]


class UnrewindableBody:
    """A body that reports it's seekable but fails to seek."""

    def seekable(self) -> bool:
        return True

    def seek(self, offset: int, whence: int = 0) -> int:
        raise UnsupportedOperation("seek")

    async def read(self, size: int = -1) -> bytes:
        return b"foobar"


async def test_data_stream_that_fails_to_seek_is_sent_once() -> None:
    harness = pipeline_harness(BodyRecordingTransport())
    call = _streaming_call_failing_once(harness, UnrewindableBody())

    with pytest.raises(CallError, match="Service unavailable"):
        await harness.pipeline(call)

    assert cast(BodyRecordingTransport, harness.transport).bodies == [b"foobar"]


async def test_input_event_stream_is_not_retried() -> None:
    harness = pipeline_harness(NonDuplexTransport())
    call = _streaming_call_failing_once(harness, BytesIO(b""))

    stream = await harness.pipeline.input_stream(call, StubEvent)

    with pytest.raises(CallError, match="Service unavailable"):
        await stream.await_output()
    assert harness.transport.send_calls == 1
