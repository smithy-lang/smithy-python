# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from dataclasses import replace
from typing import Any, cast
from unittest.mock import AsyncMock, Mock

import pytest
from smithy_core.aio.client import AsyncClient
from smithy_core.aio.eventstream import DuplexEventStream, InputEventStream
from smithy_core.aio.interfaces import ClientTransport
from smithy_core.auth import AuthOption
from smithy_core.exceptions import CallError, UnsupportedTransportError
from smithy_core.response import EMPTY_RESPONSE_METADATA
from smithy_core.shapes import ShapeID
from smithy_core.types import TypedProperties

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
