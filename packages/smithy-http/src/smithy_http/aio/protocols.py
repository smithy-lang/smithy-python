# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import asyncio
from collections.abc import AsyncIterable, Callable
from inspect import iscoroutinefunction
from typing import TYPE_CHECKING, Any, cast

from smithy_core.aio.interfaces import (
    AsyncByteStream,
    AsyncClientProtocol,
    AsyncWriter,
)
from smithy_core.aio.interfaces import StreamingBlob as AsyncStreamingBlob
from smithy_core.aio.interfaces.auth import AsyncAuthScheme
from smithy_core.aio.interfaces.eventstream import (
    AsyncEventPublisher,
    AsyncEventReceiver,
)
from smithy_core.aio.types import AsyncBytesReader
from smithy_core.deserializers import DeserializeableShape, ShapeDeserializer
from smithy_core.documents import TypeRegistry
from smithy_core.exceptions import (
    ExpectationNotMetError,
    MissingDependencyError,
    UnsupportedStreamError,
)
from smithy_core.interfaces import StreamingBlob as SyncStreamingBlob
from smithy_core.interfaces import (
    TypedProperties,
)
from smithy_core.schemas import APIOperation
from smithy_core.serializers import SerializeableShape
from smithy_core.types import PropertyKey

from ..protocols import (
    _HttpBindingProtocolBase,  # pyright: ignore[reportPrivateUsage]
    _HttpProtocolBase,  # pyright: ignore[reportPrivateUsage]
    _RpcProtocolBase,  # pyright: ignore[reportPrivateUsage]
    _RpcV2CborProtocolBase,  # pyright: ignore[reportPrivateUsage]
    _RpcV2ProtocolBase,  # pyright: ignore[reportPrivateUsage]
)
from .interfaces import HTTPRequest, HTTPResponse

__all__ = [
    "AsyncHttpBindingClientProtocol",
    "AsyncHttpClientProtocol",
    "AsyncRpcClientProtocol",
    "AsyncRpcV2CborClientProtocol",
]

try:
    from smithy_aws_event_stream._private.deserializers import (
        EventDeserializer as _EventDeserializer,
    )
    from smithy_aws_event_stream._private.serializers import (
        EventSerializer as _EventSerializer,
    )
    from smithy_aws_event_stream.aio import (
        AWSEventPublisher,
        AWSEventReceiver,
        SigningConfig,
    )
    from smithy_aws_event_stream.events import Event as _Event
    from smithy_aws_event_stream.events import EventMessage as _EventMessage
    from smithy_aws_event_stream.exceptions import MissingInitialResponse
    from smithy_core.aio.types import AsyncBytesProvider

    _HAS_EVENT_STREAM = True
except ImportError:
    _HAS_EVENT_STREAM = False  # type: ignore

if TYPE_CHECKING:
    from smithy_aws_event_stream._private.deserializers import (
        EventDeserializer as _EventDeserializer,
    )
    from smithy_aws_event_stream._private.serializers import (
        EventSerializer as _EventSerializer,
    )
    from smithy_aws_event_stream.aio import (
        AWSEventPublisher,
        AWSEventReceiver,
        SigningConfig,
    )
    from smithy_aws_event_stream.events import Event as _Event
    from smithy_aws_event_stream.events import EventMessage as _EventMessage
    from smithy_aws_event_stream.exceptions import MissingInitialResponse
    from smithy_core.aio.types import AsyncBytesProvider
    from typing_extensions import TypeForm


_EVENT_STREAM_CONTENT_TYPE = "application/vnd.amazon.eventstream"

_EVENT_STREAM_SOURCE = PropertyKey(
    key="smithy_http_event_stream_source", value_type=AsyncByteStream
)
"""Carries the response-body reader already positioned past the initial-response event.

RPC output streams read their initial response off the first event frame in
``deserialize_response``; the receiver then continues from this same reader so the
frames stay in order.
"""

_PREFETCHED_EVENT = PropertyKey(
    key="smithy_http_event_stream_prefetched", value_type=object
)
"""Carries a first stream event already decoded off the body in ``deserialize_response``.

When the output has no ``initial-response`` the first frame is a real event, not the
output; it is stashed here so the receiver replays it before reading the next frame.
"""

_INITIAL_REQUEST_EVENT = PropertyKey(
    key="smithy_http_event_stream_initial_request", value_type=object
)
"""Carries the serialized ``initial-request`` event awaiting the publisher.

The frame is NOT poured into the request body: it must be signed as the first event
in the signature chain (off the request signature), so the publisher writes it.
"""


def _assert_event_stream() -> None:
    if not _HAS_EVENT_STREAM:
        raise MissingDependencyError(
            "Attempted to use event streams, but smithy-aws-event-stream "
            "is not installed."
        )


class AsyncHttpClientProtocol(
    _HttpProtocolBase, AsyncClientProtocol[HTTPRequest, HTTPResponse]
):
    """An HTTP-based protocol."""

    async def create_event_publisher[
        OperationInput: SerializeableShape,
        OperationOutput: DeserializeableShape,
        Event: SerializeableShape,
    ](
        self,
        *,
        operation: "APIOperation[OperationInput, OperationOutput]",
        request: HTTPRequest,
        event_type: "TypeForm[Event]",
        context: TypedProperties,
        auth_scheme: AsyncAuthScheme[Any, Any, Any, Any] | None = None,
    ) -> AsyncEventPublisher[Event]:
        _assert_event_stream()
        signing_config: SigningConfig | None = None
        if auth_scheme is not None:
            event_signer = auth_scheme.event_signer(request=request)
            if event_signer is not None:
                signing_config = SigningConfig(
                    signer=event_signer,
                    signing_properties=auth_scheme.signer_properties(context=context),
                    identity_resolver=auth_scheme.identity_resolver(context=context),
                    identity_properties=auth_scheme.identity_properties(
                        context=context
                    ),
                )

        # The HTTP body must be an async writeable. Protocols that serialize an event
        # stream request are responsible for setting one.
        body = request.body
        if not isinstance(body, AsyncWriter) or not iscoroutinefunction(body.write):
            raise UnsupportedStreamError(
                "Input streams require an async write function, but none was present "
                "on the serialized HTTP request."
            )

        initial_message = cast(
            "_EventMessage | None", context.get(_INITIAL_REQUEST_EVENT)
        )
        publisher = AWSEventPublisher[Event](
            payload_codec=self.payload_codec,
            async_writer=body,
            signing_config=signing_config,
            initial_message=initial_message,
        )
        # Flush initial-request now so a duplex peer that gates its initial-response on
        # it isn't deadlocked waiting for a frame the publisher would defer.
        await publisher.prepare()
        return publisher

    def create_event_receiver[
        OperationInput: SerializeableShape,
        OperationOutput: DeserializeableShape,
        Event: DeserializeableShape,
    ](
        self,
        *,
        operation: "APIOperation[OperationInput, OperationOutput]",
        request: HTTPRequest,
        response: HTTPResponse,
        event_type: "TypeForm[Event]",
        event_deserializer: Callable[[ShapeDeserializer], Event],
        context: TypedProperties,
    ) -> AsyncEventReceiver[Event]:
        _assert_event_stream()
        return AWSEventReceiver(
            payload_codec=self.payload_codec,
            source=AsyncBytesReader(response.body),
            deserializer=event_deserializer,
        )


class AsyncHttpBindingClientProtocol(_HttpBindingProtocolBase, AsyncHttpClientProtocol):
    """An HTTP-based protocol that uses HTTP binding traits."""

    _ASYNC_BODY = True

    async def deserialize_response[
        OperationInput: "SerializeableShape",
        OperationOutput: "DeserializeableShape",
    ](
        self,
        *,
        operation: APIOperation[OperationInput, OperationOutput],
        request: HTTPRequest,
        response: HTTPResponse,
        error_registry: TypeRegistry,
        context: TypedProperties,
    ) -> OperationOutput:
        if not self._is_success(operation, context, response):
            raise self._create_error(
                operation=operation,
                request=request,
                response=response,
                response_body=await self._buffer_async_body(response.body),
                error_registry=error_registry,
                context=context,
            )

        # if body is not streaming and is async, we have to buffer it
        body: SyncStreamingBlob | None = None
        if not self._has_streaming_output(operation):
            body = await self._buffer_async_body(response.body)

        return self._deserialize_output(operation, response, body)

    async def _buffer_async_body(self, stream: AsyncStreamingBlob) -> SyncStreamingBlob:
        if isinstance(stream, bytes | bytearray):
            return stream

        match stream:
            case AsyncByteStream():
                if not iscoroutinefunction(stream.read):
                    return stream  # type: ignore
                return await stream.read()
            case AsyncIterable():
                full = b""
                async for chunk in stream:
                    full += chunk
                return full
            case _:
                return stream


class AsyncRpcClientProtocol(_RpcProtocolBase, AsyncHttpClientProtocol):
    """Base for the RPC-based protocols (awsJson, awsQuery, rpcv2).

    RPC protocols serialize the whole operation input through a codec rather than via
    HTTP bindings. This base carries the event-stream framing they share: per the
    Amazon event stream specification, an RPC event stream carries the operation input
    and output as ``initial-request`` and ``initial-response`` events at the head of
    the stream rather than as the HTTP request and response bodies.

    Subclasses build their own HTTP request envelope (path, headers) and response
    handling; they delegate the event-stream body to the helpers here, gated on the
    operation's ``input_stream_member`` / ``output_stream_member``. A protocol that
    never models an event stream (awsQuery) simply never reaches these helpers.
    """

    def _request_body(self, payload: bytes) -> AsyncBytesReader:
        return AsyncBytesReader(payload)

    def _build_initial_request_body(
        self, input: SerializeableShape, context: TypedProperties
    ) -> "AsyncBytesProvider":
        """Serialize the ``initial-request`` event and stash it for the publisher.

        The frame is not written into the returned body: the publisher must write it
        as its first (signed) frame. The body is an empty async writer the publisher
        appends to.
        """
        _assert_event_stream()
        serializer = _EventSerializer(
            payload_codec=self.payload_codec, is_client_mode=True
        )
        input.serialize(serializer)
        initial = serializer.get_result()
        if initial is None:
            raise ExpectationNotMetError(
                "Expected an initial-request event to be serialized, but was None."
            )
        context[_INITIAL_REQUEST_EVENT] = initial
        return AsyncBytesProvider()

    async def _deserialize_event_stream_response[
        OperationInput: SerializeableShape,
        OperationOutput: DeserializeableShape,
    ](
        self,
        *,
        operation: APIOperation[OperationInput, OperationOutput],
        response: HTTPResponse,
        context: TypedProperties,
    ) -> OperationOutput:
        # initial-response is optional: the spec omits it when every non-stream output
        # member is optional. Peek the first frame's :event-type -- consume it as the
        # output only when it IS the initial-response; otherwise synthesize the default
        # output and stash the frame so the receiver replays it as the stream's first
        # event rather than dropping it.
        _assert_event_stream()
        source = AsyncBytesReader(response.body)
        event = await _Event.decode_async(source)
        context[_EVENT_STREAM_SOURCE] = source
        if event is not None and event.message.headers.get(":event-type") == (
            "initial-response"
        ):
            deserializer = _EventDeserializer(
                event=event, payload_codec=self.payload_codec, is_client_mode=True
            )
            return operation.output.deserialize(deserializer)
        if event is not None:
            context[_PREFETCHED_EVENT] = event
        return self._default_output(operation)

    def _default_output[
        OperationInput: SerializeableShape,
        OperationOutput: DeserializeableShape,
    ](
        self, operation: APIOperation[OperationInput, OperationOutput]
    ) -> OperationOutput:
        """Build the output when no ``initial-response`` precedes the stream.

        :raises MissingInitialResponse: when the output has required members, so an
            absent initial-response cannot be filled by defaults.
        """
        raise NotImplementedError

    def create_event_receiver[
        OperationInput: SerializeableShape,
        OperationOutput: DeserializeableShape,
        Event: DeserializeableShape,
    ](
        self,
        *,
        operation: "APIOperation[OperationInput, OperationOutput]",
        request: HTTPRequest,
        response: HTTPResponse,
        event_type: "TypeForm[Event]",
        event_deserializer: Callable[[ShapeDeserializer], Event],
        context: TypedProperties,
    ) -> AsyncEventReceiver[Event]:
        _assert_event_stream()
        # Continue from the reader that already consumed the initial-response frame in
        # deserialize_response, so subsequent events stay in order.
        source = context.get(_EVENT_STREAM_SOURCE) or AsyncBytesReader(response.body)
        prefetched = context.get(_PREFETCHED_EVENT)
        if prefetched is not None:
            # No initial-response: replay the first frame ahead of the live stream.
            source = _PrependedEventStream(cast("_Event", prefetched), source)
        return AWSEventReceiver(
            payload_codec=self.payload_codec,
            source=source,
            deserializer=event_deserializer,
        )


class _RpcV2ClientProtocol(_RpcV2ProtocolBase, AsyncRpcClientProtocol):
    """Shared async framing for the Smithy RPC v2 protocol family."""

    async def deserialize_response[
        OperationInput: SerializeableShape,
        OperationOutput: DeserializeableShape,
    ](
        self,
        *,
        operation: APIOperation[OperationInput, OperationOutput],
        request: HTTPRequest,
        response: HTTPResponse,
        error_registry: TypeRegistry,
        context: TypedProperties,
    ) -> OperationOutput:
        if (
            self._is_event_stream_member(operation.output_stream_member)
            and response.status == 200
        ):
            return await self._deserialize_event_stream_response(
                operation=operation, response=response, context=context
            )

        return self._deserialize_body(
            operation=operation,
            response=response,
            body=await response.consume_body_async(),
            error_registry=error_registry,
            context=context,
        )

    def _default_output[
        OperationInput: SerializeableShape,
        OperationOutput: DeserializeableShape,
    ](
        self, operation: APIOperation[OperationInput, OperationOutput]
    ) -> OperationOutput:
        # initial-response is required only if the output cannot be satisfied by an
        # empty document. Clients populate missing members from their defaults, so a
        # required member WITH a default is fine; only a required member with no
        # default genuinely needs the initial-response.
        if self._requires_initial_response(operation.output_schema):
            raise MissingInitialResponse()
        return self._codec.deserialize(
            source=self._empty_document, shape=operation.output
        )


class AsyncRpcV2CborClientProtocol(_RpcV2CborProtocolBase, _RpcV2ClientProtocol):
    """An implementation of the smithy.protocols#rpcv2Cbor protocol."""


class _PrependedEventStream:
    """Serves one already-decoded event's bytes ahead of a live byte stream.

    Lets the receiver read a first event that ``deserialize_response`` pre-fetched
    (an output with no initial-response) as though it were still on the wire, then
    continues from the real source.
    """

    def __init__(self, event: "_Event", source: AsyncByteStream) -> None:
        self._buffer = event.message.encode()
        self._source = source

    async def read(self, size: int = -1) -> bytes:
        if self._buffer:
            if size < 0:
                head, self._buffer = self._buffer, b""
                return head + await self._source.read(size)
            head = self._buffer[:size]
            self._buffer = self._buffer[size:]
            return head
        return await self._source.read(size)

    async def close(self) -> None:
        # Forward close to the wrapped source so the receiver can tear down the
        # underlying response body; without this the connection leaks.
        if (close := getattr(self._source, "close", None)) is not None:
            if asyncio.iscoroutine(result := close()):
                await result
