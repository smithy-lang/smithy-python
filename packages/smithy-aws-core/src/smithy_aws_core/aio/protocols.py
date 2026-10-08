# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Callable
from dataclasses import dataclass, replace
from inspect import iscoroutinefunction
from io import BytesIO
from typing import TYPE_CHECKING, Any, ClassVar, Final

from smithy_core import URI as _URI
from smithy_core.aio.interfaces import (
    AsyncWriter,
    ProtocolSettings,
)
from smithy_core.aio.interfaces.auth import AuthScheme
from smithy_core.aio.interfaces.eventstream import EventPublisher, EventReceiver
from smithy_core.aio.types import AsyncBytesReader
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
from smithy_core.interfaces import BytesReader, BytesWriter, TypedProperties, URI
from smithy_core.interfaces import StreamingBlob as SyncStreamingBlob
from smithy_core.prelude import DOCUMENT
from smithy_core.response import ResponseMetadata
from smithy_core.schemas import APIOperation
from smithy_core.serializers import SerializeableShape, ShapeSerializer
from smithy_core.shapes import ShapeID, ShapeType
from smithy_core.traits import HTTPTrait
from smithy_core.types import PropertyKey, TimestampFormat
from smithy_http import tuples_to_fields
from smithy_http.aio import HTTPRequest as _HTTPRequest
from smithy_http.aio.interfaces import HTTPErrorIdentifier, HTTPRequest, HTTPResponse
from smithy_http.aio.protocols import (
    HttpBindingClientProtocol,
    HttpClientProtocol,
)
from smithy_http.deserializers import HTTPResponseDeserializer

from .._private.query.errors import create_aws_query_error
from .._private.query.metadata import parse_aws_query_request_id
from .._private.query.serializers import Ec2QueryShapeSerializer, QueryShapeSerializer
from .._private.restxml import parse_rest_xml_error
from ..traits import (
    AwsJson1_0Trait,
    AwsJson1_1Trait,
    AwsQueryTrait,
    Ec2QueryTrait,
    RestJson1Trait,
    RestXmlTrait,
)
from ..utils import (
    parse_document_discriminator,
    parse_error_code,
    parse_response_metadata,
    parse_retry_after,
)

try:
    from smithy_json import JSONCodec, JSONDocument

    _HAS_JSON = True
except ImportError:
    _HAS_JSON = False  # type: ignore

try:
    from smithy_xml import XMLCodec

    _HAS_XML = True
except ImportError:
    _HAS_XML = False  # type: ignore

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
    from smithy_json import JSONCodec, JSONDocument
    from smithy_xml import XMLCodec
    from typing_extensions import TypeForm


def _assert_json() -> None:
    if not _HAS_JSON:
        raise MissingDependencyError(
            "Attempted to use JSON codec, but smithy-json is not installed."
        )


def _assert_xml() -> None:
    if not _HAS_XML:
        raise MissingDependencyError(
            "Attempted to use XML codec, but smithy-xml is not installed."
        )


def _assert_event_stream() -> None:
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


if TYPE_CHECKING or _HAS_JSON:

    class AWSJSONDocument(JSONDocument):
        @property
        def discriminator(self) -> ShapeID:
            if self.shape_type is ShapeType.STRUCTURE:
                return self._schema.id
            parsed = parse_document_discriminator(
                self, self._settings.default_namespace
            )
            if parsed is None:
                raise DiscriminatorError(
                    f"Unable to parse discriminator for {self.shape_type} document."
                )
            return parsed
else:

    class AWSJSONDocument:  # type: ignore[no-redef]
        pass


class _AWSResponseMetadataMixin:
    """Adds AWS request identifiers to extracted response metadata.

    Mixed in ahead of the HTTP base class, which supplies only the status code.
    AWS protocols built on different HTTP bases each include it.
    """

    def extract_response_metadata(
        self,
        *,
        response: HTTPResponse,
        context: TypedProperties,
    ) -> ResponseMetadata:
        return parse_response_metadata(response)


class _AWSHttpBindingClientProtocol(
    _AWSResponseMetadataMixin, HttpBindingClientProtocol
):
    """Base for the AWS protocols that use HTTP bindings: restJson1 and restXml.

    Adds AWS response metadata and event streams. Events are framed as
    ``application/vnd.amazon.eventstream``, and structured event payloads use the
    protocol's payload codec.
    """

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

        # The HTTP body must be an async writeable. The HTTP serializers are responsible
        # for ensuring this.
        body = request.body
        if not isinstance(body, AsyncWriter) or not iscoroutinefunction(body.write):
            raise UnsupportedStreamError(
                "Input streams require an async write function, but none was present "
                "on the serialized HTTP request."
            )

        return AWSEventPublisher[Event](
            payload_codec=self.payload_codec,
            async_writer=body,
            signing_config=signing_config,
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
        _assert_event_stream()
        return AWSEventReceiver(
            payload_codec=self.payload_codec,
            source=AsyncBytesReader(response.body),
            deserializer=event_deserializer,
        )


class RestJsonClientProtocol(_AWSHttpBindingClientProtocol):
    """An implementation of the aws.protocols#restJson1 protocol."""

    _id: Final = RestJson1Trait.id
    _content_type: Final = "application/json"
    _error_identifier: Final = AWSErrorIdentifier()

    def __init__(self, settings: ProtocolSettings) -> None:
        _assert_json()
        self._codec: Final = JSONCodec(
            document_class=AWSJSONDocument,
            default_namespace=settings.namespace,
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

    def _retry_after(self, response: HTTPResponse) -> float | None:
        return parse_retry_after(response)

    def _resolve_error_id(
        self,
        *,
        operation: APIOperation[Any, Any],
        error_id: ShapeID,
    ) -> ShapeID:
        for error_schema in operation.error_schemas:
            if error_schema.id.name == error_id.name:
                return error_schema.id
        return error_id


class RestXmlClientProtocol(_AWSHttpBindingClientProtocol):
    """An implementation of the aws.protocols#restXml protocol."""

    _id: Final = RestXmlTrait.id
    _content_type: Final = "application/xml"

    def __init__(self, settings: ProtocolSettings) -> None:
        _assert_xml()
        self._namespace: Final = settings.namespace
        self._codec: Final = XMLCodec(default_namespace=settings.xml_namespace)

    @property
    def id(self) -> ShapeID:
        return self._id

    @property
    def payload_codec(self) -> Codec:
        return self._codec

    @property
    def content_type(self) -> str:
        return self._content_type

    async def _create_error(
        self,
        operation: APIOperation[Any, Any],
        request: HTTPRequest,
        response: HTTPResponse,
        response_body: SyncStreamingBlob,
        error_registry: TypeRegistry,
        context: TypedProperties,
    ) -> CallError:
        if isinstance(response_body, bytes | bytearray):
            body = bytes(response_body)
        else:
            body = response_body.read()

        retry_after = parse_retry_after(response)
        error_info = parse_rest_xml_error(body)
        code = error_info.code
        error_id = None
        if code is not None:
            error_id = ShapeID.from_parts(namespace=self._namespace, name=code)
            for error_schema in operation.error_schemas:
                if error_schema.id.name == code:
                    error_id = error_schema.id
                    break

        if error_id is not None and error_id in error_registry:
            error_shape = error_registry.get(error_id)
            if not issubclass(error_shape, ModeledError):
                raise ExpectationNotMetError(
                    "Modeled errors must be derived from 'ModeledError', "
                    f"but got {error_shape}"
                )

            deserializer = HTTPResponseDeserializer(
                payload_codec=_XMLErrorCodec(self._codec, error_info.wrapper_elements),
                http_trait=operation.schema.expect_trait(HTTPTrait),
                response=response,
                body=body,
            )
            modeled_error = error_shape.deserialize(deserializer)
            if not modeled_error.message and error_info.message:
                modeled_error.message = error_info.message
                # The exception's args were taken from the empty message when it
                # was constructed, so they're replaced for the message to display.
                modeled_error.args = (error_info.message,)
            if retry_after is not None:
                modeled_error.retry_after = retry_after
            return modeled_error

        message = (
            f"Unknown error for operation {operation.schema.id} "
            f"- status: {response.status}"
        )
        if code is not None:
            message += f" - code: {code}"
        if error_info.message:
            message += f" - message: {error_info.message}"
        if response.reason is not None:
            message += f" - reason: {response.reason}"

        is_timeout = response.status == 408
        is_throttle = response.status == 429
        return CallError(
            message=message,
            fault="client" if response.status < 500 else "server",
            is_throttling_error=is_throttle,
            is_timeout_error=is_timeout,
            is_retry_safe=is_throttle or is_timeout or None,
            retry_after=retry_after,
        )


@dataclass(frozen=True)
class _XMLErrorCodec(Codec):
    """Reads an error's members from inside its restXml wrapper elements."""

    codec: "XMLCodec"
    wrapper_elements: tuple[str, ...]

    @property
    def media_type(self) -> str:
        return self.codec.media_type

    def create_serializer(self, sink: BytesWriter) -> ShapeSerializer:
        return self.codec.create_serializer(sink)

    def create_deserializer(self, source: bytes | BytesReader) -> ShapeDeserializer:
        return self.codec.create_deserializer(
            source, wrapper_elements=self.wrapper_elements
        )


class _AWSJSONClientProtocol(_AWSResponseMetadataMixin, HttpClientProtocol):
    _error_identifier: Final = AWSErrorIdentifier()

    _id: ClassVar[ShapeID]
    _content_type: ClassVar[str]

    def __init__(self, settings: ProtocolSettings) -> None:
        _assert_json()
        self._service_name: Final = settings.service_target
        self._codec: Final = JSONCodec(
            document_class=AWSJSONDocument,
            default_namespace=settings.namespace,
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
        return _HTTPRequest(
            method="POST",
            destination=_URI(host="", path="/"),
            fields=tuples_to_fields(
                [
                    ("content-type", self.content_type),
                    ("content-length", str(len(payload))),
                    (
                        "x-amz-target",
                        f"{self._service_name}.{operation.schema.id.name}",
                    ),
                ]
            ),
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

        if not self._is_success(operation, context, response):
            raise await self._create_error(
                operation=operation,
                response=response,
                response_body=body,
                error_registry=error_registry,
                context=context,
            )

        if len(body) == 0:
            body = b"{}"
        return self.payload_codec.deserialize(source=body, shape=operation.output)

    def _is_success(
        self,
        operation: APIOperation[Any, Any],
        context: TypedProperties,
        response: HTTPResponse,
    ) -> bool:
        return 200 <= response.status < 300

    async def _create_error(
        self,
        *,
        operation: APIOperation[Any, Any],
        response: HTTPResponse,
        response_body: bytes,
        error_registry: TypeRegistry,
        context: TypedProperties,
    ) -> CallError:
        error_id = self.error_identifier.identify(
            operation=operation, response=response
        )
        if error_id is not None and error_id not in error_registry:
            error_id = self._resolve_error_id(operation=operation, error_id=error_id)

        retry_after = parse_retry_after(response)

        if (
            error_id is None
            and len(response_body) > 0
            and self._matches_content_type(response)
        ):
            deserializer = self.payload_codec.create_deserializer(response_body)
            document = deserializer.read_document(schema=DOCUMENT)
            document_error_id = document.discriminator
            if document_error_id not in error_registry:
                document_error_id = self._resolve_error_id(
                    operation=operation, error_id=document_error_id
                )

            if document_error_id in error_registry:
                error_id = document_error_id

        if error_id is not None and error_id in error_registry:
            error_shape = error_registry.get(error_id)

            # make sure the error shape is derived from modeled exception
            if not issubclass(error_shape, ModeledError):
                raise ExpectationNotMetError(
                    f"Modeled errors must be derived from 'ModeledError', "
                    f"but got {error_shape}"
                )

            body = response_body if len(response_body) > 0 else b"{}"
            deserializer = self.payload_codec.create_deserializer(body)
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
            retry_after=retry_after,
        )

    def _matches_content_type(self, response: HTTPResponse) -> bool:
        if "content-type" not in response.fields:
            return False
        actual = response.fields["content-type"].as_string()
        return actual.split(";", 1)[0].strip().lower() == self.content_type.lower()

    def _resolve_error_id(
        self,
        *,
        operation: APIOperation[Any, Any],
        error_id: ShapeID,
    ) -> ShapeID:
        for error_schema in operation.error_schemas:
            if error_schema.id.name == error_id.name:
                return error_schema.id
        return error_id


class AwsJson10ClientProtocol(_AWSJSONClientProtocol):
    """An implementation of the aws.protocols#awsJson1_0 protocol."""

    _id: ClassVar[ShapeID] = AwsJson1_0Trait.id
    _content_type: ClassVar[str] = "application/x-amz-json-1.0"


class AwsJson11ClientProtocol(_AWSJSONClientProtocol):
    """An implementation of the aws.protocols#awsJson1_1 protocol."""

    _id: ClassVar[ShapeID] = AwsJson1_1Trait.id
    _content_type: ClassVar[str] = "application/x-amz-json-1.1"


@dataclass(frozen=True)
class _RecordedQueryRequestId:
    """A body-sourced request ID bound to the response it was parsed from.

    Retry attempts share one properties object, so the ID is tagged with its
    source response. ``extract_response_metadata`` only trusts it for that exact
    response, so a later attempt that fails before recording its own ID (for
    example, when a pre-deserialization hook raises) cannot surface an earlier
    attempt's ID.
    """

    response: HTTPResponse
    value: str


_QUERY_REQUEST_ID = PropertyKey(
    key="aws_query_request_id", value_type=_RecordedQueryRequestId
)
"""Where :py:class:`AwsQueryClientProtocol` records a body-sourced request ID.

The body is only available while deserializing, so the value is stored there for
``extract_response_metadata`` to read back.
"""


class AwsQueryClientProtocol(_AWSResponseMetadataMixin, HttpClientProtocol):
    """An implementation of the aws.protocols#awsQuery protocol."""

    _id: ClassVar[ShapeID] = AwsQueryTrait.id
    _content_type: Final = "application/x-www-form-urlencoded"

    def __init__(self, settings: ProtocolSettings) -> None:
        _assert_xml()
        if settings.version is None:
            raise ExpectationNotMetError(
                f"The {self._id.name} protocol requires a service version, but "
                "ProtocolSettings.version was None."
            )
        self._default_namespace: Final = settings.namespace
        self._version: Final = settings.version
        self._codec: Final = XMLCodec()

    @property
    def id(self) -> ShapeID:
        return self._id

    @property
    def payload_codec(self) -> "XMLCodec":
        return self._codec

    @property
    def content_type(self) -> str:
        return self._content_type

    def extract_response_metadata(
        self,
        *,
        response: HTTPResponse,
        context: TypedProperties,
    ) -> ResponseMetadata:
        """Report the request ID, using the one recorded from the body as a fallback.

        awsQuery normally carries the identifier in the body rather than a header, so
        the mixin's header lookup usually finds nothing and the body value recorded
        during deserialization is used. A header still wins when a service sends one.
        """
        metadata = _AWSResponseMetadataMixin.extract_response_metadata(
            self, response=response, context=context
        )
        if metadata.request_id is not None:
            return metadata
        # Relies on transport_response identity being preserved from
        # deserialize_response through to here; if that ever changes, this safely
        # reports no ID rather than a wrong one.
        recorded = context.get(_QUERY_REQUEST_ID)
        if recorded is None or recorded.response is not response:
            return metadata
        return replace(metadata, request_id=recorded.value)

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
        sink = BytesIO()
        params: list[tuple[str, str]] = []
        serializer = self._create_serializer(
            sink=sink,
            action=self._action_name(operation),
            params=params,
        )
        input.serialize(serializer)
        serializer.flush()
        content_length = sink.tell()
        sink.seek(0)
        body = AsyncBytesReader(sink)
        return _HTTPRequest(
            method="POST",
            destination=_URI(host="", path="/"),
            fields=tuples_to_fields(
                [
                    ("content-type", self.content_type),
                    ("content-length", str(content_length)),
                ]
            ),
            body=body,
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

        # Recorded before any branch below returns or raises, so successes, empty
        # outputs and errors alike can report the identifier. Bound to this
        # response so extraction never attributes it to a different attempt.
        request_id = parse_aws_query_request_id(body)
        if request_id is not None:
            context[_QUERY_REQUEST_ID] = _RecordedQueryRequestId(response, request_id)

        if not self._is_success(operation, context, response):
            raise await self._create_error(
                operation=operation,
                response=response,
                response_body=body,
                error_registry=error_registry,
                context=context,
            )

        if len(body) == 0:
            return operation.output.deserialize(
                HTTPResponseDeserializer(
                    payload_codec=self.payload_codec,
                    response=response,
                    body=body,
                )
            )

        wrapper_elements = self._response_wrapper_elements(operation)
        deserializer = self.payload_codec.create_deserializer(
            body, wrapper_elements=wrapper_elements
        )
        return operation.output.deserialize(deserializer)

    def _is_success(
        self,
        operation: APIOperation[Any, Any],
        context: TypedProperties,
        response: HTTPResponse,
    ) -> bool:
        return 200 <= response.status < 300

    async def _create_error(
        self,
        *,
        operation: APIOperation[Any, Any],
        response: HTTPResponse,
        response_body: bytes,
        error_registry: TypeRegistry,
        context: TypedProperties,
    ) -> CallError:
        return create_aws_query_error(
            body=response_body,
            operation=operation,
            error_registry=error_registry,
            default_namespace=self._default_namespace,
            wrapper_elements=self._error_wrapper_elements(),
            status=response.status,
            context=context,
            retry_after=parse_retry_after(response),
        )

    def _create_serializer(
        self,
        *,
        sink: BytesIO,
        action: str,
        params: list[tuple[str, str]],
    ) -> QueryShapeSerializer:
        return QueryShapeSerializer(
            sink=sink, action=action, version=self._version, params=params
        )

    def _action_name(
        self,
        operation: APIOperation[SerializeableShape, DeserializeableShape],
    ) -> str:
        return operation.schema.id.name

    def _response_wrapper_elements(
        self,
        operation: APIOperation[SerializeableShape, DeserializeableShape],
    ) -> tuple[str, ...]:
        name = operation.schema.id.name
        # Operations with no output members will omit the <OpResult> element.
        if not operation.output_schema.members:
            return (f"{name}Response",)
        return (
            f"{name}Response",
            f"{name}Result",
        )

    def _error_wrapper_elements(self) -> tuple[str, ...]:
        return ("ErrorResponse", "Error")


class Ec2QueryClientProtocol(AwsQueryClientProtocol):
    """An implementation of the aws.protocols#ec2Query protocol.

    An EC2-specific extension of awsQuery: input keys resolve via ``@ec2QueryName``
    and lists are always flattened; responses have no ``Result`` wrapper and errors
    nest under ``<Response><Errors><Error>``.
    """

    _id: ClassVar[ShapeID] = Ec2QueryTrait.id

    def _create_serializer(
        self,
        *,
        sink: BytesIO,
        action: str,
        params: list[tuple[str, str]],
    ) -> QueryShapeSerializer:
        return Ec2QueryShapeSerializer(
            sink=sink, action=action, version=self._version, params=params
        )

    def _response_wrapper_elements(
        self,
        operation: APIOperation[SerializeableShape, DeserializeableShape],
    ) -> tuple[str, ...]:
        return (f"{operation.schema.id.name}Response",)

    def _error_wrapper_elements(self) -> tuple[str, ...]:
        return ("Response", "Errors", "Error")
