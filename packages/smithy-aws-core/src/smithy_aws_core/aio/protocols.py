# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Callable
from inspect import iscoroutinefunction
from io import BytesIO
from typing import TYPE_CHECKING, Any, Final

from smithy_core import URI as _URI
from smithy_core.aio.interfaces import AsyncWriter
from smithy_core.aio.interfaces.auth import AuthScheme
from smithy_core.aio.interfaces.eventstream import EventPublisher, EventReceiver
from smithy_core.aio.types import AsyncBytesReader
from smithy_core.codecs import Codec
from smithy_core.deserializers import DeserializeableShape, ShapeDeserializer
from smithy_core.documents import TypeRegistry
from smithy_core.exceptions import (
    CallError,
    DiscriminatorError,
    MissingDependencyError,
    UnsupportedStreamError,
)
from smithy_core.interfaces import TypedProperties, URI
from smithy_core.schemas import APIOperation, Schema
from smithy_core.serializers import SerializeableShape
from smithy_core.shapes import ShapeID, ShapeType
from smithy_core.types import TimestampFormat
from smithy_http import tuples_to_fields
from smithy_http.aio import HTTPRequest as _HTTPRequest
from smithy_http.aio.interfaces import HTTPErrorIdentifier, HTTPRequest, HTTPResponse
from smithy_http.aio.protocols import HttpBindingClientProtocol, HttpClientProtocol
from smithy_http.deserializers import HTTPResponseDeserializer

from .._private.query.errors import (
    create_aws_query_error,
)
from .._private.query.serializers import QueryShapeSerializer
from ..traits import AwsQueryTrait, RestJson1Trait
from ..utils import parse_document_discriminator, parse_error_code

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
            "Attempted to use JSON protocol support, but smithy-json is not installed."
        )


def _assert_xml() -> None:
    if not _HAS_XML:
        raise MissingDependencyError(
            "Attempted to use XML protocol support, but smithy-xml is not installed."
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


class RestJsonClientProtocol(HttpBindingClientProtocol):
    """An implementation of the aws.protocols#restJson1 protocol."""

    _id: Final = RestJson1Trait.id
    _contentType: Final = "application/json"
    _error_identifier: Final = AWSErrorIdentifier()

    def __init__(self, service_schema: Schema) -> None:
        """Initialize a RestJsonClientProtocol.

        :param service: The schema for the service to interact with.
        """
        _assert_json()
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
        return self._contentType

    @property
    def error_identifier(self) -> HTTPErrorIdentifier:
        return self._error_identifier

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


class AwsQueryClientProtocol(HttpClientProtocol):
    """An implementation of the aws.protocols#awsQuery protocol."""

    _id: Final = AwsQueryTrait.id
    _content_type: Final = "application/x-www-form-urlencoded"

    def __init__(self, service_schema: Schema, version: str) -> None:
        _assert_xml()
        self._default_namespace: Final = service_schema.id.namespace
        self._version: Final = version
        self._codec: Final = XMLCodec(default_namespace=self._default_namespace)

    @property
    def id(self) -> ShapeID:
        return self._id

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
        serializer = QueryShapeSerializer(
            sink=sink,
            action=self._action_name(operation),
            version=self._version,
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
                    ("content-type", self._content_type),
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

        if response.status >= 300:
            raise self._create_error(
                operation=operation,
                response=response,
                response_body=body,
                error_registry=error_registry,
            )

        if len(body) == 0:
            return operation.output.deserialize(
                HTTPResponseDeserializer(
                    payload_codec=self._codec,
                    response=response,
                    body=body,
                )
            )

        wrapper_elements = self._response_wrapper_elements(operation)
        deserializer = self._codec.create_deserializer(
            body, wrapper_elements=wrapper_elements
        )
        return operation.output.deserialize(deserializer)

    def _create_error(
        self,
        *,
        operation: APIOperation[Any, Any],
        response: HTTPResponse,
        response_body: bytes,
        error_registry: TypeRegistry,
    ) -> CallError:
        return create_aws_query_error(
            body=response_body,
            operation=operation,
            error_registry=error_registry,
            default_namespace=self._default_namespace,
            wrapper_elements=self._error_wrapper_elements(),
            status=response.status,
        )

    def _action_name(
        self,
        operation: APIOperation[SerializeableShape, DeserializeableShape],
    ) -> str:
        return operation.schema.id.name

    def _response_wrapper_elements(
        self,
        operation: APIOperation[SerializeableShape, DeserializeableShape],
    ) -> tuple[str, str]:
        return (
            f"{operation.schema.id.name}Response",
            f"{operation.schema.id.name}Result",
        )

    def _error_wrapper_elements(self) -> tuple[str, ...]:
        return ("ErrorResponse", "Error")
