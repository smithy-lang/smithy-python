# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from base64 import b64encode
from collections.abc import Callable, Iterator, Sized
from contextlib import AbstractContextManager, contextmanager
from datetime import datetime
from decimal import Decimal
from inspect import iscoroutinefunction
from io import BytesIO
from types import TracebackType
from typing import TYPE_CHECKING
from urllib.parse import quote as urlquote

from smithy_core import URI
from smithy_core.aio.types import AsyncBytesProvider, AsyncBytesReader
from smithy_core.codecs import Codec
from smithy_core.exceptions import SerializationError
from smithy_core.schemas import Schema
from smithy_core.serializers import (
    InterceptingSerializer,
    MapSerializer,
    ShapeSerializer,
    SpecificShapeSerializer,
)
from smithy_core.traits import (
    EndpointTrait,
    HTTPHeaderTrait,
    HTTPPrefixHeadersTrait,
    HTTPQueryTrait,
    HTTPTrait,
    MediaTypeTrait,
    TimestampFormatTrait,
)
from smithy_core.types import PathPattern, TimestampFormat
from smithy_core.utils import serialize_float

from . import Field, tuples_to_fields
from .aio import HTTPRequest as _HTTPRequest
from .aio import HTTPResponse as _HTTPResponse
from .aio.interfaces import HTTPRequest, HTTPResponse
from .bindings import Binding, RequestBindingMatcher
from .schema_extensions import (
    HTTP_BINDING_SCHEMA_EXTENSION,
    HTTPBindingSchemaMetadata,
    HTTPMemberBindingMetadata,
    HTTPOperationSchemaMetadata,
)
from .utils import join_query_params

if TYPE_CHECKING:
    from smithy_core.aio.interfaces import StreamingBlob as AsyncStreamingBlob


__all__ = [
    "HTTPBindingSerializer",
    "HTTPRequestSerializer",
    "HTTPResponseSerializer",
]


# TODO: refactor this to share code with response serializer
class HTTPRequestSerializer(SpecificShapeSerializer):
    """Binds a serializable shape to an HTTP request.

    The resultant HTTP request is not immediately sendable. In particular, the host of
    the destination URI is incomplete and MUST be suffixed before sending.
    """

    def __init__(
        self,
        payload_codec: Codec,
        http_trait: HTTPTrait,
        endpoint_trait: EndpointTrait | None = None,
        omit_empty_payload: bool = True,
        operation_metadata: HTTPOperationSchemaMetadata | None = None,
    ) -> None:
        """Initialize an HTTPRequestSerializer.

        :param payload_codec: The codec to use to serialize the HTTP payload, if one is
            present.
        :param http_trait: The HTTP trait of the operation being handled.
        :param endpoint_trait: The optional endpoint trait of the operation being
            handled.
        :param omit_empty_payload: Whether an empty payload should be omitted.
        :param operation_metadata: Optional cached operation binding metadata.
        """
        self._http_trait = http_trait
        self._endpoint_trait = endpoint_trait
        self._payload_codec = payload_codec
        self._omit_empty_payload = omit_empty_payload
        self._operation_metadata = operation_metadata
        self.result: HTTPRequest | None = None

    @contextmanager
    def begin_struct(self, schema: Schema) -> Iterator[ShapeSerializer]:
        binding_serializer = HTTPBindingSerializer(
            payload_codec=self._payload_codec,
            schema=schema,
            http_trait=self._http_trait,
            endpoint_trait=self._endpoint_trait,
            omit_empty_payload=self._omit_empty_payload,
            operation_metadata=self._operation_metadata,
        )
        try:
            yield binding_serializer
        except BaseException as error:
            binding_serializer.abort(type(error), error, error.__traceback__)
            raise
        else:
            self.result = binding_serializer.build_request()


def _compute_content_length(
    payload: object,
) -> int | None:
    if (tell := getattr(payload, "tell", None)) is not None and not iscoroutinefunction(
        tell
    ):
        start: int = tell()
        if (end := _seek(payload, 0, 2)) is not None:
            content_length: int = end - start
            _seek(payload, start, 0)
            return content_length
    return None


def _seek(payload: object, pos: int, whence: int = 0) -> int | None:
    if (seek := getattr(payload, "seek", None)) is not None and not iscoroutinefunction(
        seek
    ):
        return seek(pos, whence)
    return None


class HTTPBindingSerializer(InterceptingSerializer):
    """Serialize structure members into HTTP request binding locations.

    Generated structures drive this serializer directly through
    :py:meth:`SerializeableStruct.serialize_members`. Call
    :py:meth:`build_request` after all members have been written.
    """

    def __init__(
        self,
        *,
        payload_codec: Codec,
        schema: Schema,
        http_trait: HTTPTrait,
        endpoint_trait: EndpointTrait | None = None,
        omit_empty_payload: bool = True,
        operation_metadata: HTTPOperationSchemaMetadata | None = None,
    ) -> None:
        """Initialize an HTTPBindingSerializer.

        :param payload_codec: The codec used to serialize document-bound members.
        :param schema: The structure schema whose members are being serialized.
        :param http_trait: The HTTP trait of the operation being handled.
        :param endpoint_trait: The optional endpoint trait of the operation.
        :param omit_empty_payload: Whether an empty document payload should be omitted.
        :param operation_metadata: Optional cached operation binding metadata.
        """
        self._operation_metadata = operation_metadata or (
            HTTPOperationSchemaMetadata.from_traits(http_trait, endpoint_trait)
        )
        self._binding_metadata: HTTPBindingSchemaMetadata = schema.get_extension(
            HTTP_BINDING_SCHEMA_EXTENSION
        )
        request_metadata = self._binding_metadata.request
        self._body_context: AbstractContextManager[ShapeSerializer] | None = None
        self._sync_payload: BytesIO | None = None
        self._raw_payload_serializer: RawPayloadSerializer | None = None
        self._payload: AsyncBytesReader | AsyncBytesProvider | None = None
        self._content_type: str | None = payload_codec.media_type
        self._content_length: int | None = None
        self._content_length_required = False
        self._writes_document_body = False
        self._result: HTTPRequest | None = None

        if request_metadata.event_stream_member is not None:
            self._payload = AsyncBytesProvider()
            self._content_type = "application/vnd.amazon.eventstream"
            payload_serializer: ShapeSerializer = SpecificShapeSerializer()
        elif (payload_metadata := request_metadata.payload) is not None:
            self._content_length_required = payload_metadata.requires_length
            if payload_metadata.is_raw:
                self._content_type = payload_metadata.media_type
                self._raw_payload_serializer = RawPayloadSerializer()
                payload_serializer = self._raw_payload_serializer
            else:
                if payload_metadata.media_type is not None:
                    self._content_type = payload_metadata.media_type
                self._sync_payload = BytesIO()
                payload_serializer = payload_codec.create_serializer(self._sync_payload)
        else:
            self._sync_payload = BytesIO()
            payload_serializer = payload_codec.create_serializer(self._sync_payload)
            self._writes_document_body = (
                self._binding_metadata.should_write_request_body(omit_empty_payload)
            )
            if self._writes_document_body:
                self._body_context = payload_serializer.begin_struct(schema)
                payload_serializer = self._body_context.__enter__()
            else:
                self._content_type = None

        self._payload_serializer = payload_serializer
        self.header_serializer = HTTPHeaderSerializer(
            header_names=request_metadata.header_names,
        )
        self.query_serializer = HTTPQuerySerializer(
            query_param_exclusions=(
                request_metadata.query_names
                | self._operation_metadata.query_literal_names
            ),
        )
        self.path_serializer = HTTPPathSerializer(
            self._operation_metadata.path,
            greedy_label_names=self._operation_metadata.greedy_label_names,
        )
        self.host_prefix_serializer = HostPrefixSerializer(
            payload_serializer,
            self._operation_metadata.host_prefix,
        )

    def before(self, schema: Schema) -> ShapeSerializer:
        metadata = self._binding_metadata.members[schema.expect_member_index()]
        match metadata.request_binding:
            case Binding.HEADER | Binding.PREFIX_HEADERS:
                self.header_serializer.set_member_metadata(metadata)
                return self.header_serializer
            case Binding.QUERY | Binding.QUERY_PARAMS:
                self.query_serializer.set_member_metadata(metadata)
                return self.query_serializer
            case Binding.LABEL:
                self.path_serializer.set_member_metadata(metadata)
                return self.path_serializer
            case Binding.HOST:
                self.host_prefix_serializer.set_member_metadata(metadata)
                return self.host_prefix_serializer
            case _:
                return self._payload_serializer

    def after(self, schema: Schema) -> None:
        pass

    def build_request(self) -> HTTPRequest:
        """Build the HTTP request after payload serialization."""
        if self._result is not None:
            return self._result

        if self._body_context is not None:
            self._body_context.__exit__(None, None, None)
            self._body_context = None

        payload = self._payload
        if self._raw_payload_serializer is not None:
            raw_payload = self._raw_payload_serializer.payload
            if isinstance(raw_payload, Sized):
                self._content_length = len(raw_payload)
            payload = AsyncBytesReader(raw_payload or b"")
        elif self._sync_payload is not None:
            if (
                self._binding_metadata.request.payload is not None
                or self._writes_document_body
            ):
                self._content_length = self._sync_payload.tell()
            self._sync_payload.seek(0)
            payload = AsyncBytesReader(self._sync_payload)

        assert payload is not None  # noqa: S101

        headers = self.header_serializer.headers
        if self._content_type is not None and (
            not self._binding_metadata.request.has_content_type_header
            or not any(name.lower() == "content-type" for name, _ in headers)
        ):
            headers.append(("content-type", self._content_type))

        if self._content_length is not None:
            headers.append(("content-length", str(self._content_length)))

        fields = tuples_to_fields(headers)
        if self._content_length_required and "content-length" not in fields:
            content_length = _compute_content_length(payload)
            if content_length is None:
                raise SerializationError(
                    "This operation requires the content length of the input "
                    "stream, but it was not provided and was unable to be computed."
                )
            fields.set_field(Field(name="content-length", values=[str(content_length)]))

        self._result = _HTTPRequest(
            method=self._operation_metadata.method,
            destination=URI(
                host=self.host_prefix_serializer.host_prefix,
                path=self.path_serializer.path,
                query=join_query_params(
                    params=self.query_serializer.query_params,
                    prefix=self._operation_metadata.query or "",
                ),
            ),
            fields=fields,
            body=payload,
        )
        return self._result

    def abort(
        self,
        exc_type: type[BaseException],
        exc_value: BaseException,
        traceback: TracebackType | None,
    ) -> None:
        """Abort an in-progress document payload after serialization fails."""
        if self._body_context is not None:
            self._body_context.__exit__(exc_type, exc_value, traceback)
            self._body_context = None


class HTTPRequestBindingSerializer(InterceptingSerializer):
    """Legacy request binding router.

    New code should use :py:class:`HTTPBindingSerializer`, which also owns payload
    setup and request finalization.
    """

    def __init__(
        self,
        payload_serializer: ShapeSerializer,
        path_pattern: PathPattern,
        host_prefix_pattern: str,
        binding_matcher: RequestBindingMatcher,
    ) -> None:
        self._payload_serializer = payload_serializer
        self.header_serializer = HTTPHeaderSerializer()
        self.query_serializer = HTTPQuerySerializer()
        self.path_serializer = HTTPPathSerializer(path_pattern)
        self.host_prefix_serializer = HostPrefixSerializer(
            payload_serializer, host_prefix_pattern
        )
        self._binding_matcher = binding_matcher

    def before(self, schema: Schema) -> ShapeSerializer:
        match self._binding_matcher.match(schema):
            case Binding.HEADER | Binding.PREFIX_HEADERS:
                return self.header_serializer
            case Binding.QUERY | Binding.QUERY_PARAMS:
                return self.query_serializer
            case Binding.LABEL:
                return self.path_serializer
            case Binding.HOST:
                return self.host_prefix_serializer
            case _:
                return self._payload_serializer

    def after(self, schema: Schema) -> None:
        pass


class HTTPResponseSerializer(SpecificShapeSerializer):
    """Binds a serializable shape to an HTTP response."""

    def __init__(
        self,
        payload_codec: Codec,
        http_trait: HTTPTrait,
        omit_empty_payload: bool = True,
        operation_metadata: HTTPOperationSchemaMetadata | None = None,
    ) -> None:
        """Initialize an HTTPResponseSerializer.

        :param payload_codec: The codec to use to serialize the HTTP payload, if one is
            present.
        :param http_trait: The HTTP trait of the operation being handled.
        :param omit_empty_payload: Whether an empty payload should be omitted.
        :param operation_metadata: Optional cached operation binding metadata.
        """
        self._operation_metadata = operation_metadata or (
            HTTPOperationSchemaMetadata.from_traits(http_trait)
        )
        self._payload_codec = payload_codec
        self.result: HTTPResponse | None = None
        self._omit_empty_payload = omit_empty_payload

    @contextmanager
    def begin_struct(self, schema: Schema) -> Iterator[ShapeSerializer]:
        payload: AsyncBytesReader | AsyncBytesProvider
        binding_serializer: HTTPResponseBindingSerializer

        content_type: str | None = self._payload_codec.media_type
        content_length: int | None = None
        content_length_source: object | None = None
        content_length_required = False

        binding_metadata = schema.get_extension(HTTP_BINDING_SCHEMA_EXTENSION)
        response_metadata = binding_metadata.response
        if response_metadata.event_stream_member is not None:
            payload = AsyncBytesProvider()
            content_type = "application/vnd.amazon.eventstream"
            binding_serializer = HTTPResponseBindingSerializer(
                SpecificShapeSerializer(), binding_metadata
            )
            yield binding_serializer
        elif (payload_metadata := response_metadata.payload) is not None:
            content_length_required = payload_metadata.requires_length
            if payload_metadata.is_raw:
                content_type = payload_metadata.media_type
                payload_serializer = RawPayloadSerializer()
                binding_serializer = HTTPResponseBindingSerializer(
                    payload_serializer, binding_metadata
                )
                yield binding_serializer
                raw_payload = payload_serializer.payload
                if isinstance(raw_payload, Sized):
                    content_length = len(raw_payload)
                content_length_source = raw_payload
                payload = AsyncBytesReader(raw_payload or b"")
            else:
                if payload_metadata.media_type is not None:
                    content_type = payload_metadata.media_type
                sync_payload = BytesIO()
                payload_serializer = self._payload_codec.create_serializer(sync_payload)
                binding_serializer = HTTPResponseBindingSerializer(
                    payload_serializer, binding_metadata
                )
                yield binding_serializer
                content_length = sync_payload.tell()
                sync_payload.seek(0)
                payload = AsyncBytesReader(sync_payload)
        else:
            sync_payload = BytesIO()
            payload_serializer = self._payload_codec.create_serializer(sync_payload)
            if binding_metadata.should_write_response_body(self._omit_empty_payload):
                with payload_serializer.begin_struct(schema) as body_serializer:
                    binding_serializer = HTTPResponseBindingSerializer(
                        body_serializer, binding_metadata
                    )
                    yield binding_serializer
                content_length = sync_payload.tell()
            else:
                content_type = None
                content_length = None
                binding_serializer = HTTPResponseBindingSerializer(
                    payload_serializer,
                    binding_metadata,
                )
                yield binding_serializer
            sync_payload.seek(0)
            payload = AsyncBytesReader(sync_payload)

        headers = binding_serializer.header_serializer.headers
        if content_type is not None and (
            "content-type" not in response_metadata.header_names
            or not any(name.lower() == "content-type" for name, _ in headers)
        ):
            headers.append(("content-type", content_type))

        if content_length is not None:
            headers.append(("content-length", str(content_length)))

        fields = tuples_to_fields(headers)
        if content_length_required and "content-length" not in fields:
            content_length = _compute_content_length(
                content_length_source if content_length_source is not None else payload
            )
            if content_length is None:
                raise SerializationError(
                    "This operation requires the content length of the input "
                    "stream, but it was not provided and was unable to be computed."
                )
            fields.set_field(Field(name="content-length", values=[str(content_length)]))

        status = binding_serializer.response_code_serializer.response_code
        if status is None:
            if binding_metadata.response_status > 0:
                status = binding_metadata.response_status
            else:
                status = self._operation_metadata.response_status

        self.result = _HTTPResponse(
            fields=fields,
            body=payload,
            status=status,
        )


class HTTPResponseBindingSerializer(InterceptingSerializer):
    """Delegates HTTP response bindings to binding-location-specific serializers."""

    def __init__(
        self,
        payload_serializer: ShapeSerializer,
        binding_metadata: HTTPBindingSchemaMetadata,
    ) -> None:
        """Initialize an HTTPResponseBindingSerializer.

        :param payload_serializer: The :py:class:`ShapeSerializer` to use to serialize
            the payload, if necessary.
        """
        self._payload_serializer = payload_serializer
        self.header_serializer = HTTPHeaderSerializer(
            response=True,
            header_names=binding_metadata.response.header_names,
        )
        self.response_code_serializer = HTTPResponseCodeSerializer()
        self._binding_metadata = binding_metadata

    def before(self, schema: Schema) -> ShapeSerializer:
        metadata = self._binding_metadata.members[schema.expect_member_index()]
        match metadata.response_binding:
            case Binding.HEADER | Binding.PREFIX_HEADERS:
                self.header_serializer.set_member_metadata(metadata)
                return self.header_serializer
            case Binding.STATUS:
                return self.response_code_serializer
            case _:
                return self._payload_serializer

    def after(self, schema: Schema) -> None:
        pass


class RawPayloadSerializer(SpecificShapeSerializer):
    """Binds properties of serializable shape to an HTTP payload."""

    payload: "AsyncStreamingBlob | None"
    """The serialized payload.

    This will only be non-null after serialization.
    """

    def __init__(self) -> None:
        """Initialize a RawPayloadSerializer."""
        self.payload: AsyncStreamingBlob | None = None

    def write_string(self, schema: Schema, value: str) -> None:
        self.payload = value.encode("utf-8")

    def write_blob(self, schema: Schema, value: bytes) -> None:
        self.payload = value

    def write_data_stream(self, schema: Schema, value: "AsyncStreamingBlob") -> None:
        self.payload = value


class HTTPHeaderSerializer(SpecificShapeSerializer):
    """Binds properties of a serializable shape to HTTP headers."""

    headers: list[tuple[str, str]]
    """A list of serialized headers.

    This should only be accessed after serialization.
    """

    def __init__(
        self,
        key: str | None = None,
        headers: list[tuple[str, str]] | None = None,
        *,
        response: bool = False,
        header_names: frozenset[str] = frozenset(),
        timestamp_format: TimestampFormat | None = None,
        has_media_type: bool | None = None,
    ) -> None:
        """Initialize an HTTPHeaderSerializer.

        :param key: An optional key to specifically write. If not set, the
            :py:class:`HTTPHeaderTrait` will be checked instead. Required when
            collecting list entries.
        :param headers: An optional list of header tuples to append to. If not
            set, one will be created. Values appended will not be escaped.
        :param response: Whether to use response-direction member metadata.
        :param header_names: Declared explicit header names that take precedence over
            prefix-header map entries.
        :param timestamp_format: A fixed timestamp format for list entries.
        :param has_media_type: Whether list entries require base64 encoding.
        """
        self.headers: list[tuple[str, str]] = headers if headers is not None else []
        self._key = key
        self._member_metadata: HTTPMemberBindingMetadata | None = None
        self._response = response
        self._header_names = header_names
        self._timestamp_format = timestamp_format
        self._has_media_type = has_media_type

    def set_member_metadata(self, metadata: HTTPMemberBindingMetadata) -> None:
        """Set the cached plan for the next top-level member write."""
        self._member_metadata = metadata

    def _key_for(self, schema: Schema) -> str:
        if self._key is not None:
            return self._key
        if (metadata := self._member_metadata) is not None:
            key = (
                metadata.response_wire_name
                if self._response
                else metadata.request_wire_name
            )
            if key is not None:
                return key
        return schema.expect_trait(HTTPHeaderTrait).key

    def _timestamp_format_for(self, schema: Schema) -> TimestampFormat:
        if self._timestamp_format is not None:
            return self._timestamp_format
        if (metadata := self._member_metadata) is not None:
            format = (
                metadata.response_timestamp_format
                if self._response
                else metadata.request_timestamp_format
            )
            if format is not None:
                return format
        if (trait := schema.get_trait(TimestampFormatTrait)) is not None:
            return trait.format
        return TimestampFormat.HTTP_DATE

    def _has_media_type_for(self, schema: Schema) -> bool:
        if self._has_media_type is not None:
            return self._has_media_type
        if (metadata := self._member_metadata) is not None:
            return metadata.media_type is not None
        return MediaTypeTrait in schema

    @contextmanager
    def begin_list(self, schema: Schema, size: int) -> Iterator[ShapeSerializer]:
        metadata = self._member_metadata
        delegate = HTTPHeaderSerializer(
            key=self._key_for(schema),
            headers=self.headers,
            timestamp_format=(
                metadata.response_timestamp_format
                if metadata is not None and self._response
                else (
                    metadata.request_timestamp_format if metadata is not None else None
                )
            ),
            has_media_type=(
                metadata.media_type is not None if metadata is not None else None
            ),
        )
        yield delegate

    @contextmanager
    def begin_map(self, schema: Schema, size: int) -> Iterator[MapSerializer]:
        metadata = self._member_metadata
        prefix = (
            (
                metadata.response_wire_name
                if self._response
                else metadata.request_wire_name
            )
            if metadata is not None
            else None
        )
        if prefix is None:
            prefix = schema.expect_trait(HTTPPrefixHeadersTrait).prefix
        yield HTTPHeaderMapSerializer(prefix, self.headers, self._header_names)

    def write_boolean(self, schema: Schema, value: bool) -> None:
        self.headers.append((self._key_for(schema), "true" if value else "false"))

    def write_byte(self, schema: Schema, value: int) -> None:
        self.headers.append((self._key_for(schema), str(value)))

    def write_short(self, schema: Schema, value: int) -> None:
        self.headers.append((self._key_for(schema), str(value)))

    def write_integer(self, schema: Schema, value: int) -> None:
        self.headers.append((self._key_for(schema), str(value)))

    def write_long(self, schema: Schema, value: int) -> None:
        self.headers.append((self._key_for(schema), str(value)))

    def write_big_integer(self, schema: Schema, value: int) -> None:
        self.headers.append((self._key_for(schema), str(value)))

    def write_float(self, schema: Schema, value: float) -> None:
        self.headers.append((self._key_for(schema), serialize_float(value)))

    def write_double(self, schema: Schema, value: float) -> None:
        self.headers.append((self._key_for(schema), serialize_float(value)))

    def write_big_decimal(self, schema: Schema, value: Decimal) -> None:
        self.headers.append((self._key_for(schema), serialize_float(value)))

    def write_string(self, schema: Schema, value: str) -> None:
        if self._has_media_type_for(schema):
            value = b64encode(value.encode("utf-8")).decode("utf-8")
        self.headers.append((self._key_for(schema), value))

    def write_timestamp(self, schema: Schema, value: datetime) -> None:
        self.headers.append(
            (
                self._key_for(schema),
                str(self._timestamp_format_for(schema).serialize(value)),
            )
        )


class HTTPHeaderMapSerializer(MapSerializer):
    """Binds a mapping property of a serializeable shape to multiple HTTP headers."""

    def __init__(
        self,
        prefix: str,
        headers: list[tuple[str, str]],
        header_names: frozenset[str] = frozenset(),
    ) -> None:
        """Initialize an HTTPHeaderMapSerializer.

        :param prefix: The prefix to prepend to each of the map keys.
        :param headers: The list of header tuples to append to.
        :param header_names: Explicit header names that take precedence over map keys.
        """
        self._prefix = prefix
        self._headers = headers
        self._header_names = header_names
        self._delegate = CapturingSerializer()

    def entry(self, key: str, value_writer: Callable[[ShapeSerializer], None]):
        header_name = self._prefix + key
        if header_name.lower() in self._header_names:
            return
        value_writer(self._delegate)
        assert self._delegate.result is not None  # noqa: S101
        self._headers.append((header_name, self._delegate.result))


class CapturingSerializer(SpecificShapeSerializer):
    """Directly passes along a string through a serializer."""

    result: str | None
    """The captured string.

    This will only be set after the serializer has been used.
    """

    def __init__(self) -> None:
        self.result = None

    def write_string(self, schema: Schema, value: str) -> None:
        self.result = value


class HTTPQuerySerializer(SpecificShapeSerializer):
    """Binds properties of a serializable shape to HTTP URI query params."""

    def __init__(
        self,
        key: str | None = None,
        params: list[tuple[str, str]] | None = None,
        *,
        query_param_exclusions: frozenset[str] = frozenset(),
        timestamp_format: TimestampFormat | None = None,
    ) -> None:
        """Initialize an HTTPQuerySerializer.

        :param key: An optional key to specifically write. If not set, the
            :py:class:`HTTPQueryTrait` will be checked instead. Required when
            collecting list or map entries.
        :param params: An optional list of query tuples to append to. If not
            set, one will be created.
        :param query_param_exclusions: Query names that map entries cannot override.
        :param timestamp_format: A fixed timestamp format for list entries.
        """
        self.query_params: list[tuple[str, str]] = params if params is not None else []
        self._key = key
        self._member_metadata: HTTPMemberBindingMetadata | None = None
        self._query_param_exclusions = query_param_exclusions
        self._timestamp_format = timestamp_format

    def set_member_metadata(self, metadata: HTTPMemberBindingMetadata) -> None:
        """Set the cached plan for the next top-level member write."""
        self._member_metadata = metadata

    def _key_for(self, schema: Schema) -> str:
        if self._key is not None:
            return self._key
        if (metadata := self._member_metadata) is not None:
            if metadata.request_wire_name is not None:
                return metadata.request_wire_name
        return schema.expect_trait(HTTPQueryTrait).key

    def _timestamp_format_for(self, schema: Schema) -> TimestampFormat:
        if self._timestamp_format is not None:
            return self._timestamp_format
        if (metadata := self._member_metadata) is not None:
            if metadata.request_timestamp_format is not None:
                return metadata.request_timestamp_format
        if (trait := schema.get_trait(TimestampFormatTrait)) is not None:
            return trait.format
        return TimestampFormat.DATE_TIME

    @contextmanager
    def begin_list(self, schema: Schema, size: int) -> Iterator[ShapeSerializer]:
        metadata = self._member_metadata
        yield HTTPQuerySerializer(
            key=self._key_for(schema),
            params=self.query_params,
            timestamp_format=(
                metadata.request_timestamp_format if metadata is not None else None
            ),
        )

    @contextmanager
    def begin_map(self, schema: Schema, size: int) -> Iterator[MapSerializer]:
        yield HTTPQueryMapSerializer(
            self.query_params,
            query_param_exclusions=self._query_param_exclusions,
        )

    def write_boolean(self, schema: Schema, value: bool) -> None:
        self.query_params.append((self._key_for(schema), "true" if value else "false"))

    def write_byte(self, schema: Schema, value: int) -> None:
        self.write_integer(schema, value)

    def write_short(self, schema: Schema, value: int) -> None:
        self.write_integer(schema, value)

    def write_integer(self, schema: Schema, value: int) -> None:
        self.query_params.append((self._key_for(schema), str(value)))

    def write_long(self, schema: Schema, value: int) -> None:
        self.write_integer(schema, value)

    def write_big_integer(self, schema: Schema, value: int) -> None:
        self.write_integer(schema, value)

    def write_float(self, schema: Schema, value: float) -> None:
        self.query_params.append((self._key_for(schema), serialize_float(value)))

    def write_double(self, schema: Schema, value: float) -> None:
        self.write_float(schema, value)

    def write_big_decimal(self, schema: Schema, value: Decimal) -> None:
        self.query_params.append((self._key_for(schema), serialize_float(value)))

    def write_string(self, schema: Schema, value: str) -> None:
        self.query_params.append((self._key_for(schema), value))

    def write_timestamp(self, schema: Schema, value: datetime) -> None:
        self.query_params.append(
            (
                self._key_for(schema),
                str(self._timestamp_format_for(schema).serialize(value)),
            )
        )


class HTTPPathSerializer(SpecificShapeSerializer):
    """Binds properties of a serializable shape to the HTTP URI path."""

    def __init__(
        self,
        path_pattern: PathPattern,
        *,
        greedy_label_names: frozenset[str] | None = None,
    ) -> None:
        """Initialize an HTTPPathSerializer.

        :param path_pattern: The pattern to bind properties to. This is also used to
            detect greedy labels, which have different escaping requirements.
        :param greedy_label_names: Cached names of greedy labels.
        """
        self._path_pattern = path_pattern
        self._member_metadata: HTTPMemberBindingMetadata | None = None
        self._greedy_label_names = (
            greedy_label_names
            if greedy_label_names is not None
            else frozenset(path_pattern.greedy_labels)
        )
        self._path_params: dict[str, str] = {}

    def set_member_metadata(self, metadata: HTTPMemberBindingMetadata) -> None:
        """Set the cached plan for the next top-level member write."""
        self._member_metadata = metadata

    def _name_for(self, schema: Schema) -> str:
        if (metadata := self._member_metadata) is not None:
            if metadata.request_wire_name is not None:
                return metadata.request_wire_name
        return schema.expect_member_name()

    def _timestamp_format_for(self, schema: Schema) -> TimestampFormat:
        if (metadata := self._member_metadata) is not None:
            if metadata.request_timestamp_format is not None:
                return metadata.request_timestamp_format
        if (trait := schema.get_trait(TimestampFormatTrait)) is not None:
            return trait.format
        return TimestampFormat.DATE_TIME

    @property
    def path(self) -> str:
        """Get the formatted path.

        This must not be accessed before serialization is complete, otherwise an
        exception will be raised.
        """
        return self._path_pattern.format(**self._path_params)

    def write_boolean(self, schema: Schema, value: bool) -> None:
        self._path_params[self._name_for(schema)] = "true" if value else "false"

    def write_byte(self, schema: Schema, value: int) -> None:
        self.write_integer(schema, value)

    def write_short(self, schema: Schema, value: int) -> None:
        self.write_integer(schema, value)

    def write_integer(self, schema: Schema, value: int) -> None:
        self._path_params[self._name_for(schema)] = str(value)

    def write_long(self, schema: Schema, value: int) -> None:
        self.write_integer(schema, value)

    def write_big_integer(self, schema: Schema, value: int) -> None:
        self.write_integer(schema, value)

    def write_float(self, schema: Schema, value: float) -> None:
        self._path_params[self._name_for(schema)] = serialize_float(value)

    def write_double(self, schema: Schema, value: float) -> None:
        self.write_float(schema, value)

    def write_big_decimal(self, schema: Schema, value: Decimal) -> None:
        self._path_params[self._name_for(schema)] = serialize_float(value)

    def write_string(self, schema: Schema, value: str) -> None:
        key = self._name_for(schema)
        if key in self._greedy_label_names:
            value = urlquote(value)
        else:
            value = urlquote(value, safe="")
        self._path_params[key] = value

    def write_timestamp(self, schema: Schema, value: datetime) -> None:
        self._path_params[self._name_for(schema)] = urlquote(
            str(self._timestamp_format_for(schema).serialize(value))
        )


class HTTPQueryMapSerializer(MapSerializer):
    """Binds properties of a serializable shape to a map of HTTP query params."""

    def __init__(
        self,
        query_params: list[tuple[str, str]],
        *,
        query_param_exclusions: frozenset[str] = frozenset(),
    ) -> None:
        """Initialize an HTTPQueryMapSerializer.

        :param query_params: The list of query param tuples to append to.
        :param query_param_exclusions: Query names that map entries cannot override.
        """
        self._query_params = query_params
        self._query_param_exclusions = query_param_exclusions

    def entry(self, key: str, value_writer: Callable[[ShapeSerializer], None]):
        if key in self._query_param_exclusions:
            return
        value_writer(HTTPQueryMapValueSerializer(key, self._query_params))


class HTTPQueryMapValueSerializer(SpecificShapeSerializer):
    def __init__(self, key: str, query_params: list[tuple[str, str]]) -> None:
        """Initialize an HTTPQueryMapValueSerializer.

        :param key: The key of the query parameter.
        :param query_params: The list of query param tuples to append to.
        """
        self._key = key
        self._query_params = query_params

    def write_string(self, schema: Schema, value: str) -> None:
        # Note: values are escaped when query params are joined
        self._query_params.append((self._key, value))

    @contextmanager
    def begin_list(self, schema: Schema, size: int) -> Iterator[ShapeSerializer]:
        yield self


class HostPrefixSerializer(SpecificShapeSerializer):
    """Binds properites of a serializable shape to the HTTP URI host.

    These properties are also bound to the payload.
    """

    def __init__(
        self,
        payload_serializer: ShapeSerializer,
        host_prefix_pattern: str,
    ) -> None:
        """Initialize a HostPrefixSerializer.

        :param host_prefix_pattern: The pattern to bind properties to.
        :param payload_serializer: The payload serializer to additionally write
            properties to.
        """
        self._prefix_params: dict[str, str] = {}
        self._host_prefix_pattern = host_prefix_pattern
        self._payload_serializer = payload_serializer
        self._member_metadata: HTTPMemberBindingMetadata | None = None

    def set_member_metadata(self, metadata: HTTPMemberBindingMetadata) -> None:
        """Set the cached plan for the next top-level member write."""
        self._member_metadata = metadata

    def _name_for(self, schema: Schema) -> str:
        if (
            self._member_metadata is not None
            and self._member_metadata.request_wire_name is not None
        ):
            return self._member_metadata.request_wire_name
        return schema.expect_member_name()

    @property
    def host_prefix(self) -> str:
        """The formatted host prefix.

        This must not be accessed before serialization is complete, otherwise an
        exception will be raised.
        """
        return self._host_prefix_pattern.format(**self._prefix_params)

    def write_string(self, schema: Schema, value: str) -> None:
        self._payload_serializer.write_string(schema, value)
        self._prefix_params[self._name_for(schema)] = urlquote(value, safe=".")


class HTTPResponseCodeSerializer(SpecificShapeSerializer):
    """Binds properties of a serializable shape to the HTTP response code."""

    response_code: int | None
    """The bound response code, or None if one hasn't been bound."""

    def __init__(self) -> None:
        """Initialize an HTTPResponseCodeSerializer."""
        self.response_code: int | None = None

    def write_byte(self, schema: Schema, value: int) -> None:
        self.response_code = value

    def write_short(self, schema: Schema, value: int) -> None:
        self.response_code = value

    def write_integer(self, schema: Schema, value: int) -> None:
        self.response_code = value
