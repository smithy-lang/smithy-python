# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import asyncio
import os
from collections.abc import AsyncIterable, Callable
from inspect import iscoroutinefunction
from typing import TYPE_CHECKING, Any, cast

from smithy_core import URI as _URI
from smithy_core.aio.interfaces import (
    AsyncByteStream,
    AsyncWriter,
    ClientProtocol,
    ProtocolSettings,
)
from smithy_core.aio.interfaces import StreamingBlob as AsyncStreamingBlob
from smithy_core.aio.interfaces.auth import AuthScheme
from smithy_core.aio.interfaces.eventstream import EventPublisher, EventReceiver
from smithy_core.aio.types import AsyncBytesReader
from smithy_core.codecs import Codec
from smithy_core.deserializers import DeserializeableShape, ShapeDeserializer
from smithy_core.documents import TypeRegistry
from smithy_core.exceptions import (
    CallError,
    ExpectationNotMetError,
    MissingDependencyError,
    ModeledError,
    UnsupportedStreamError,
)
from smithy_core.interfaces import (
    Endpoint,
    SeekableBytesReader,
    TypedProperties,
    URI,
)
from smithy_core.interfaces import StreamingBlob as SyncStreamingBlob
from smithy_core.prelude import DOCUMENT, UNIT
from smithy_core.response import ResponseMetadata
from smithy_core.schemas import APIOperation, Schema
from smithy_core.serializers import SerializeableShape, SerializeableStruct
from smithy_core.shapes import ShapeID, ShapeType
from smithy_core.traits import (
    ORIGINAL_SHAPE_ID,
    DefaultTrait,
    RequiredTrait,
    RpcV2CborTrait,
)
from smithy_core.types import PropertyKey

from .. import tuples_to_fields
from ..deserializers import HTTPResponseDeserializer
from ..schema_extensions import (
    HTTP_BINDING_SCHEMA_EXTENSION,
    HTTP_OPERATION_SCHEMA_EXTENSION,
)
from ..serializers import HTTPBindingSerializer, HTTPRequestSerializer
from . import HTTPRequest as _HTTPRequest
from .interfaces import HTTPErrorIdentifier, HTTPRequest, HTTPResponse

__all__ = [
    "HttpBindingClientProtocol",
    "HttpClientProtocol",
    "RpcClientProtocol",
    "RpcV2CborClientProtocol",
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


class HttpClientProtocol(ClientProtocol[HTTPRequest, HTTPResponse]):
    """An HTTP-based protocol."""

    @property
    def payload_codec(self) -> Codec:
        """The codec used for the serde of event payloads and HTTP bodies."""
        raise NotImplementedError()

    def set_service_endpoint(
        self,
        *,
        request: HTTPRequest,
        endpoint: Endpoint,
    ) -> HTTPRequest:
        uri = endpoint.uri
        previous = request.destination

        path = previous.path or uri.path
        if uri.path is not None and previous.path is not None:
            path = os.path.join(uri.path, previous.path.lstrip("/"))

        if path is not None and not path.startswith("/"):
            path = "/" + path

        query = previous.query or uri.query
        if uri.query and previous.query:
            query = f"{uri.query}&{previous.query}"

        request.destination = _URI(
            scheme=uri.scheme,
            username=uri.username or previous.username,
            password=uri.password or previous.password,
            host=uri.host,
            port=uri.port or previous.port,
            path=path,
            query=query,
            fragment=uri.fragment or previous.fragment,
        )

        return request

    def extract_response_metadata(
        self,
        *,
        response: HTTPResponse,
        context: TypedProperties,
    ) -> ResponseMetadata:
        """Extract the status code from an HTTP response.

        Identifiers such as request IDs are not part of HTTP itself, so protocols
        that define them are expected to override this and add them.
        """
        return ResponseMetadata(http_status_code=response.status)

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
        auth_scheme: AuthScheme[Any, Any, Any, Any] | None = None,
    ) -> EventPublisher[Event]:
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
    ) -> EventReceiver[Event]:
        _assert_event_stream()
        return AWSEventReceiver(
            payload_codec=self.payload_codec,
            source=AsyncBytesReader(response.body),
            deserializer=event_deserializer,
        )


class HttpBindingClientProtocol(HttpClientProtocol):
    """An HTTP-based protocol that uses HTTP binding traits."""

    @property
    def payload_codec(self) -> Codec:
        """The codec used for the serde of input and output payloads."""
        raise NotImplementedError()

    @property
    def content_type(self) -> str:
        """The media type of the http payload."""
        raise NotImplementedError()

    @property
    def error_identifier(self) -> HTTPErrorIdentifier:
        """The class used to identify the shape IDs of errors based on fields or other
        response information."""
        raise NotImplementedError()

    def serialize_request[
        OperationInput: "SerializeableShape",
        OperationOutput: "DeserializeableShape",
    ](
        self,
        *,
        operation: APIOperation[OperationInput, OperationOutput],
        input: OperationInput,
        endpoint: URI,
        context: TypedProperties,
    ) -> HTTPRequest:
        operation_metadata = operation.schema.get_extension(
            HTTP_OPERATION_SCHEMA_EXTENSION
        )
        if isinstance(input, SerializeableStruct):
            serializer = HTTPBindingSerializer(
                payload_codec=self.payload_codec,
                schema=operation.input_schema,
                http_trait=operation_metadata.http_trait,
                operation_metadata=operation_metadata,
            )
            try:
                input.serialize_members(serializer)
            except BaseException as error:
                serializer.abort(type(error), error, error.__traceback__)
                raise
            return serializer.build_request()

        serializer = HTTPRequestSerializer(
            payload_codec=self.payload_codec,
            http_trait=operation_metadata.http_trait,
            operation_metadata=operation_metadata,
        )
        input.serialize(serializer)
        if serializer.result is None:
            raise ExpectationNotMetError(
                "Expected request to be serialized, but was None"
            )
        return serializer.result

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
            raise await self._create_error(
                operation=operation,
                request=request,
                response=response,
                response_body=await self._buffer_async_body(response.body),
                error_registry=error_registry,
                context=context,
            )

        # if body is not streaming and is async, we have to buffer it
        body: SyncStreamingBlob | None = None
        response_metadata = operation.output_schema.get_extension(
            HTTP_BINDING_SCHEMA_EXTENSION
        ).response
        if response_metadata.streaming_member is None:
            body = await self._buffer_async_body(response.body)

        deserializer = HTTPResponseDeserializer(
            payload_codec=self.payload_codec,
            response=response,
            body=body,
        )

        return operation.output.deserialize(deserializer)

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

    def _is_success(
        self,
        operation: APIOperation[Any, Any],
        context: TypedProperties,
        response: HTTPResponse,
    ) -> bool:
        return 200 <= response.status < 300

    async def _create_error(
        self,
        operation: APIOperation[Any, Any],
        request: HTTPRequest,
        response: HTTPResponse,
        response_body: SyncStreamingBlob,
        error_registry: TypeRegistry,
        context: TypedProperties,
    ) -> CallError:
        error_id = self.error_identifier.identify(
            operation=operation, response=response
        )
        if error_id is not None and error_id not in error_registry:
            error_id = self._resolve_error_id(
                operation=operation,
                error_id=error_id,
            )

        retry_after = self._retry_after(response)

        if error_id is None and self._matches_content_type(response):
            if isinstance(response_body, bytearray):
                response_body = bytes(response_body)
            deserializer = self.payload_codec.create_deserializer(source=response_body)
            document = deserializer.read_document(schema=DOCUMENT)
            document_error_id = document.discriminator
            if document_error_id not in error_registry:
                document_error_id = self._resolve_error_id(
                    operation=operation,
                    error_id=document_error_id,
                )

            if document_error_id in error_registry:
                error_id = document_error_id
                if isinstance(response_body, SeekableBytesReader):
                    response_body.seek(0)

        if error_id is not None and error_id in error_registry:
            error_shape = error_registry.get(error_id)

            # make sure the error shape is derived from modeled exception
            if not issubclass(error_shape, ModeledError):
                raise ExpectationNotMetError(
                    f"Modeled errors must be derived from 'ModeledError', "
                    f"but got {error_shape}"
                )

            deserializer = HTTPResponseDeserializer(
                payload_codec=self.payload_codec,
                response=response,
                body=response_body,
            )
            modeled_error = error_shape.deserialize(deserializer)
            if retry_after is not None:
                modeled_error.retry_after = retry_after
            return modeled_error

        message = (
            f"Unknown error for operation {operation.schema.id} "
            f"- status: {response.status}"
        )
        if error_id is not None:
            message += f" - id: {error_id}"
        if response.reason is not None:
            message += f" - reason: {response.status}"

        is_timeout = response.status == 408
        is_throttle = response.status == 429
        fault = "client" if response.status < 500 else "server"

        return CallError(
            message=message,
            fault=fault,
            is_throttling_error=is_throttle,
            is_timeout_error=is_timeout,
            is_retry_safe=is_throttle or is_timeout or None,
            retry_after=retry_after,
        )

    def _retry_after(self, response: HTTPResponse) -> float | None:
        """The retry delay in seconds requested by the server, if the response carries one."""
        return None

    def _resolve_error_id(
        self,
        *,
        operation: APIOperation[Any, Any],
        error_id: ShapeID,
    ) -> ShapeID:
        """Resolve a response discriminator to its modeled error shape ID."""
        return error_id

    def _matches_content_type(self, response: HTTPResponse) -> bool:
        if "content-type" not in response.fields:
            return False
        return response.fields["content-type"].as_string() == self.content_type


try:
    from smithy_cbor import CBORCodec
    from smithy_cbor import loads as _cbor_loads

    _HAS_CBOR = True
except ImportError:
    _HAS_CBOR = False  # type: ignore

if TYPE_CHECKING:
    from smithy_cbor import CBORCodec
    from smithy_cbor import loads as _cbor_loads


def _assert_cbor() -> None:
    if not _HAS_CBOR:
        raise MissingDependencyError(
            "Attempted to use CBOR codec, but smithy-cbor is not installed."
        )


def _is_unit(schema: Schema | None) -> bool:
    """rpcv2Cbor treats an operation with unit input as having no body, and unit output
    as an empty response. Codegen synthesizes a wrapper struct for a unit member but
    tags it with ``smithy.synthetic#originalShapeId = smithy.api#Unit``.
    """
    if schema is None:
        return False
    if schema.id == UNIT.id:
        return True
    original = schema.traits.get(ORIGINAL_SHAPE_ID)
    return original is not None and original.document_value == str(UNIT.id)


def _is_event_stream_member(member: Schema | None) -> bool:
    """Whether a ``@streaming`` member is an EVENT stream (union), not a data stream.

    ``input_stream_member``/``output_stream_member`` match any ``@streaming`` member;
    a blob target is a data stream, only a union target is an event stream.
    """
    return member is not None and member.expect_member_target().shape_type is (
        ShapeType.UNION
    )


class RpcClientProtocol(HttpClientProtocol):
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

    # The protocol trait's eventStreamHttp ALPN list (empty if the trait left it unset).
    _event_stream_http: tuple[str, ...] = ()

    def _requires_http2(self, operation: APIOperation[Any, Any]) -> bool:
        # Only EVENT streams (a @streaming UNION member) force HTTP/2 -- a @streaming
        # blob is a data stream and runs fine over HTTP/1.1. input_stream_member /
        # output_stream_member match either, so check the target is a union here.
        if not (
            _is_event_stream_member(operation.input_stream_member)
            or _is_event_stream_member(operation.output_stream_member)
        ):
            return False
        # Require HTTP/2 unless the model EXPLICITLY allows only HTTP/1.1: no list, or
        # any list containing h2, requires h2; only an h1-and-nothing-else list opts out.
        return "h2" in self._event_stream_http or not self._event_stream_http

    @staticmethod
    def _requires_initial_response(output: Schema) -> bool:
        """Whether the output needs an ``initial-response`` to be populated.

        An empty document satisfies any member that is optional or has a default
        (clients fill defaults), so only a ``@required`` member without a ``@default``
        forces an initial-response.
        """
        for member in output.members.values():
            if member.get_trait(RequiredTrait) is not None and (
                member.get_trait(DefaultTrait) is None
            ):
                return True
        return False

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
    ) -> EventReceiver[Event]:
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


class _RpcV2ClientProtocol(RpcClientProtocol):
    """Shared framing for the Smithy RPC v2 protocol family (rpcv2Cbor, rpcv2Json).

    Subclasses supply the codec-specific pieces: the protocol id, content type,
    ``Smithy-Protocol`` header value, the empty-document sentinel, codec construction,
    and error ``__type`` decoding. All HTTP/RPC framing lives here.
    """

    _id: ShapeID
    _content_type: str
    _smithy_protocol: str
    # Serialized empty document (e.g. CBOR `{}` or JSON `{}`) used when a response body
    # is absent so absent members take their defaults.
    _empty_document: bytes
    _codec: Codec
    _service_name: str

    @property
    def id(self) -> ShapeID:
        return self._id

    @property
    def payload_codec(self) -> Codec:
        return self._codec

    @property
    def content_type(self) -> str:
        return self._content_type

    def _decode_document(self, body: bytes) -> object:
        """Decode a serialized document to a Python object, for reading the error
        ``__type`` discriminator.
        """
        raise NotImplementedError

    def serialize_request[
        OperationInput: SerializeableShape,
        OperationOutput: DeserializeableShape,
    ](
        self,
        *,
        operation: APIOperation[OperationInput, OperationOutput],
        input: OperationInput,
        endpoint: URI,
        context: TypedProperties,
    ) -> HTTPRequest:
        operation_name = operation.schema.id.name
        path = f"/service/{self._service_name}/operation/{operation_name}"

        # An event-stream operation must negotiate HTTP/2 (see _requires_http2); mark
        # the request so the transport does so for this operation alone, leaving
        # non-streaming operations on HTTP/1.1.
        http2_required = self._requires_http2(operation)

        # Accept describes the RESPONSE and Content-Type the REQUEST body, so they turn
        # on output_stream_member and input_stream_member independently: a one-way
        # stream advertises the event-stream media type on only the streaming side.
        accept = (
            _EVENT_STREAM_CONTENT_TYPE
            if operation.output_stream_member is not None
            else self._content_type
        )
        fields: list[tuple[str, str]] = [
            ("Smithy-Protocol", self._smithy_protocol),
            ("Accept", accept),
        ]

        if operation.input_stream_member is not None:
            # RPC event streams carry the input as an initial-request event at the head
            # of the stream body; the HTTP envelope is otherwise a normal RPC request.
            fields.append(("Content-Type", _EVENT_STREAM_CONTENT_TYPE))
            return _HTTPRequest(
                method="POST",
                destination=_URI(host="", path=path),
                fields=tuples_to_fields(fields),
                body=self._build_initial_request_body(input, context),
                http2_required=http2_required,
            )

        # The protocol omits the body AND the Content-Type header for operations whose
        # input is the unit type (no modeled input). Every other operation serializes
        # the input shape, even when it has no members.
        if _is_unit(operation.input_schema):
            payload = b""
        else:
            payload = self._codec.serialize(shape=input)
            fields.append(("Content-Type", self._content_type))
            fields.append(("Content-Length", str(len(payload))))

        return _HTTPRequest(
            method="POST",
            destination=_URI(host="", path=path),
            fields=tuples_to_fields(fields),
            body=AsyncBytesReader(payload),
            http2_required=http2_required,
        )

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
        if operation.output_stream_member is not None and response.status == 200:
            return await self._deserialize_event_stream_response(
                operation=operation, response=response, context=context
            )

        body = await response.consume_body_async()
        if response.status != 200:
            raise self._create_error(
                operation=operation,
                response=response,
                body=body,
                error_registry=error_registry,
                context=context,
            )
        # An empty body (unit output, or a server that elides the empty document) is a
        # valid response: deserialize an empty document so absent members take defaults.
        if not body or _is_unit(operation.output_schema):
            body = self._empty_document
        return self._codec.deserialize(source=body, shape=operation.output)

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

    def _create_error(
        self,
        *,
        operation: APIOperation[Any, Any],
        response: HTTPResponse,
        body: bytes,
        error_registry: TypeRegistry,
        context: TypedProperties,
    ) -> Exception:
        # The protocol discriminates errors by a top-level `__type` member in the body
        # holding the absolute error shape id (no error header). Resolve it against the
        # registry, then deserialize the same body into the modeled error shape.
        error_id: ShapeID | None = None
        if body:
            decoded = self._decode_document(body)
            if isinstance(decoded, dict):
                raw_type = cast("dict[str, object]", decoded).get("__type")
                if isinstance(raw_type, str):
                    error_id = self._normalize_error_id(raw_type, operation)

        if error_id is not None and error_id in error_registry:
            error_shape = error_registry.get(error_id)
            if not issubclass(error_shape, ModeledError):
                raise ExpectationNotMetError(
                    f"Modeled errors must derive from 'ModeledError', got {error_shape}"
                )
            deserializer = self._codec.create_deserializer(body or self._empty_document)
            return error_shape.deserialize(deserializer)

        message = (
            f"Unknown error for operation {operation.schema.id} "
            f"- status: {response.status}"
        )
        if error_id is not None:
            message += f" - id: {error_id}"
        return CallError(
            message=message,
            fault="client" if response.status < 500 else "server",
        )

    @staticmethod
    def _normalize_error_id(
        raw_type: str, operation: APIOperation[Any, Any]
    ) -> ShapeID:
        # `__type` may carry a full shape id, or (per spec) a name that may include a
        # trailing "#"-qualified suffix. Match on the shape name against the operation's
        # modeled errors so a bare or oddly-qualified name still resolves.
        candidate = ShapeID(raw_type)
        for error_schema in operation.error_schemas:
            if error_schema.id == candidate or error_schema.id.name == candidate.name:
                return error_schema.id
        return candidate


class RpcV2CborClientProtocol(_RpcV2ClientProtocol):
    """An implementation of the smithy.protocols#rpcv2Cbor protocol."""

    _id: ShapeID = RpcV2CborTrait.id
    _content_type: str = "application/cbor"
    _smithy_protocol: str = "rpc-v2-cbor"
    # CBOR encoding of an empty indefinite-length map (0xBF 0xFF), i.e. `{}`.
    _empty_document: bytes = b"\xbf\xff"

    def __init__(self, settings: ProtocolSettings) -> None:
        _assert_cbor()
        self._service_name = settings.service_target
        self._event_stream_http = tuple(settings.event_stream_http)
        self._codec = CBORCodec(default_namespace=settings.namespace)

    def _decode_document(self, body: bytes) -> object:
        return _cbor_loads(body)  # type: ignore[possibly-unbound]


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
