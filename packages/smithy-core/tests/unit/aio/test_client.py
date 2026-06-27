#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""Tests for the async request pipeline in ``smithy_core.aio.client``."""

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Self

from smithy_core import URI
from smithy_core.aio.client import ClientCall, RequestPipeline
from smithy_core.aio.interfaces import (
    ClientProtocol,
    ClientTransport,
    StreamingBlob,
)
from smithy_core.aio.interfaces.eventstream import EventPublisher, EventReceiver
from smithy_core.aio.retries import SimpleRetryStrategy
from smithy_core.auth import NoAuthResolver
from smithy_core.deserializers import ShapeDeserializer
from smithy_core.documents import TypeRegistry
from smithy_core.endpoints import Endpoint, EndpointResolverParams
from smithy_core.interceptors import Interceptor
from smithy_core.interfaces import Endpoint as _Endpoint
from smithy_core.interfaces import TypedProperties as TypedPropertiesInterface
from smithy_core.interfaces import URI as URIInterface
from smithy_core.schemas import APIOperation, Schema
from smithy_core.serializers import ShapeSerializer
from smithy_core.shapes import ShapeID, ShapeType
from smithy_core.traits import StreamingTrait
from smithy_core.types import TypedProperties

_NAMESPACE = "smithy.test"


# --- Minimal shapes ------------------------------------------------------------------


class _Input:
    """A minimal SerializeableShape used as operation input and event type."""

    def serialize(self, serializer: ShapeSerializer) -> None:
        pass


class _Output:
    """A minimal DeserializeableShape used as operation output."""

    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> "_Output":
        return cls()


# --- Minimal transport request/response ----------------------------------------------


@dataclass
class _Request:
    destination: URIInterface
    body: StreamingBlob = b""

    async def consume_body_async(self) -> bytes:
        return b""

    def consume_body(self) -> bytes:
        return b""


@dataclass
class _Response:
    status: int = 200

    @property
    def body(self) -> StreamingBlob:
        return b""

    async def consume_body_async(self) -> bytes:
        return b""

    def consume_body(self) -> bytes:
        return b""


# --- Minimal protocol / transport / publisher ----------------------------------------


class _NoOpPublisher(EventPublisher[_Input]):
    """A no-op EventPublisher returned for the input stream."""

    async def send(self, event: _Input) -> None:
        pass

    async def close(self) -> None:
        pass

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()


class _Protocol(ClientProtocol[_Request, _Response]):
    @property
    def id(self) -> ShapeID:
        return ShapeID(f"{_NAMESPACE}#TestProtocol")

    def serialize_request(
        self,
        *,
        operation: APIOperation[Any, Any],
        input: Any,
        endpoint: URIInterface,
        context: TypedPropertiesInterface,
    ) -> _Request:
        return _Request(destination=URI(host="example.com"))

    def set_service_endpoint(
        self, *, request: _Request, endpoint: _Endpoint
    ) -> _Request:
        return request

    def create_event_publisher(
        self,
        *,
        operation: APIOperation[Any, Any],
        request: _Request,
        event_type: Any,
        context: TypedPropertiesInterface,
        auth_scheme: Any = None,
    ) -> EventPublisher[Any]:
        return _NoOpPublisher()

    def create_event_receiver(
        self,
        *,
        operation: APIOperation[Any, Any],
        request: _Request,
        response: _Response,
        event_type: Any,
        event_deserializer: Callable[[ShapeDeserializer], Any],
        context: TypedPropertiesInterface,
    ) -> EventReceiver[Any]:
        raise NotImplementedError("This is only for tests.")

    async def deserialize_response(
        self,
        *,
        operation: APIOperation[Any, Any],
        request: _Request,
        response: _Response,
        error_registry: TypeRegistry,
        context: TypedPropertiesInterface,
    ) -> Any:
        return _Output()


class _InstantTransport(ClientTransport[_Request, _Response]):
    """A transport whose ``send`` returns immediately."""

    TIMEOUT_EXCEPTIONS: tuple[type[Exception], ...] = ()

    async def send(self, request: _Request) -> _Response:
        return _Response()


class _BlockingEndpointResolver:
    """Endpoint resolver that parks until ``release`` is set.

    Endpoint resolution is awaited inside ``_handle_attempt`` *before* the
    pipeline sets the request future, so blocking here gives the test a
    deterministic point at which to cancel the in-flight stream call while the
    request future has not yet been resolved.
    """

    def __init__(self) -> None:
        self.entered = asyncio.Event()
        self.release = asyncio.Event()

    async def resolve_endpoint(self, params: EndpointResolverParams[Any]) -> _Endpoint:
        self.entered.set()
        await self.release.wait()
        return Endpoint(uri=URI(host="example.com"))


# --- Operation/call construction ------------------------------------------------------


def _streaming_operation() -> APIOperation[_Input, _Output]:
    """Build an operation whose input has a streaming member (non-retryable)."""
    blob = Schema(id=ShapeID("smithy.api#Blob"), shape_type=ShapeType.BLOB)
    stream_member = Schema.member(
        id=ShapeID(f"{_NAMESPACE}#Input$stream"),
        target=blob,
        index=0,
        member_traits=[StreamingTrait()],
    )
    input_schema = Schema(
        id=ShapeID(f"{_NAMESPACE}#Input"),
        shape_type=ShapeType.STRUCTURE,
        members=[stream_member],
    )
    output_schema = Schema(
        id=ShapeID(f"{_NAMESPACE}#Output"), shape_type=ShapeType.STRUCTURE
    )
    op_schema = Schema(
        id=ShapeID(f"{_NAMESPACE}#Operation"), shape_type=ShapeType.OPERATION
    )
    return APIOperation(
        input=_Input,
        output=_Output,
        schema=op_schema,
        input_schema=input_schema,
        output_schema=output_schema,
        error_registry=TypeRegistry({}),
        effective_auth_schemes=[],
        error_schemas=[],
    )


def _make_call(
    operation: APIOperation[_Input, _Output],
    endpoint_resolver: _BlockingEndpointResolver,
) -> ClientCall[_Input, _Output]:
    return ClientCall(
        input=_Input(),
        operation=operation,
        context=TypedProperties(),
        interceptor=Interceptor(),
        auth_scheme_resolver=NoAuthResolver(),
        supported_auth_schemes={},
        endpoint_resolver=endpoint_resolver,
        retry_strategy=SimpleRetryStrategy(),
    )


# --- The regression test --------------------------------------------------------------


async def test_cancelled_request_future_does_not_raise_invalid_state() -> None:
    """A cancelled request future must not cause an InvalidStateError.

    ``input_stream``/``duplex_stream`` run ``_execute_request`` in a background
    task and pass it a request future, which the pipeline resolves once the
    transport send has been kicked off. If the consumer awaiting that future is
    cancelled (e.g. the caller is cancelled or times out), asyncio cancels the
    future. The still-running background task then reaches
    ``request_future.set_result(...)`` on a cancelled future, which raises
    ``asyncio.InvalidStateError`` unless the set is guarded.

    Cancelling the future directly here is exactly the call asyncio makes
    internally when the task awaiting it is cancelled.
    """
    resolver = _BlockingEndpointResolver()
    pipeline = RequestPipeline(protocol=_Protocol(), transport=_InstantTransport())
    call = _make_call(_streaming_operation(), resolver)

    request_future: asyncio.Future[Any] = asyncio.Future()
    task = asyncio.ensure_future(
        pipeline._execute_request(call, request_future)  # pyright: ignore[reportPrivateUsage]
    )

    # Park the pipeline inside endpoint resolution, before it resolves the
    # future, then cancel the future as a cancelled consumer would.
    await resolver.entered.wait()
    request_future.cancel()
    assert request_future.cancelled()

    # Let the pipeline proceed to the (now-guarded) set_result.
    resolver.release.set()

    # With the guard the request completes cleanly; without it, set_result on
    # the cancelled future raises InvalidStateError (surfaced as SmithyError).
    output, _ = await task
    assert output is not None


async def test_non_streaming_request_succeeds() -> None:
    """A normal (non-stream) request with no request future is unaffected."""
    resolver = _BlockingEndpointResolver()
    resolver.release.set()
    pipeline = RequestPipeline(protocol=_Protocol(), transport=_InstantTransport())
    call = _make_call(_streaming_operation(), resolver)

    output = await pipeline(call)
    assert output is not None
