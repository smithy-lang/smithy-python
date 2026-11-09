# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import logging
import uuid
from collections.abc import AsyncIterator, Callable, Iterator
from dataclasses import dataclass, field, replace
from io import BytesIO, UnsupportedOperation
from typing import Any, cast
from unittest.mock import AsyncMock, Mock, patch

import pytest
from smithy_core.aio.client import AsyncClient
from smithy_core.aio.eventstream import AsyncDuplexEventStream, AsyncInputEventStream
from smithy_core.aio.interfaces import AsyncClientTransport
from smithy_core.aio.types import AsyncBytesReader
from smithy_core.auth import RESOLVED_IDENTITY, AuthOption
from smithy_core.client import OPERATION as OPERATION_PROPERTY
from smithy_core.client import ClientCall
from smithy_core.endpoints import RESOLVED_ENDPOINT, EndpointAuthScheme
from smithy_core.exceptions import (
    CallError,
    ClientTimeoutError,
    ResourceLifecycleError,
    SmithyError,
    UnsupportedAuthSchemeError,
    UnsupportedTransportError,
)
from smithy_core.interceptors import (
    InputContext,
    Interceptor,
    InterceptorChain,
    OutputContext,
    RequestContext,
)
from smithy_core.response import EMPTY_RESPONSE_METADATA
from smithy_core.retries import (
    RETRY_STRATEGY,
    AdaptiveRetryStrategy,
    ExponentialRetryBackoffStrategy,
    SimpleRetryStrategy,
    StandardRetryStrategy,
)
from smithy_core.schemas import APIOperation, Schema
from smithy_core.shapes import ShapeID, ShapeType
from smithy_core.traits import IdempotencyTokenTrait
from smithy_core.types import TypedProperties

from ._pipeline_harness import (
    DATA_STREAM_OPERATION,
    OPERATION,
    TOKEN_OPERATION,
    DuplexTransport,
    NonDuplexTransport,
    StubEndpoint,
    StubEndpointResolver,
    StubEvent,
    StubEventReceiver,
    StubInput,
    StubOutput,
    StubRequest,
    TokenInput,
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

    assert isinstance(stream, AsyncDuplexEventStream)
    output, output_stream = await stream.await_output()
    assert isinstance(output, StubOutput)
    assert isinstance(output_stream, StubEventReceiver)


async def test_input_stream_does_not_require_duplex_support() -> None:
    harness = pipeline_harness(NonDuplexTransport())

    stream = await harness.pipeline.input_stream(client_call(), StubEvent)

    assert isinstance(stream, AsyncInputEventStream)
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
            strategy.rate_limiter,
            "_send_token_waits",
            Mock(side_effect=[iter(()), timeout]),
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


def _signing_call(
    scheme: Mock, option: AuthOption, endpoint: StubEndpoint
) -> ClientCall[Any, Any]:
    return replace(
        client_call(),
        auth_scheme_resolver=Mock(resolve_auth_scheme=Mock(return_value=[option])),
        supported_auth_schemes={option.scheme_id: scheme},
        endpoint_resolver=Mock(resolve_endpoint=Mock(return_value=endpoint)),
    )


async def test_endpoint_signer_properties_override_option_and_scheme_defaults() -> None:
    harness = pipeline_harness(NonDuplexTransport())
    scheme = Mock(scheme_id=ShapeID("com.example#auth"))
    scheme.identity_resolver.return_value.get_identity = AsyncMock()
    scheme.signer_properties.return_value = {
        "region": "default",
        "service": "default",
        "scope": "default",
    }
    sign = scheme.signer.return_value.sign = AsyncMock()
    option = AuthOption(
        scheme_id=scheme.scheme_id,
        identity_properties=TypedProperties(),
        signer_properties=TypedProperties({"service": "option", "scope": "option"}),
    )
    endpoint = StubEndpoint()
    endpoint.auth_schemes = (
        EndpointAuthScheme(
            scheme_id=ShapeID("com.example#other"),
            properties=TypedProperties({"region": "other"}),
        ),
        EndpointAuthScheme(
            scheme_id=scheme.scheme_id,
            properties=TypedProperties({"scope": "endpoint"}),
        ),
    )

    await harness.pipeline(_signing_call(scheme, option, endpoint))

    assert sign.call_args.kwargs["properties"] == {
        "region": "default",
        "service": "option",
        "scope": "endpoint",
    }


async def test_signing_fails_when_the_endpoint_lists_other_auth_schemes() -> None:
    harness = pipeline_harness(NonDuplexTransport())
    scheme = Mock(scheme_id=ShapeID("com.example#auth"))
    scheme.identity_resolver.return_value.get_identity = AsyncMock()
    option = AuthOption(
        scheme_id=scheme.scheme_id,
        identity_properties=TypedProperties(),
        signer_properties=TypedProperties(),
    )
    endpoint = StubEndpoint()
    endpoint.auth_schemes = (
        EndpointAuthScheme(scheme_id=ShapeID("com.example#other")),
    )

    with pytest.raises(UnsupportedAuthSchemeError, match=r"com\.example#other"):
        await harness.pipeline(_signing_call(scheme, option, endpoint))
    scheme.signer.return_value.sign.assert_not_called()


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


class _AsyncEndpointResolver:
    def __init__(self) -> None:
        self.resolved_inputs: list[Any] = []

    async def resolve_endpoint(self, params: Any) -> StubEndpoint:
        self.resolved_inputs.append(params.input)
        return StubEndpoint()


async def test_async_endpoint_resolvers_are_awaited() -> None:
    harness = pipeline_harness(NonDuplexTransport())
    resolver = _AsyncEndpointResolver()
    call = replace(client_call(), endpoint_resolver=resolver)

    await harness.pipeline(call)

    assert resolver.resolved_inputs == [call.input]


class _RecordHooks(Interceptor[Any, Any, Any, Any]):
    def __init__(self, events: list[str]) -> None:
        self.events = events

    def read_before_attempt(self, context: RequestContext[Any, Any]) -> None:
        self.events.append("read_before_attempt")

    def modify_before_signing(self, context: RequestContext[Any, Any]) -> Any:
        self.events.append("modify_before_signing")
        return context.transport_request

    def read_before_signing(self, context: RequestContext[Any, Any]) -> None:
        self.events.append("read_before_signing")

    def read_after_signing(self, context: RequestContext[Any, Any]) -> None:
        self.events.append("read_after_signing")


async def test_identity_resolves_before_the_endpoint_and_signing_after_hooks() -> None:
    events: list[str] = []
    identity = Mock()

    async def get_identity(**kwargs: Any) -> Any:
        events.append("get_identity")
        return identity

    class _Resolver(StubEndpointResolver):
        def resolve_endpoint(self, params: Any) -> Any:
            events.append("resolve_endpoint")
            assert params.context[RESOLVED_IDENTITY] is identity
            return super().resolve_endpoint(params)

    def signer_properties(**kwargs: Any) -> dict[str, Any]:
        events.append("signer_properties")
        assert kwargs["context"][RESOLVED_ENDPOINT] is not None
        return {}

    async def sign(**kwargs: Any) -> Any:
        events.append("sign")
        assert kwargs["identity"] is identity
        return kwargs["request"]

    def resolve_auth_scheme(**kwargs: Any) -> list[AuthOption]:
        events.append("resolve_auth_scheme")
        return [option]

    harness = pipeline_harness(NonDuplexTransport())
    scheme = Mock()
    scheme.identity_resolver.return_value.get_identity = get_identity
    scheme.signer_properties = signer_properties
    scheme.signer.return_value.sign = sign
    option = AuthOption(scheme_id=ShapeID("com.example#auth"))
    call = replace(
        client_call(),
        interceptor=InterceptorChain([_RecordHooks(events)]),
        auth_scheme_resolver=Mock(resolve_auth_scheme=resolve_auth_scheme),
        supported_auth_schemes={option.scheme_id: scheme},
        endpoint_resolver=_Resolver(),
    )

    await harness.pipeline(call)

    assert events == [
        "read_before_attempt",
        "resolve_auth_scheme",
        "get_identity",
        "resolve_endpoint",
        "modify_before_signing",
        "read_before_signing",
        "signer_properties",
        "sign",
        "read_after_signing",
    ]
    assert call.context[RESOLVED_IDENTITY] is identity


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


class _StubClient(AsyncClient[Any]):
    """Simulates a generated client's post-setup state via the public ctor."""

    def __init__(self, *, setup: bool = True) -> None:
        super().__init__()
        self.transport = _CountingTransport()
        if setup:
            self._transport = cast(AsyncClientTransport[Any, Any], self.transport)
            self._setup_done = True

    @property
    def closed(self) -> bool:
        return self._closed


def test_build_call_adds_retry_strategy_to_request_properties() -> None:
    retry_strategy = StandardRetryStrategy()
    config = Mock(interceptors=[])
    client = _StubClient()
    _, call = client._build_call(  # pyright: ignore[reportPrivateUsage]
        cast(Any, Mock()),
        cast(Any, Mock()),
        config=config,
        retry_strategy=retry_strategy,
    )

    assert call.context[RETRY_STRATEGY] is retry_strategy
    assert call.retry_strategy is retry_strategy


def test_build_call_adds_operation_to_request_properties() -> None:
    operation = cast(Any, Mock())
    client = _StubClient()
    _, call = client._build_call(  # pyright: ignore[reportPrivateUsage]
        cast(Any, Mock()),
        operation,
        config=Mock(interceptors=[]),
        retry_strategy=StandardRetryStrategy(),
    )

    assert call.context[OPERATION_PROPERTY] is operation
    assert call.operation is operation


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

    with pytest.raises(ResourceLifecycleError):
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
    harness: Any, body: Any, *, operation: Any = DATA_STREAM_OPERATION
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
        operation=operation,
        retry_strategy=SimpleRetryStrategy(
            backoff_strategy=ExponentialRetryBackoffStrategy(backoff_scale_value=0),
            max_attempts=2,
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


class UnrewindableBody:
    """A body that reports it's seekable but fails to seek."""

    def seekable(self) -> bool:
        return True

    def seek(self, offset: int, whence: int = 0) -> int:
        raise UnsupportedOperation("seek")

    async def read(self, size: int = -1) -> bytes:
        return b"foobar"


@pytest.mark.parametrize(
    "factory",
    [lambda: AsyncBytesReader(_chunks()), UnrewindableBody],
    ids=["not-seekable", "fails-to-seek"],
)
async def test_data_stream_that_cant_be_rewound_is_sent_once(
    factory: Callable[[], Any],
) -> None:
    harness = pipeline_harness(BodyRecordingTransport())
    call = _streaming_call_failing_once(harness, factory())

    with pytest.raises(CallError, match="Service unavailable"):
        await harness.pipeline(call)

    assert cast(BodyRecordingTransport, harness.transport).bodies == [b"foobar"]


class SeekBackFailsBody(UnrewindableBody):
    """A body that reports its position but fails to seek back to it."""

    def seek(self, offset: int, whence: int = 0) -> int:
        if whence == 1:
            return 0
        raise UnsupportedOperation("seek")


async def test_data_stream_that_fails_to_rewind_returns_the_attempts_error() -> None:
    harness = pipeline_harness(BodyRecordingTransport())
    call = _streaming_call_failing_once(harness, SeekBackFailsBody())

    with pytest.raises(CallError, match="Service unavailable") as exc_info:
        await harness.pipeline(call)

    assert cast(BodyRecordingTransport, harness.transport).bodies == [b"foobar"]
    assert any(
        note.startswith("Retry not attempted") for note in exc_info.value.__notes__
    )


class _CountingGenerator:
    def __init__(self, *tokens: str) -> None:
        self.tokens = list(tokens) or ["generated-token"]
        self.calls = 0

    def __call__(self) -> str:
        token = self.tokens[self.calls % len(self.tokens)]
        self.calls += 1
        return token


@pytest.fixture
def token_generator() -> Iterator[_CountingGenerator]:
    generator = _CountingGenerator("first-token", "second-token", "third-token")
    with patch("smithy_core._pipeline._default_idempotency_token", new=generator):
        yield generator


def _token_call(
    input: Any,
    *,
    interceptor: Interceptor[Any, Any, Any, Any] | None = None,
    retry_strategy: Any = None,
) -> Any:
    return replace(
        retryable_client_call(retry_strategy),
        input=input,
        operation=TOKEN_OPERATION,
        interceptor=InterceptorChain([interceptor] if interceptor else []),
    )


async def test_unset_idempotency_token_is_generated_once(
    token_generator: _CountingGenerator,
) -> None:
    harness = pipeline_harness(NonDuplexTransport())

    await harness.pipeline(_token_call(TokenInput(message="hi")))

    assert token_generator.calls == 1
    [serialized] = harness.protocol.serialized_inputs
    assert serialized.client_token == "first-token"
    assert serialized.message == "hi"


async def test_set_idempotency_token_is_sent_unchanged(
    token_generator: _CountingGenerator,
) -> None:
    harness = pipeline_harness(NonDuplexTransport())
    input = TokenInput(client_token="caller-token")

    await harness.pipeline(_token_call(input))

    assert token_generator.calls == 0
    assert harness.protocol.serialized_inputs[0] is input
    assert input.client_token == "caller-token"


class _FailingTwiceTransport(BodyRecordingTransport):
    async def send(self, request: Any) -> Any:
        response = await super().send(request)
        if self.send_calls <= 2:
            raise CallError("Service unavailable", is_retry_safe=True)
        return response


async def test_idempotency_token_is_the_same_on_every_retry(
    token_generator: _CountingGenerator,
) -> None:
    harness = pipeline_harness(_FailingTwiceTransport())

    def serialize_request(**kwargs: Any) -> StubRequest:
        harness.protocol.serialize_request_calls += 1
        request = StubRequest()
        request.body = kwargs["input"].client_token.encode()
        return request

    harness.protocol.serialize_request = serialize_request  # type: ignore[method-assign]
    strategy = SimpleRetryStrategy(
        backoff_strategy=ExponentialRetryBackoffStrategy(backoff_scale_value=0),
        max_attempts=3,
    )

    await harness.pipeline(_token_call(TokenInput(), retry_strategy=strategy))

    assert harness.protocol.serialize_request_calls == 1
    assert harness.transport.send_calls == 3
    assert cast(BodyRecordingTransport, harness.transport).bodies == [
        b"first-token",
        b"first-token",
        b"first-token",
    ]
    assert token_generator.calls == 1


async def test_empty_string_idempotency_token_is_sent_unchanged(
    token_generator: _CountingGenerator,
) -> None:
    harness = pipeline_harness(NonDuplexTransport())
    input = TokenInput(client_token="")

    await harness.pipeline(_token_call(input))

    # Only an unset (None) token is filled; "" is an explicit caller value.
    assert token_generator.calls == 0
    [serialized] = harness.protocol.serialized_inputs
    assert serialized is input
    assert serialized.client_token == ""


_STRING_SCHEMA = Schema(id=ShapeID("smithy.api#String"), shape_type=ShapeType.STRING)

_PASCAL_TOKEN_OPERATION: APIOperation[Any, Any] = APIOperation(
    static_schema=(
        ShapeType.OPERATION.value,
        "com.example",
        "PascalTokenOperation",
        0,
        Schema.collection(
            id=ShapeID("com.example#PascalTokenInput"),
            members={
                "ClientToken": {
                    "target": _STRING_SCHEMA,
                    "traits": [IdempotencyTokenTrait()],
                },
            },
        ),
        Schema.collection(id=ShapeID("com.example#PascalTokenOutput"), members={}),
        (),
    ),
    effective_auth_schemes=[],
)


async def test_pascal_case_token_member_is_filled_on_its_python_field(
    token_generator: _CountingGenerator,
) -> None:
    harness = pipeline_harness(NonDuplexTransport())
    call = replace(_token_call(TokenInput()), operation=_PASCAL_TOKEN_OPERATION)

    await harness.pipeline(call)

    # The model member "ClientToken" maps to the Python field "client_token".
    [serialized] = harness.protocol.serialized_inputs
    assert serialized.client_token == "first-token"


async def test_caller_input_is_not_mutated_by_token_fill(
    token_generator: _CountingGenerator,
) -> None:
    harness = pipeline_harness(NonDuplexTransport())
    input = TokenInput(message="hi")

    await harness.pipeline(_token_call(input))

    assert input.client_token is None
    [serialized] = harness.protocol.serialized_inputs
    assert serialized is not input
    assert serialized.client_token == "first-token"


async def test_input_without_idempotency_member_is_passed_through(
    token_generator: _CountingGenerator,
) -> None:
    harness = pipeline_harness(NonDuplexTransport())
    call = retryable_client_call()

    await harness.pipeline(call)

    assert token_generator.calls == 0
    assert harness.protocol.serialized_inputs[0] is call.input


async def test_default_idempotency_token_is_a_uuid4() -> None:
    harness = pipeline_harness(NonDuplexTransport())

    await harness.pipeline(_token_call(TokenInput()))
    await harness.pipeline(_token_call(TokenInput()))

    first, second = (i.client_token for i in harness.protocol.serialized_inputs)
    assert uuid.UUID(first).version == 4
    assert first != second


def test_idempotency_token_field_name_is_cached() -> None:
    operation = replace(TOKEN_OPERATION)
    first = operation._idempotency_token_field  # pyright: ignore[reportPrivateUsage]

    assert first == "client_token"
    assert operation.__dict__["_idempotency_token_field"] == "client_token"


class _RecordTokens(Interceptor[Any, Any, Any, Any]):
    def __init__(self, *, rebuild_input: bool = False) -> None:
        self.rebuild_input = rebuild_input
        self.read_before_execution_input: Any = None
        self.modify_before_serialization_token: Any = "unset"
        self.read_before_serialization_token: Any = None

    def read_before_execution(self, context: InputContext[Any]) -> None:
        self.read_before_execution_input = context.request

    def modify_before_serialization(self, context: InputContext[Any]) -> Any:
        self.modify_before_serialization_token = context.request.client_token
        if self.rebuild_input:
            return TokenInput(message="rebuilt")
        return context.request

    def read_before_serialization(self, context: InputContext[Any]) -> None:
        self.read_before_serialization_token = context.request.client_token


async def test_token_is_filled_after_modify_before_serialization(
    token_generator: _CountingGenerator,
) -> None:
    harness = pipeline_harness(NonDuplexTransport())
    interceptor = _RecordTokens()
    input = TokenInput()

    await harness.pipeline(_token_call(input, interceptor=interceptor))

    assert interceptor.read_before_execution_input is input
    assert interceptor.modify_before_serialization_token is None
    assert interceptor.read_before_serialization_token == "first-token"


async def test_input_rebuilt_by_an_interceptor_still_gets_a_token(
    token_generator: _CountingGenerator,
) -> None:
    harness = pipeline_harness(NonDuplexTransport())
    interceptor = _RecordTokens(rebuild_input=True)

    await harness.pipeline(_token_call(TokenInput(), interceptor=interceptor))

    [serialized] = harness.protocol.serialized_inputs
    assert serialized.message == "rebuilt"
    assert serialized.client_token == "first-token"


class _NonDataclassTokenInput:
    def __init__(self) -> None:
        self.client_token: str | None = None

    def serialize(self, serializer: Any) -> None:
        pass


async def test_non_dataclass_input_is_passed_through(
    token_generator: _CountingGenerator,
) -> None:
    harness = pipeline_harness(NonDuplexTransport())
    input = _NonDataclassTokenInput()

    await harness.pipeline(_token_call(input))

    assert token_generator.calls == 0
    assert harness.protocol.serialized_inputs[0] is input


@dataclass(kw_only=True)
class _PostInitTokenInput:
    client_token: str | None = None
    message: str | None = None
    post_init_calls: int = field(default=0, compare=False)

    def __post_init__(self) -> None:
        self.post_init_calls += 1

    def serialize(self, serializer: Any) -> None:
        pass


@dataclass(kw_only=True, frozen=True)
class _FrozenTokenInput:
    client_token: str | None = None

    def serialize(self, serializer: Any) -> None:
        pass


async def test_token_fill_does_not_rerun_post_init(
    token_generator: _CountingGenerator,
) -> None:
    harness = pipeline_harness(NonDuplexTransport())
    input = _PostInitTokenInput(message="hi")

    await harness.pipeline(_token_call(input))

    [serialized] = harness.protocol.serialized_inputs
    assert serialized is not input
    assert serialized.client_token == "first-token"
    assert serialized.message == "hi"
    assert serialized.post_init_calls == 1
    assert input.client_token is None


async def test_frozen_dataclass_input_gets_a_token(
    token_generator: _CountingGenerator,
) -> None:
    harness = pipeline_harness(NonDuplexTransport())
    input = _FrozenTokenInput()

    await harness.pipeline(_token_call(input))

    [serialized] = harness.protocol.serialized_inputs
    assert serialized.client_token == "first-token"
    assert input.client_token is None


@dataclass(kw_only=True)
class _MisnamedTokenInput:
    token: str | None = None

    def serialize(self, serializer: Any) -> None:
        pass


async def test_input_without_the_derived_field_is_passed_through(
    token_generator: _CountingGenerator, caplog: pytest.LogCaptureFixture
) -> None:
    harness = pipeline_harness(NonDuplexTransport())
    input = _MisnamedTokenInput()

    with caplog.at_level(logging.WARNING):
        await harness.pipeline(_token_call(input))

    assert token_generator.calls == 0
    assert harness.protocol.serialized_inputs[0] is input
    [record] = [r for r in caplog.records if "idempotency token" in r.message]
    assert record.levelno == logging.WARNING
    # Logged through the client's logger, alongside the rest of the pipeline's logs
    assert record.name == harness.pipeline._logger.name  # pyright: ignore[reportPrivateUsage]


class _SetToken(Interceptor[Any, Any, Any, Any]):
    def modify_before_serialization(self, context: InputContext[Any]) -> Any:
        return replace(context.request, client_token="interceptor-token")


async def test_token_set_by_an_interceptor_is_sent_unchanged(
    token_generator: _CountingGenerator,
) -> None:
    harness = pipeline_harness(NonDuplexTransport())

    await harness.pipeline(_token_call(TokenInput(), interceptor=_SetToken()))

    assert token_generator.calls == 0
    [serialized] = harness.protocol.serialized_inputs
    assert serialized.client_token == "interceptor-token"


class _RecordCompletion(Interceptor[Any, Any, Any, Any]):
    def __init__(self) -> None:
        self.completion_response: Any = None
        self.after_execution_response: Any = None

    def modify_before_completion(
        self, context: OutputContext[Any, Any, Any, Any]
    ) -> Any:
        self.completion_response = context.response
        return context.response

    def read_after_execution(self, context: OutputContext[Any, Any, Any, Any]) -> None:
        self.after_execution_response = context.response


async def test_failing_token_generation_fails_the_call() -> None:
    harness = pipeline_harness(NonDuplexTransport())
    interceptor = _RecordCompletion()
    error = RuntimeError("no entropy")

    def generator() -> str:
        raise error

    with patch("smithy_core._pipeline._default_idempotency_token", new=generator):
        with pytest.raises(SmithyError) as exc_info:
            await harness.pipeline(_token_call(TokenInput(), interceptor=interceptor))

    assert exc_info.value.__cause__ is error
    assert interceptor.completion_response is error
    assert interceptor.after_execution_response is error
    assert harness.protocol.serialize_request_calls == 0
    assert harness.transport.send_calls == 0


async def test_input_event_stream_is_not_retried() -> None:
    harness = pipeline_harness(NonDuplexTransport())
    call = _streaming_call_failing_once(harness, BytesIO(b""), operation=OPERATION)

    stream = await harness.pipeline.input_stream(call, StubEvent)

    with pytest.raises(CallError, match="Service unavailable"):
        await stream.await_output()
    assert harness.transport.send_calls == 1


class _ConnectionRefused(TimeoutError):
    """Mimics transports that raise connection failures as timeouts."""


class _TimingOutTransport(NonDuplexTransport):
    TIMEOUT_EXCEPTIONS = (TimeoutError,)


@pytest.mark.parametrize(
    ("error", "message"),
    [
        (
            _ConnectionRefused("Failed to establish a new connection"),
            "A timeout error occurred (_ConnectionRefused: Failed to establish a new"
            " connection).",
        ),
        (TimeoutError(), "A timeout error occurred (TimeoutError)."),
    ],
)
async def test_timeout_errors_name_their_cause(error: Exception, message: str) -> None:
    transport = _TimingOutTransport()
    transport.send = AsyncMock(side_effect=error)  # type: ignore[method-assign]
    harness = pipeline_harness(transport)

    with pytest.raises(ClientTimeoutError) as exc_info:
        await harness.pipeline(client_call())

    assert str(exc_info.value) == message
    assert exc_info.value.__cause__ is error


class _TrackedBody:
    def __init__(self) -> None:
        self.closed = False

    async def read(self, size: int = -1) -> bytes:
        return b""

    async def close(self) -> None:
        self.closed = True


class _TrackedBodyTransport(NonDuplexTransport):
    def __init__(self) -> None:
        super().__init__()
        self.bodies: list[_TrackedBody] = []

    async def send(self, request: Any) -> Any:
        self.send_calls += 1
        body = _TrackedBody()
        self.bodies.append(body)
        return Mock(body=body)


async def test_failed_attempts_close_their_response_bodies() -> None:
    transport = _TrackedBodyTransport()
    harness = pipeline_harness(transport)

    async def raise_retryable_error(**kwargs: Any) -> StubOutput:
        raise CallError("Rate exceeded", is_retry_safe=True)

    harness.protocol.deserialize_response = raise_retryable_error  # type: ignore[method-assign]
    strategy = SimpleRetryStrategy(
        backoff_strategy=ExponentialRetryBackoffStrategy(backoff_scale_value=0),
        max_attempts=2,
    )

    with pytest.raises(CallError):
        await harness.pipeline(retryable_client_call(strategy))

    assert len(transport.bodies) == 2
    assert all(body.closed for body in transport.bodies)


async def test_successful_response_body_is_left_open() -> None:
    transport = _TrackedBodyTransport()
    harness = pipeline_harness(transport)

    await harness.pipeline(retryable_client_call())

    assert [body.closed for body in transport.bodies] == [False]


async def test_failure_closing_a_body_does_not_hide_the_error() -> None:
    transport = _TrackedBodyTransport()
    harness = pipeline_harness(transport)

    async def fail_close() -> None:
        raise OSError("already gone")

    async def raise_error(**kwargs: Any) -> StubOutput:
        transport.bodies[0].close = fail_close  # type: ignore[method-assign]
        raise CallError("original")

    harness.protocol.deserialize_response = raise_error  # type: ignore[method-assign]

    with pytest.raises(CallError, match="original"):
        await harness.pipeline(retryable_client_call())
