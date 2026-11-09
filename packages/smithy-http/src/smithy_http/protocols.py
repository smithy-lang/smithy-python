# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import json
import os
from collections.abc import Callable, Mapping, Sequence
from io import BytesIO
from typing import TYPE_CHECKING, Any, cast

from smithy_core import URI as _URI
from smithy_core.codecs import Codec
from smithy_core.deserializers import DeserializeableShape
from smithy_core.documents import TypeRegistry
from smithy_core.exceptions import (
    CallError,
    ExpectationNotMetError,
    MissingDependencyError,
    ModeledError,
    UnsupportedStreamError,
)
from smithy_core.exceptions import (
    SmithyError as _SmithyError,
)
from smithy_core.interfaces import (
    AnyStreamingBlob,
    ClientProtocol,
    Endpoint,
    ProtocolSettings,
    SeekableBytesReader,
    TypedProperties,
    URI,
)
from smithy_core.interfaces import StreamingBlob as SyncStreamingBlob
from smithy_core.prelude import DOCUMENT, UNIT
from smithy_core.program import Program
from smithy_core.response import ResponseMetadata
from smithy_core.schemas import APIOperation, Schema
from smithy_core.serializers import SerializeableShape, SerializeableStruct
from smithy_core.shapes import ShapeID, ShapeType
from smithy_core.traits import (
    ORIGINAL_SHAPE_ID,
    DefaultTrait,
    RequiredTrait,
    RpcV2CborTrait,
    RpcV2JsonTrait,
)
from smithy_core.types import TimestampFormat as _TimestampFormat

from smithy_http import HTTPRequest as _HTTPRequest
from smithy_http.interfaces import HTTPErrorIdentifier, HTTPRequest, HTTPResponse

from . import tuples_to_fields
from .deserializers import HTTPResponseDeserializer
from .schema_extensions import (
    HTTP_BINDING_SCHEMA_EXTENSION,
    HTTP_OPERATION_SCHEMA_EXTENSION,
)
from .serializers import HTTPBindingSerializer, HTTPRequestSerializer

if TYPE_CHECKING:
    from smithy_core._schema_compact import StaticSchema

__all__ = [
    "HttpBindingClientProtocol",
    "HttpClientProtocol",
    "RpcClientProtocol",
    "RpcV2CborClientProtocol",
    "RpcV2JsonClientProtocol",
]

_EVENT_STREAM_CONTENT_TYPE = "application/vnd.amazon.eventstream"

try:
    from smithy_cbor import CBORCodec
    from smithy_cbor import loads as _cbor_loads

    _HAS_CBOR = True
except ImportError:
    _HAS_CBOR = False  # type: ignore

if TYPE_CHECKING:
    from smithy_cbor import CBORCodec
    from smithy_cbor import loads as _cbor_loads

try:
    from smithy_json import JSONCodec as _JSONCodec

    _HAS_JSON = True
except ImportError:
    _HAS_JSON = False  # type: ignore

if TYPE_CHECKING:
    from smithy_json import JSONCodec as _JSONCodec


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
                event_stream_body=self._event_stream_body,
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

    def deserialize_response_program[
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
        read_body: Callable[[AnyStreamingBlob], Any],
    ) -> Program[OperationOutput]:
        if not self._is_success(operation, context, response):
            body = yield lambda: read_body(response.body)
            raise self._create_error(
                operation=operation,
                request=request,
                response=response,
                response_body=body,
                error_registry=error_registry,
                context=context,
            )
        if self._has_streaming_output(operation):
            return self._deserialize_output(operation, response, None)
        body = yield lambda: read_body(response.body)
        return self._deserialize_output(operation, response, body)

    def _event_stream_body(self) -> Any:
        """Create the request body that input event stream events are written to."""
        raise UnsupportedStreamError(
            "Event streams are not supported by synchronous clients."
        )

    def _has_streaming_output(self, operation: APIOperation[Any, Any]) -> bool:
        response_metadata = operation.output_schema.get_extension(
            HTTP_BINDING_SCHEMA_EXTENSION
        ).response
        return response_metadata.streaming_member is not None

    def _deserialize_output[
        OperationInput: "SerializeableShape",
        OperationOutput: "DeserializeableShape",
    ](
        self,
        operation: APIOperation[OperationInput, OperationOutput],
        response: HTTPResponse,
        body: SyncStreamingBlob | None,
    ) -> OperationOutput:
        deserializer = HTTPResponseDeserializer(
            payload_codec=self.payload_codec,
            response=response,
            body=body,
        )
        return operation.output.deserialize(deserializer)

    def _is_success(
        self,
        operation: APIOperation[Any, Any],
        context: TypedProperties,
        response: HTTPResponse,
    ) -> bool:
        return 200 <= response.status < 300

    def _create_error(
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


class RpcClientProtocol(HttpClientProtocol):
    """Base for the RPC-based protocols (awsJson, awsQuery, rpcv2).

    RPC protocols serialize the whole operation input through a codec rather than via
    HTTP bindings. Per the Amazon event stream specification, an RPC event stream
    carries the operation input and output as ``initial-request`` and
    ``initial-response`` events at the head of the stream rather than as the HTTP
    request and response bodies.
    """

    # The protocol trait's eventStreamHttp ALPN list (empty if the trait left it unset).
    _event_stream_http: tuple[str, ...] = ()
    # The serialized empty document, deserialized when a response omits the output.
    _empty_document: bytes = b"{}"

    def deserialize_response_program[
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
        read_body: Callable[[AnyStreamingBlob], Any],
    ) -> Program[OperationOutput]:
        if (
            self._is_event_stream_member(operation.output_stream_member)
            and response.status == 200
        ):
            return (
                yield from self._deserialize_event_stream_response(
                    operation=operation, response=response, context=context
                )
            )
        body = yield lambda: read_body(response.body)
        return self._deserialize_body(
            operation=operation,
            response=response,
            body=body,
            error_registry=error_registry,
            context=context,
        )

    def _deserialize_body[
        OperationInput: SerializeableShape,
        OperationOutput: DeserializeableShape,
    ](
        self,
        *,
        operation: APIOperation[OperationInput, OperationOutput],
        response: HTTPResponse,
        body: bytes,
        error_registry: TypeRegistry,
        context: TypedProperties,
    ) -> OperationOutput:
        raise NotImplementedError

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
        raise UnsupportedStreamError(
            "Event streams are not supported by synchronous clients."
        )
        yield  # pyright: ignore[reportUnreachable]

    def _default_output[
        OperationInput: SerializeableShape,
        OperationOutput: DeserializeableShape,
    ](
        self, operation: APIOperation[OperationInput, OperationOutput]
    ) -> OperationOutput:
        """Build the output when no ``initial-response`` precedes the event stream.

        :raises MissingInitialResponse: when the output has a required member without
            a default, which an absent initial-response cannot fill.
        """
        if self._requires_initial_response(operation.output_schema):
            from smithy_aws_event_stream.exceptions import MissingInitialResponse

            raise MissingInitialResponse()
        return self.payload_codec.deserialize(
            source=self._empty_document, shape=operation.output
        )

    def _build_initial_request_body(
        self, input: SerializeableShape, context: TypedProperties
    ) -> Any:
        """Build the body of an RPC event stream request."""
        raise UnsupportedStreamError(
            "Event streams are not supported by synchronous clients."
        )

    @staticmethod
    def _resolve_event_stream_http(
        service_schema: "StaticSchema | Schema", protocol_id: ShapeID
    ) -> tuple[str, ...]:
        """Read this protocol's ``eventStreamHttp`` ALPN list off the service schema.

        Keyed by the protocol's own id, so a service carrying several protocol traits
        yields each protocol its own value rather than a flattened one. The compact
        schema codegen emits is hydrated on first read (cached thereafter).
        """
        from smithy_core._schema_compact import hydrate

        trait = hydrate(service_schema).get_trait(protocol_id)
        if trait is None:
            return ()
        value = trait.document_value
        if not isinstance(value, Mapping):
            return ()
        versions = value.get("eventStreamHttp")
        if not isinstance(versions, Sequence) or isinstance(versions, str | bytes):
            return ()
        return tuple(str(v) for v in versions)

    @staticmethod
    def _is_event_stream_member(member: Schema | None) -> bool:
        """Whether a ``@streaming`` member is an EVENT stream (union), not a data stream.

        ``input_stream_member``/``output_stream_member`` match any ``@streaming``
        member; a blob target is a data stream, only a union target is an event stream.
        """
        return member is not None and member.expect_member_target().shape_type is (
            ShapeType.UNION
        )

    def _requires_http2(self, operation: APIOperation[Any, Any]) -> bool:
        # Only EVENT streams (a @streaming UNION member) force HTTP/2 -- a @streaming
        # blob is a data stream and runs fine over HTTP/1.1. input_stream_member /
        # output_stream_member match either, so check the target is a union here.
        if not (
            self._is_event_stream_member(operation.input_stream_member)
            or self._is_event_stream_member(operation.output_stream_member)
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


class _RpcV2ProtocolBase(RpcClientProtocol):
    """Shared framing for the Smithy RPC v2 protocol family (rpcv2Cbor, rpcv2Json).

    Subclasses supply the codec-specific pieces: the protocol id, content type,
    ``Smithy-Protocol`` header value, the empty-document sentinel, codec construction,
    and error ``__type`` decoding. All HTTP/RPC framing lives here, including the
    check that a response echoes the request's ``Smithy-Protocol`` header. It runs in
    ``deserialize_response_program``, so sync and async clients (and the async
    event-stream response path) share it.
    """

    _id: ShapeID
    _content_type: str
    _smithy_protocol: str
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
        # Only an EVENT stream (union member) counts; a @streaming blob is a data stream
        # and takes the normal media type.
        accept = (
            _EVENT_STREAM_CONTENT_TYPE
            if self._is_event_stream_member(operation.output_stream_member)
            else self._content_type
        )
        fields: list[tuple[str, str]] = [
            ("Smithy-Protocol", self._smithy_protocol),
            ("Accept", accept),
        ]

        if self._is_event_stream_member(operation.input_stream_member):
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
            body=BytesIO(payload),
            http2_required=http2_required,
        )

    def deserialize_response_program[
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
        read_body: Callable[[AnyStreamingBlob], Any],
    ) -> Program[OperationOutput]:
        # A response whose Smithy-Protocol header differs from the request's is
        # malformed: the spec requires handling it on the status code alone, without
        # interpreting the body or other headers. Checked first, for every status
        # (including 200) and before the event-stream branch.
        actual_protocol = (
            response.fields["Smithy-Protocol"].as_string()
            if "Smithy-Protocol" in response.fields
            else None
        )
        if actual_protocol != self._smithy_protocol:
            yield from self._discard_body(operation, response, read_body)
            raise CallError(
                message=(
                    f"Malformed response for operation {operation.schema.id}: "
                    f"expected Smithy-Protocol header {self._smithy_protocol!r}, "
                    f"got {actual_protocol!r} - status: {response.status}"
                ),
                fault="client" if response.status < 500 else "server",
            )
        return (
            yield from super().deserialize_response_program(
                operation=operation,
                request=request,
                response=response,
                error_registry=error_registry,
                context=context,
                read_body=read_body,
            )
        )

    def _discard_body(
        self,
        operation: APIOperation[Any, Any],
        response: HTTPResponse,
        read_body: Callable[[AnyStreamingBlob], Any],
    ) -> Program[None]:
        """Release a response body that will not be interpreted.

        A bounded body is drained, as the error path does, so the connection can be
        reused. A response to an event-stream operation may be long-lived, so it is
        closed instead of drained to avoid blocking on it.
        """
        if self._is_event_stream_member(operation.output_stream_member):
            yield lambda: _close(response.body)
            return
        yield lambda: read_body(response.body)

    def _decode_document(self, body: bytes) -> object:
        """Decode a serialized document to a Python object, for reading the error
        ``__type`` discriminator.
        """
        raise NotImplementedError

    def _deserialize_body[
        OperationInput: SerializeableShape,
        OperationOutput: DeserializeableShape,
    ](
        self,
        *,
        operation: APIOperation[OperationInput, OperationOutput],
        response: HTTPResponse,
        body: bytes,
        error_registry: TypeRegistry,
        context: TypedProperties,
    ) -> OperationOutput:
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
        raw_type: object = None
        if body:
            # A body that cannot be decoded is a malformed error response, which the
            # spec requires handling on the status code alone.
            try:
                decoded = self._decode_document(body)
            except Exception:
                decoded = None
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
        elif isinstance(raw_type, str):
            message += f" - id: {raw_type}"
        return CallError(
            message=message,
            fault="client" if response.status < 500 else "server",
        )

    @staticmethod
    def _normalize_error_id(
        raw_type: str, operation: APIOperation[Any, Any]
    ) -> ShapeID | None:
        # The spec requires `__type` to be the absolute shape id. Tolerate looser forms
        # servers emit in practice -- a bare name, a different namespace, or an
        # awsJson-style ":"-delimited suffix -- by matching on the shape name against
        # the operation's modeled errors. Returns None if nothing usable remains.
        name = raw_type.split(":", 1)[0]
        short_name = name.rpartition("#")[2]
        for error_schema in operation.error_schemas:
            if str(error_schema.id) == name or error_schema.id.name == short_name:
                return error_schema.id
        try:
            return ShapeID(name)
        except _SmithyError:
            return None


class RpcV2CborClientProtocol(_RpcV2ProtocolBase):
    """An implementation of the smithy.protocols#rpcv2Cbor protocol."""

    _id: ShapeID = RpcV2CborTrait.id
    _content_type: str = "application/cbor"
    _smithy_protocol: str = "rpc-v2-cbor"
    # CBOR encoding of an empty indefinite-length map (0xBF 0xFF), i.e. `{}`.
    _empty_document: bytes = b"\xbf\xff"

    def __init__(self, settings: ProtocolSettings) -> None:
        _assert_cbor()
        self._service_name = settings.service_target
        self._event_stream_http = self._resolve_event_stream_http(
            settings.service_schema, self._id
        )
        self._codec = CBORCodec(default_namespace=settings.namespace)

    def _decode_document(self, body: bytes) -> object:
        return _cbor_loads(body)  # type: ignore[possibly-unbound]


class RpcV2JsonClientProtocol(_RpcV2ProtocolBase):
    """An implementation of the smithy.protocols#rpcv2Json protocol."""

    _id: ShapeID = RpcV2JsonTrait.id
    _content_type: str = "application/json"
    _smithy_protocol: str = "rpc-v2-json"
    _empty_document: bytes = b"{}"

    def __init__(self, settings: ProtocolSettings) -> None:
        _assert_json()
        self._service_name = settings.service_target
        self._event_stream_http = self._resolve_event_stream_http(
            settings.service_schema, self._id
        )
        # The protocol ignores @jsonName and @timestampFormat: members serialize under
        # their member names and timestamps as epoch-seconds. bigInteger/bigDecimal
        # travel as JSON strings to preserve arbitrary precision.
        self._codec = _JSONCodec(
            use_json_name=False,
            use_timestamp_format=False,
            default_timestamp_format=_TimestampFormat.EPOCH_SECONDS,
            arbitrary_precision_as_string=True,
            default_namespace=settings.namespace,
        )

    def _decode_document(self, body: bytes) -> object:
        return json.loads(body)


def _assert_cbor() -> None:
    if not _HAS_CBOR:
        raise MissingDependencyError(
            "Attempted to use CBOR codec, but smithy-cbor is not installed."
        )


def _assert_json() -> None:
    if not _HAS_JSON:
        raise MissingDependencyError(
            "Attempted to use JSON codec, but smithy-json is not installed."
        )


def _close(stream: Any) -> Any:
    """Effect: close a stream, returning the awaitable if its ``close`` is async.

    Mode-neutral: the async program runner awaits the result, the sync one calls it.
    """
    if (close := getattr(stream, "close", None)) is not None:
        return close()
    return None


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
