# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import os
from collections.abc import AsyncIterable
from inspect import iscoroutinefunction
from typing import TYPE_CHECKING, Any, cast

from smithy_core import URI as _URI
from smithy_core.aio.interfaces import AsyncByteStream, ClientProtocol
from smithy_core.aio.interfaces import StreamingBlob as AsyncStreamingBlob
from smithy_core.aio.types import AsyncBytesReader
from smithy_core.codecs import Codec
from smithy_core.deserializers import DeserializeableShape
from smithy_core.documents import TypeRegistry
from smithy_core.exceptions import CallError, ExpectationNotMetError, ModeledError
from smithy_core.interfaces import (
    Endpoint,
    SeekableBytesReader,
    TypedProperties,
    URI,
    is_streaming_blob,
)
from smithy_core.interfaces import StreamingBlob as SyncStreamingBlob
from smithy_core.prelude import DOCUMENT
from smithy_core.schemas import APIOperation, Schema
from smithy_core.serializers import SerializeableShape
from smithy_core.shapes import ShapeID
from smithy_core.traits import EndpointTrait, HTTPTrait

from .. import tuples_to_fields
from ..deserializers import HTTPResponseDeserializer
from ..serializers import HTTPRequestSerializer
from . import HTTPRequest as _ConcreteHTTPRequest
from .interfaces import HTTPErrorIdentifier, HTTPRequest, HTTPResponse


class HttpClientProtocol(ClientProtocol[HTTPRequest, HTTPResponse]):
    """An HTTP-based protocol."""

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
        # TODO(optimization): request binding cache like done in SJ
        serializer = HTTPRequestSerializer(
            payload_codec=self.payload_codec,
            http_trait=operation.schema.expect_trait(HTTPTrait),
            endpoint_trait=operation.schema.get_trait(EndpointTrait),
        )

        input.serialize(serializer=serializer)
        request = serializer.result

        if request is None:
            raise ExpectationNotMetError(
                "Expected request to be serialized, but was None"
            )

        return request

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
        if not operation.output_stream_member and not is_streaming_blob(body):
            body = await self._buffer_async_body(response.body)

        # TODO(optimization): response binding cache like done in SJ
        deserializer = HTTPResponseDeserializer(
            payload_codec=self.payload_codec,
            http_trait=operation.schema.expect_trait(HTTPTrait),
            response=response,
            body=body,
        )

        return operation.output.deserialize(deserializer)

    async def _buffer_async_body(self, stream: AsyncStreamingBlob) -> SyncStreamingBlob:
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
                http_trait=operation.schema.expect_trait(HTTPTrait),
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


# smithy-cbor is an optional dependency: only clients using the rpcv2Cbor protocol
# need the codec, so importing it is guarded the same way smithy-aws-core guards its
# JSON/XML codecs.
try:
    from smithy_cbor import CBORCodec
    from smithy_cbor import loads as _cbor_loads
    from smithy_cbor import strip_default_members as _cbor_strip_defaults

    _HAS_CBOR = True
except ImportError:
    _HAS_CBOR = False  # type: ignore

if TYPE_CHECKING:
    from smithy_cbor import CBORCodec
    from smithy_cbor import loads as _cbor_loads
    from smithy_cbor import strip_default_members as _cbor_strip_defaults


# An operation whose input/output was the unit type carries the synthetic
# originalShapeId trait pointing at smithy.api#Unit.
_UNIT_SHAPE_ID = ShapeID("smithy.api#Unit")
_ORIGINAL_SHAPE_ID = ShapeID("smithy.synthetic#originalShapeId")

# The Smithy default trait, used to omit top-level input members left at their default.
_DEFAULT_TRAIT_ID = ShapeID("smithy.api#default")

# CBOR encoding of an empty indefinite-length map (0xBF 0xFF), i.e. `{}`.
_EMPTY_CBOR_MAP = b"\xbf\xff"


def _is_unit(schema: Schema | None) -> bool:
    """rpcv2Cbor treats an operation with unit input as having no body, and unit output
    as an empty response. Codegen synthesizes a wrapper struct for a unit member but
    tags it with ``smithy.synthetic#originalShapeId = smithy.api#Unit``.
    """
    if schema is None:
        return False
    if schema.id == _UNIT_SHAPE_ID:
        return True
    original = schema.traits.get(_ORIGINAL_SHAPE_ID)
    return original is not None and original.document_value == str(_UNIT_SHAPE_ID)


def _top_level_defaults(schema: Schema | None) -> dict[str, Any]:
    """Only the operation input's own members are inspected, so nested members with
    defaults are never included. An empty result (the common case) lets the caller skip
    stripping entirely.
    """
    if schema is None or not schema.members:
        return {}
    defaults: dict[str, Any] = {}
    for name, member in schema.members.items():
        trait = member.traits.get(_DEFAULT_TRAIT_ID)
        if trait is not None:
            defaults[name] = trait.document_value
    return defaults


class RpcV2CborClientProtocol(HttpClientProtocol):
    """rpcv2Cbor is an RPC protocol, NOT an HTTP-binding protocol: HTTP binding traits
    are ignored, every request is a ``POST`` to a fixed URI of the form
    ``/service/{ServiceName}/operation/{OperationName}``, and the body is the CBOR
    encoding of the input shape. It therefore extends :class:`HttpClientProtocol`
    directly rather than :class:`HttpBindingClientProtocol`.

    NOTE: malformed-response detection (Smithy-Protocol header mismatch, HTTP-status-only
    error handling) is not yet implemented.
    """

    _id: ShapeID = ShapeID("smithy.protocols#rpcv2Cbor")
    _content_type: str = "application/cbor"
    _smithy_protocol: str = "rpc-v2-cbor"

    def __init__(self, service_schema: Schema) -> None:
        if not _HAS_CBOR:
            raise ExpectationNotMetError(
                "Attempted to use the rpcv2Cbor protocol, but smithy-cbor is not "
                "installed."
            )
        self._service_name: str = service_schema.id.name
        self._codec: Codec = CBORCodec(  # type: ignore[possibly-unbound]
            default_namespace=service_schema.id.namespace
        )

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

        # rpcv2Cbor omits the body AND the Content-Type header for operations whose
        # input is the unit type (no modeled input). Every other operation serializes
        # the input shape, even when it has no members (an empty indefinite map).
        fields: list[tuple[str, str]] = [
            ("Smithy-Protocol", self._smithy_protocol),
            ("Accept", self._content_type),
        ]
        if _is_unit(operation.input_schema):
            payload = b""
        else:
            payload = self._codec.serialize(shape=input)
            # The client omits top-level input members left at their modeled default.
            defaults = _top_level_defaults(operation.input_schema)
            if defaults:
                payload = _cbor_strip_defaults(payload, defaults)  # type: ignore[possibly-unbound]
            fields.append(("Content-Type", self._content_type))
            fields.append(("Content-Length", str(len(payload))))

        return _ConcreteHTTPRequest(
            method="POST",
            destination=_URI(host="", path=path),
            fields=tuples_to_fields(fields),
            body=AsyncBytesReader(payload),
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
        body = await response.consume_body_async()
        if not (200 <= response.status < 300):
            raise self._create_error(
                operation=operation,
                response=response,
                body=body,
                error_registry=error_registry,
            )
        # An empty body (unit output, or a server that elides the empty map) is a valid
        # response: deserialize it as an empty CBOR map so absent members take their
        # defaults.
        if not body or _is_unit(operation.output_schema):
            body = _EMPTY_CBOR_MAP
        return self._codec.deserialize(source=body, shape=operation.output)

    def _create_error(
        self,
        *,
        operation: APIOperation[Any, Any],
        response: HTTPResponse,
        body: bytes,
        error_registry: TypeRegistry,
    ) -> Exception:
        # rpcv2Cbor discriminates errors by a top-level `__type` member in the CBOR body
        # holding the absolute error shape id (no error header). Resolve it against the
        # registry, then deserialize the same body into the modeled error shape.
        error_id: ShapeID | None = None
        if body:
            decoded: object = _cbor_loads(body)  # type: ignore[possibly-unbound]
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
            deserializer = self._codec.create_deserializer(body or _EMPTY_CBOR_MAP)
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
