# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from collections.abc import AsyncIterable, Callable
from inspect import iscoroutinefunction
from string import Formatter
from typing import TYPE_CHECKING, Any, Final
from urllib.parse import quote as urlquote

from smithy_core import URI as _URI
from smithy_core.aio.interfaces import AsyncByteStream, AsyncWriter
from smithy_core.aio.interfaces import StreamingBlob as AsyncStreamingBlob
from smithy_core.aio.interfaces.auth import AuthScheme
from smithy_core.aio.interfaces.eventstream import EventPublisher, EventReceiver
from smithy_core.aio.types import AsyncBytesProvider, AsyncBytesReader
from smithy_core.codecs import Codec
from smithy_core.deserializers import DeserializeableShape, ShapeDeserializer
from smithy_core.documents import TypeRegistry
from smithy_core.exceptions import (
    CallError,
    DiscriminatorError,
    ExpectationNotMetError,
    MissingDependencyError,
    ModeledError,
    UnsupportedStreamError,
)
from smithy_core.interfaces import (
    BytesReader,
    SeekableBytesReader,
    TypedProperties,
    URI,
    is_streaming_blob,
)
from smithy_core.interfaces import StreamingBlob as SyncStreamingBlob
from smithy_core.prelude import DOCUMENT
from smithy_core.schemas import APIOperation, Schema
from smithy_core.serializers import SerializeableShape
from smithy_core.shapes import ShapeID, ShapeType
from smithy_core.traits import EndpointTrait, HTTPTrait
from smithy_core.types import TimestampFormat
from smithy_http import tuples_to_fields
from smithy_http.aio import HTTPRequest as _HTTPRequest
from smithy_http.aio.interfaces import HTTPErrorIdentifier, HTTPRequest, HTTPResponse
from smithy_http.aio.protocols import HttpBindingClientProtocol, HttpClientProtocol
from smithy_json import JSONCodec, JSONDocument

from ..traits import (
    AwsJson1_0Trait,
    AwsJson1_1Trait,
    RestJson1Trait,
)
from ..utils import (
    parse_document_discriminator,
    parse_error_code,
)

try:
    from smithy_aws_event_stream.aio import (
        AWSEventPublisher,
        AWSEventReceiver,
        SigningConfig,
    )

    _HAS_EVENT_STREAM = True
except ImportError:
    _HAS_EVENT_STREAM = False  # type: ignore

if TYPE_CHECKING:
    from smithy_aws_event_stream.aio import (
        AWSEventPublisher,
        AWSEventReceiver,
        SigningConfig,
    )
    from typing_extensions import TypeForm


def _assert_event_stream_capable() -> None:
    if not _HAS_EVENT_STREAM:
        raise MissingDependencyError(
            "Attempted to use event streams, but smithy-aws-event-stream "
            "is not installed."
        )


class AWSErrorIdentifier(HTTPErrorIdentifier):
    _HEADER_KEY: Final = "x-amzn-errortype"

    def identify(
        self,
        *,
        operation: APIOperation[Any, Any],
        response: HTTPResponse,
    ) -> ShapeID | None:
        if self._HEADER_KEY not in response.fields:
            return None

        error_field = response.fields[self._HEADER_KEY]
        code = error_field.values[0] if len(error_field.values) > 0 else None
        if code is not None:
            return parse_error_code(code, operation.schema.id.namespace)
        return None


class AWSJSONDocument(JSONDocument):
    @property
    def discriminator(self) -> ShapeID:
        if self.shape_type is ShapeType.STRUCTURE:
            return self._schema.id
        parsed = parse_document_discriminator(self, self._settings.default_namespace)
        if parsed is None:
            raise DiscriminatorError(
                f"Unable to parse discriminator for {self.shape_type} document."
            )
        return parsed


class _EventStreamClientProtocolMixin:
    @property
    def payload_codec(self) -> Codec:
        raise NotImplementedError

    def _resolve_event_signing_config(
        self,
        *,
        auth_scheme: AuthScheme[Any, Any, Any, Any] | None,
        request: HTTPRequest,
        context: TypedProperties,
    ) -> "SigningConfig | None":
        if auth_scheme is None:
            return None
        event_signer = auth_scheme.event_signer(request=request)
        if event_signer is None:
            return None
        return SigningConfig(
            signer=event_signer,
            signing_properties=auth_scheme.signer_properties(context=context),
            identity_resolver=auth_scheme.identity_resolver(context=context),
            identity_properties=auth_scheme.identity_properties(context=context),
        )

    def _request_async_writer(self, request: HTTPRequest) -> AsyncWriter:
        body = request.body
        if not isinstance(body, AsyncWriter) or not iscoroutinefunction(body.write):
            raise UnsupportedStreamError(
                "Input streams require an async write function, but none was present "
                "on the serialized HTTP request."
            )
        return body

    def create_event_publisher[
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
        _assert_event_stream_capable()
        return AWSEventPublisher[Event](
            payload_codec=self.payload_codec,
            async_writer=self._request_async_writer(request),
            signing_config=self._resolve_event_signing_config(
                auth_scheme=auth_scheme,
                request=request,
                context=context,
            ),
        )

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
        _assert_event_stream_capable()
        return AWSEventReceiver(
            payload_codec=self.payload_codec,
            source=AsyncBytesReader(response.body),
            deserializer=event_deserializer,
        )


class RestJsonClientProtocol(
    _EventStreamClientProtocolMixin, HttpBindingClientProtocol
):
    """An implementation of the aws.protocols#restJson1 protocol."""

    _id: Final = RestJson1Trait.id
    _content_type: Final = "application/json"
    _error_identifier: Final = AWSErrorIdentifier()

    def __init__(self, service_schema: Schema) -> None:
        """Initialize a RestJsonClientProtocol.

        :param service: The schema for the service to interact with.
        """
        self._codec: Final = JSONCodec(
            document_class=AWSJSONDocument,
            default_namespace=service_schema.id.namespace,
            default_timestamp_format=TimestampFormat.EPOCH_SECONDS,
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

    @property
    def error_identifier(self) -> HTTPErrorIdentifier:
        return self._error_identifier


class _AWSJSONClientProtocol(_EventStreamClientProtocolMixin, HttpClientProtocol):
    _error_identifier: Final = AWSErrorIdentifier()
    _http_trait: Final = HTTPTrait({"method": "POST", "uri": "/"})

    _id: ShapeID
    _content_type: str
    _document_class: type[JSONDocument] = AWSJSONDocument

    def __init__(self, service_schema: Schema) -> None:
        self._service_name = service_schema.id.name
        self._codec: Final = JSONCodec(
            document_class=self._document_class,
            default_namespace=service_schema.id.namespace,
            default_timestamp_format=TimestampFormat.EPOCH_SECONDS,
            use_json_name=False,
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

    @property
    def error_identifier(self) -> HTTPErrorIdentifier:
        return self._error_identifier

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
        payload = self.payload_codec.serialize(shape=input)
        input_stream_member = operation.input_stream_member
        has_input_event_stream = (
            isinstance(input_stream_member, Schema)
            and input_stream_member.shape_type is ShapeType.UNION
        )

        field_tuples: list[tuple[str, str]] = [
            ("x-amz-target", f"{self._service_name}.{operation.schema.id.name}"),
        ]
        if has_input_event_stream:
            field_tuples.append(("content-type", "application/vnd.amazon.eventstream"))
            body: AsyncBytesReader | AsyncBytesProvider = AsyncBytesProvider()
        else:
            field_tuples.extend(
                [
                    ("content-type", self.content_type),
                    ("content-length", str(len(payload))),
                ]
            )
            body = AsyncBytesReader(payload)

        fields = tuples_to_fields(field_tuples)
        host = self._resolve_host_prefix(operation=operation, payload=payload)
        return _HTTPRequest(
            destination=_URI(
                host=host,
                path=self._http_trait.path.pattern,
                query=self._http_trait.query,
            ),
            body=body,
            method=self._http_trait.method,
            fields=fields,
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
        if not self._is_success(operation, context, response):
            raise await self._create_error(
                operation=operation,
                request=request,
                response=response,
                response_body=await self._buffer_async_body(response.body),
                error_registry=error_registry,
                context=context,
            )

        if operation.output_stream_member is not None:
            # Stream members are consumed via create_event_receiver().
            return self.payload_codec.deserialize(source=b"{}", shape=operation.output)

        body = response.body
        if not is_streaming_blob(body):
            body = await self._buffer_async_body(body)
        if not is_streaming_blob(body):
            raise UnsupportedStreamError(
                "Unable to read async stream. This stream must be buffered prior "
                "to deserializing."
            )

        source = self._coerce_json_source(response=response, body=body)
        return self.payload_codec.deserialize(source=source, shape=operation.output)

    async def _buffer_async_body(self, stream: AsyncStreamingBlob) -> SyncStreamingBlob:
        match stream:
            case AsyncByteStream():
                if not iscoroutinefunction(stream.read):
                    return stream  # type: ignore
                return await stream.read()
            case AsyncIterable():
                chunks: list[bytes] = []
                async for chunk in stream:
                    chunks.append(chunk)
                return b"".join(chunks)
            case _:
                return stream

    def _is_success(
        self,
        operation: APIOperation[Any, Any],
        context: TypedProperties,
        response: HTTPResponse,
    ) -> bool:
        return 200 <= response.status < 300

    def _resolve_host_prefix(
        self,
        *,
        operation: APIOperation[Any, Any],
        payload: bytes,
    ) -> str:
        endpoint_trait = operation.schema.get_trait(EndpointTrait)
        if endpoint_trait is None:
            return ""

        host_prefix = endpoint_trait.host_prefix
        labels = self._host_prefix_labels(host_prefix)
        if not labels:
            return host_prefix

        deserializer = self.payload_codec.create_deserializer(source=payload)
        document = deserializer.read_document(schema=DOCUMENT)
        if document.shape_type is not ShapeType.MAP:
            raise ExpectationNotMetError(
                f"Expected input document to be a map for host labels, got {document.shape_type}"
            )

        values: dict[str, str] = {}
        map_document = document.as_map()
        for label in labels:
            value = map_document.get(label)
            if value is None or value.shape_type is not ShapeType.STRING:
                raise ExpectationNotMetError(
                    f"Expected host label member '{label}' to be a string in input payload"
                )
            values[label] = urlquote(value.as_string(), safe=".")

        return host_prefix.format(**values)

    def _host_prefix_labels(self, host_prefix: str) -> set[str]:
        labels: set[str] = set()
        for _, field_name, _, _ in Formatter().parse(host_prefix):
            if field_name:
                labels.add(field_name)
        return labels

    def _coerce_json_source(
        self,
        *,
        response: HTTPResponse,
        body: SyncStreamingBlob,
    ) -> bytes | BytesReader:
        if self._is_empty_body(response=response, body=body):
            return b"{}"
        if isinstance(body, bytearray):
            return bytes(body)
        return body

    def _is_empty_body(
        self, *, response: HTTPResponse, body: SyncStreamingBlob
    ) -> bool:
        if "content-length" in response.fields:
            return int(response.fields["content-length"].as_string()) == 0
        if isinstance(body, bytes | bytearray):
            return len(body) == 0
        if (
            seek := getattr(body, "seek", None)
        ) is not None and not iscoroutinefunction(seek):
            position = None
            if (
                tell := getattr(body, "tell", None)
            ) is not None and not iscoroutinefunction(tell):
                position = tell()
            content_length = seek(0, 2)
            if position is not None:
                seek(position, 0)
            else:
                seek(0, 0)
            return content_length == 0
        return False

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

        if error_id is None and self._matches_content_type(response):
            if isinstance(response_body, bytearray):
                response_body = bytes(response_body)
            deserializer = self.payload_codec.create_deserializer(source=response_body)
            document = deserializer.read_document(schema=DOCUMENT)

            if document.discriminator in error_registry:
                error_id = document.discriminator
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

            source = self._coerce_json_source(response=response, body=response_body)
            deserializer = self.payload_codec.create_deserializer(source=source)
            return error_shape.deserialize(deserializer)

        message = (
            f"Unknown error for operation {operation.schema.id} "
            f"- status: {response.status}"
        )
        if error_id is not None:
            message += f" - id: {error_id}"
        if response.reason is not None:
            message += f" - reason: {response.reason}"

        is_timeout = response.status == 408
        is_throttle = response.status == 429
        fault = "client" if response.status < 500 else "server"

        return CallError(
            message=message,
            fault=fault,
            is_throttling_error=is_throttle,
            is_timeout_error=is_timeout,
            is_retry_safe=is_throttle or is_timeout or None,
        )

    def _matches_content_type(self, response: HTTPResponse) -> bool:
        if "content-type" not in response.fields:
            return False
        actual = response.fields["content-type"].as_string()
        return actual.split(";", 1)[0].strip().lower() == self.content_type.lower()


class AwsJson10ClientProtocol(_AWSJSONClientProtocol):
    """An implementation of the aws.protocols#awsJson1_0 protocol."""

    _id: ShapeID = AwsJson1_0Trait.id
    _content_type: str = "application/x-amz-json-1.0"


class AwsJson11ClientProtocol(_AWSJSONClientProtocol):
    """An implementation of the aws.protocols#awsJson1_1 protocol."""

    _id: ShapeID = AwsJson1_1Trait.id
    _content_type: str = "application/x-amz-json-1.1"
