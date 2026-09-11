# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from typing import Any

import pytest
from smithy_core.aio.eventstream import DuplexEventStream, InputEventStream
from smithy_core.exceptions import CallError, UnsupportedTransportError
from smithy_core.response import EMPTY_RESPONSE_METADATA

from ._pipeline_harness import (
    DuplexTransport,
    NonDuplexTransport,
    StubEvent,
    StubEventReceiver,
    StubOutput,
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
