# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Callable
from inspect import iscoroutinefunction
from typing import TYPE_CHECKING, Any, cast

from smithy_core.aio.interfaces import (
    AsyncByteStream,
    AsyncClientProtocol,
    AsyncWriter,
)
from smithy_core.aio.interfaces.auth import AsyncAuthScheme
from smithy_core.aio.interfaces.eventstream import (
    AsyncEventPublisher,
    AsyncEventReceiver,
)
from smithy_core.aio.types import AsyncBytesReader
from smithy_core.aio.utils import close_async
from smithy_core.deserializers import DeserializeableShape, ShapeDeserializer
from smithy_core.exceptions import (
    ExpectationNotMetError,
    MissingDependencyError,
    UnsupportedStreamError,
)
from smithy_core.interfaces import (
    TypedProperties,
)
from smithy_core.program import Program
from smithy_core.schemas import APIOperation
from smithy_core.serializers import SerializeableShape
from smithy_core.types import PropertyKey

from smithy_http.interfaces import HTTPRequest, HTTPResponse

from ..protocols import (
    HttpClientProtocol,
    RpcClientProtocol,
    RpcV2CborClientProtocol,
    RpcV2JsonClientProtocol,
)

__all__ = [
    "AsyncHttpEventStreamMixin",
    "AsyncRpcEventStreamMixin",
    "AsyncRpcV2CborClientProtocol",
    "AsyncRpcV2JsonClientProtocol",
]

try:
    from smithy_aws_event_stream._private.deserializers import (
        EventDeserializer as _EventDeserializer,
    )
    from smithy_aws_event_stream._private.serializers import (
        EventSerializer as _EventSerializer,
    )
    from smithy_aws_event_stream.aio import (
        AsyncAWSEventPublisher,
        AsyncAWSEventReceiver,
        decode_event_async,
    )
    from smithy_aws_event_stream.events import Event as _Event
    from smithy_aws_event_stream.events import EventMessage as _EventMessage
    from smithy_aws_event_stream.signing import SigningConfig
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
        AsyncAWSEventPublisher,
        AsyncAWSEventReceiver,
        decode_event_async,
    )
    from smithy_aws_event_stream.events import Event as _Event
    from smithy_aws_event_stream.events import EventMessage as _EventMessage
    from smithy_aws_event_stream.signing import SigningConfig
    from smithy_core.aio.types import AsyncBytesProvider
    from typing_extensions import TypeForm


_EVENT_STREAM_CONTENT_TYPE = "application/vnd.amazon.eventstream"

_EVENT_STREAM_SOURCE = PropertyKey(
    key="smithy_http_event_stream_source", value_type=AsyncByteStream
)
"""Carries the response-body reader already positioned past the initial-response event.

RPC output streams read their initial response off the first event frame in
``deserialize_response_program``; the receiver then continues from this same reader so the
frames stay in order.
"""

_PREFETCHED_EVENT = PropertyKey(
    key="smithy_http_event_stream_prefetched", value_type=object
)
"""Carries a first stream event already decoded off the body in ``deserialize_response_program``.

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


class AsyncHttpEventStreamMixin(
    HttpClientProtocol, AsyncClientProtocol[HTTPRequest, HTTPResponse]
):
    """Adds event streams to an HTTP protocol for async clients.

    Compose it ahead of a protocol, as in
    ``class AsyncRestJson(AsyncHttpEventStreamMixin, RestJsonClientProtocol)``.
    """

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
        signing_config: SigningConfig[Any, Any, Any, Any] | None = None
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
        publisher = AsyncAWSEventPublisher[Event](
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
        return AsyncAWSEventReceiver(
            payload_codec=self.payload_codec,
            source=AsyncBytesReader(response.body),
            deserializer=event_deserializer,
        )

    def _event_stream_body(self) -> "AsyncBytesProvider":
        _assert_event_stream()
        return AsyncBytesProvider()


class AsyncRpcEventStreamMixin(AsyncHttpEventStreamMixin, RpcClientProtocol):
    """Adds the RPC event stream framing to an RPC protocol for async clients.

    RPC event streams carry the operation input and output as ``initial-request``
    and ``initial-response`` events at the head of the stream.
    """

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
        # deserialization, so subsequent events stay in order.
        source = context.get(_EVENT_STREAM_SOURCE) or AsyncBytesReader(response.body)
        prefetched = context.get(_PREFETCHED_EVENT)
        if prefetched is not None:
            # No initial-response: replay the first frame ahead of the live stream.
            source = _PrependedEventStream(cast("_Event", prefetched), source)
        return AsyncAWSEventReceiver(
            payload_codec=self.payload_codec,
            source=source,
            deserializer=event_deserializer,
        )

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

    def _deserialize_event_stream_response[
        OperationInput: SerializeableShape,
        OperationOutput: DeserializeableShape,
    ](
        self,
        *,
        operation: APIOperation[OperationInput, OperationOutput],
        response: HTTPResponse,
        context: TypedProperties,
    ) -> Program[OperationOutput]:
        # initial-response is optional: the spec omits it when every non-stream output
        # member is optional. Peek the first frame's :event-type -- consume it as the
        # output only when it IS the initial-response; otherwise synthesize the default
        # output and stash the frame so the receiver replays it as the stream's first
        # event rather than dropping it.
        _assert_event_stream()
        source = AsyncBytesReader(response.body)
        event = yield lambda: decode_event_async(source)
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


class AsyncRpcV2CborClientProtocol(AsyncRpcEventStreamMixin, RpcV2CborClientProtocol):
    """An implementation of the smithy.protocols#rpcv2Cbor protocol."""


class AsyncRpcV2JsonClientProtocol(AsyncRpcEventStreamMixin, RpcV2JsonClientProtocol):
    """An implementation of the smithy.protocols#rpcv2Json protocol."""


def _assert_event_stream() -> None:
    if not _HAS_EVENT_STREAM:
        raise MissingDependencyError(
            "Attempted to use event streams, but smithy-aws-event-stream "
            "is not installed."
        )


class _PrependedEventStream:
    """Serves one already-decoded event's bytes ahead of a live byte stream.

    Lets the receiver read a first event that ``deserialize_response_program`` pre-fetched
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
        await close_async(self._source)
