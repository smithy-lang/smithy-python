#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import datetime
from base64 import b64decode
from collections.abc import Callable
from decimal import Decimal
from inspect import iscoroutinefunction
from typing import TYPE_CHECKING, Any, TypeGuard

from smithy_core.aio.interfaces import AsyncByteStream
from smithy_core.aio.types import AsyncBytesReader
from smithy_core.codecs import Codec
from smithy_core.deserializers import ShapeDeserializer, SpecificShapeDeserializer
from smithy_core.exceptions import UnsupportedStreamError
from smithy_core.interfaces import is_bytes_reader, is_streaming_blob
from smithy_core.schemas import Schema
from smithy_core.shapes import ShapeType
from smithy_core.traits import (
    HTTPTrait,
    MediaTypeTrait,
    TimestampFormatTrait,
)
from smithy_core.types import TimestampFormat
from smithy_core.utils import ensure_utc, strict_parse_bool, strict_parse_float

from .aio.interfaces import HTTPResponse
from .bindings import Binding
from .interfaces import Field, Fields
from .schema_extensions import HTTP_BINDING_SCHEMA_EXTENSION, HTTPPayloadMetadata
from .utils import split_header

if TYPE_CHECKING:
    from smithy_core.aio.interfaces import StreamingBlob as AsyncStreamingBlob
    from smithy_core.interfaces import StreamingBlob as SyncStreamingBlob


__all__ = ["HTTPResponseDeserializer"]

_PREFIX_HEADER_OMISSIONS = frozenset(
    {
        "authorization",
        "connection",
        "content-length",
        "expect",
        "host",
        "max-forwards",
        "proxy-authenticate",
        "server",
        "te",
        "trailer",
        "transfer-encoding",
        "upgrade",
        "user-agent",
        "www-authenticate",
        "x-forwarded-for",
    }
)


def _discard_value(schema: Schema, deserializer: ShapeDeserializer) -> None:
    """Consume a value that belongs to a non-document HTTP binding."""
    if deserializer.is_null():
        deserializer.read_null()
        return

    match schema.shape_type:
        case ShapeType.STRUCTURE | ShapeType.UNION:
            deserializer.read_struct(schema, _discard_value)
        case ShapeType.LIST:
            value_schema = schema.members["member"]
            deserializer.read_list(
                schema,
                lambda value: _discard_value(value_schema, value),
            )
        case ShapeType.MAP:
            value_schema = schema.members["value"]
            deserializer.read_map(
                schema,
                lambda _, value: _discard_value(value_schema, value),
            )
        case ShapeType.BOOLEAN:
            deserializer.read_boolean(schema)
        case ShapeType.BLOB:
            deserializer.read_blob(schema)
        case ShapeType.BYTE:
            deserializer.read_byte(schema)
        case ShapeType.SHORT:
            deserializer.read_short(schema)
        case ShapeType.INTEGER | ShapeType.INT_ENUM:
            deserializer.read_integer(schema)
        case ShapeType.LONG:
            deserializer.read_long(schema)
        case ShapeType.BIG_INTEGER:
            deserializer.read_big_integer(schema)
        case ShapeType.FLOAT:
            deserializer.read_float(schema)
        case ShapeType.DOUBLE:
            deserializer.read_double(schema)
        case ShapeType.BIG_DECIMAL:
            deserializer.read_big_decimal(schema)
        case ShapeType.STRING | ShapeType.ENUM:
            deserializer.read_string(schema)
        case ShapeType.TIMESTAMP:
            deserializer.read_timestamp(schema)
        case ShapeType.DOCUMENT:
            deserializer.read_document(schema)
        case _:
            raise TypeError(f"Unsupported document member type: {schema.shape_type}")


class HTTPResponseDeserializer(SpecificShapeDeserializer):
    """Deserialize HTTP response bindings through the shape deserializer contract."""

    # Note: caller will have to read the body if it's async and not streaming
    def __init__(
        self,
        *,
        payload_codec: Codec,
        response: HTTPResponse,
        http_trait: HTTPTrait | None = None,
        body: "SyncStreamingBlob | None" = None,
    ) -> None:
        """Initialize an HTTPResponseDeserializer.

        :param payload_codec: The Codec to use to deserialize the payload, if present.
        :param response: The HTTP response to read from.
        :param http_trait: The HTTP trait of the operation being handled.
        :param body: The HTTP response body in a synchronously readable form. This is
            necessary for async response bodies when there is no streaming member.
        """
        self._payload_codec = payload_codec
        self._response = response
        self._http_trait = http_trait
        self._body = body

    def read_struct(
        self, schema: Schema, consumer: Callable[[Schema, ShapeDeserializer], None]
    ) -> None:
        binding_metadata = schema.get_extension(HTTP_BINDING_SCHEMA_EXTENSION)
        response_metadata = binding_metadata.response
        response = self._response
        fields = response.fields
        field_entries = fields.entries
        payload_metadata = response_metadata.payload
        event_stream_member = response_metadata.event_stream_member

        for (
            member,
            binding,
            name,
            is_list,
            timestamp_format,
            value_shape_type,
            has_media_type,
        ) in response_metadata.dispatch:
            match binding:
                case Binding.HEADER:
                    assert name is not None  # noqa: S101
                    header = field_entries.get(name)
                    if header is not None:
                        if is_list:
                            consumer(
                                member,
                                HTTPHeaderListDeserializer(
                                    header,
                                    timestamp_format,
                                    value_shape_type,
                                    has_media_type,
                                ),
                            )
                        else:
                            consumer(
                                member,
                                HTTPHeaderDeserializer(
                                    header.as_string(),
                                    timestamp_format,
                                    has_media_type,
                                ),
                            )
                case Binding.PREFIX_HEADERS:
                    assert name is not None  # noqa: S101
                    consumer(
                        member,
                        HTTPHeaderMapDeserializer(fields, name),
                    )
                case Binding.STATUS:
                    consumer(
                        member,
                        HTTPResponseCodeDeserializer(response.status),
                    )
                case Binding.PAYLOAD:
                    assert payload_metadata is not None  # noqa: S101
                    if event_stream_member is None and self._should_read_payload(
                        payload_metadata
                    ):
                        deserializer = self._create_payload_deserializer(
                            payload_metadata
                        )
                        consumer(member, deserializer)
                case _:
                    pass

        if response_metadata.has_body and not self._has_empty_body(
            response, self._body
        ):
            deserializer = self._create_body_deserializer()
            body_members = response_metadata.body_members

            def consume_body(
                member: Schema, member_deserializer: ShapeDeserializer
            ) -> None:
                if body_members[member.expect_member_index()]:
                    consumer(member, member_deserializer)
                else:
                    _discard_value(member, member_deserializer)

            deserializer.read_struct(schema, consume_body)

    def _should_read_payload(self, payload: HTTPPayloadMetadata) -> bool:
        if payload.is_raw:
            return True
        return not self._has_empty_body(self._response, self._body)

    def _has_empty_body(
        self, response: HTTPResponse, body: "SyncStreamingBlob | None"
    ) -> bool:
        if "content-length" in response.fields:
            return int(response.fields["content-length"].as_string()) == 0
        if isinstance(body, bytes | bytearray):
            return len(body) == 0
        if (seek := getattr(self._body, "seek", None)) is not None:
            content_length = seek(0, 2)
            if content_length == 0:
                return True
            seek(0, 0)
        return False

    def _create_payload_deserializer(
        self, payload: HTTPPayloadMetadata
    ) -> ShapeDeserializer:
        if payload.is_raw:
            body = self._body if self._body is not None else self._response.body
            return RawPayloadDeserializer(body)
        return self._create_body_deserializer()

    def _create_body_deserializer(self):
        body = self._body if self._body is not None else self._response.body
        if not is_streaming_blob(body):
            raise UnsupportedStreamError(
                "Unable to read async stream. This stream must be buffered prior "
                "to creating the deserializer."
            )

        if isinstance(body, bytearray):
            body = bytes(body)

        return self._payload_codec.create_deserializer(body)


class HTTPHeaderDeserializer(SpecificShapeDeserializer):
    """Binds HTTP header values to a deserializable shape.

    For headers with list values, see :py:class:`HTTPHeaderListDeserializer`.
    """

    def __init__(
        self,
        value: str,
        timestamp_format: TimestampFormat | None = None,
        has_media_type: bool | None = None,
    ) -> None:
        """Initialize an HTTPHeaderDeserializer.

        :param value: The string value of the header.
        """
        self._value = value
        self._timestamp_format = timestamp_format
        self._has_media_type = has_media_type

    def is_null(self) -> bool:
        return False

    def read_boolean(self, schema: Schema) -> bool:
        return strict_parse_bool(self._value)

    def read_byte(self, schema: Schema) -> int:
        return self.read_integer(schema)

    def read_short(self, schema: Schema) -> int:
        return self.read_integer(schema)

    def read_integer(self, schema: Schema) -> int:
        return int(self._value)

    def read_long(self, schema: Schema) -> int:
        return self.read_integer(schema)

    def read_big_integer(self, schema: Schema) -> int:
        return self.read_integer(schema)

    def read_float(self, schema: Schema) -> float:
        return strict_parse_float(self._value)

    def read_double(self, schema: Schema) -> float:
        return self.read_float(schema)

    def read_big_decimal(self, schema: Schema) -> Decimal:
        return Decimal(self._value).canonical()

    def read_string(self, schema: Schema) -> str:
        has_media_type = self._has_media_type
        if has_media_type is None:
            has_media_type = MediaTypeTrait in schema
        if has_media_type:
            return b64decode(self._value).decode("utf-8")
        return self._value

    def read_timestamp(self, schema: Schema) -> datetime.datetime:
        format = self._timestamp_format
        if format is None:
            format = TimestampFormat.HTTP_DATE
            if (trait := schema.get_trait(TimestampFormatTrait)) is not None:
                format = trait.format
        return ensure_utc(format.deserialize(self._value))


class HTTPHeaderListDeserializer(SpecificShapeDeserializer):
    """Binds HTTP header lists to a deserializable shape."""

    def __init__(
        self,
        field: Field,
        timestamp_format: TimestampFormat | None = None,
        value_shape_type: ShapeType | None = None,
        has_media_type: bool | None = None,
    ) -> None:
        """Initialize an HTTPHeaderListDeserializer.

        :param field: The field to deserialize.
        """
        self._field = field
        self._timestamp_format = timestamp_format
        self._value_shape_type = value_shape_type
        self._has_media_type = has_media_type

    def read_list(
        self, schema: Schema, consumer: Callable[["ShapeDeserializer"], None]
    ) -> None:
        values = self._field.values
        if len(values) == 1:
            value_shape_type = self._value_shape_type
            timestamp_format = self._timestamp_format
            if value_shape_type is None:
                value_schema = schema.members["member"]
                value_shape_type = value_schema.shape_type
                if (trait := value_schema.get_trait(TimestampFormatTrait)) is not None:
                    timestamp_format = trait.format
            is_http_date_list = (
                value_shape_type is ShapeType.TIMESTAMP
                and timestamp_format in (None, TimestampFormat.HTTP_DATE)
            )
            values = split_header(values[0], is_http_date_list)
        for value in values:
            consumer(
                HTTPHeaderDeserializer(
                    value,
                    self._timestamp_format,
                    self._has_media_type,
                )
            )


class HTTPHeaderMapDeserializer(SpecificShapeDeserializer):
    """Binds HTTP header maps to a deserializable shape."""

    def __init__(self, fields: Fields, prefix: str = "") -> None:
        """Initialize an HTTPHeaderMapDeserializer.

        :param fields: The collection of headers to search for map values.
        :param prefix: An optional prefix to limit which headers are pulled in to the
            map. By default, all non-restricted headers are pulled in, including headers
            that are bound to other properties on the shape.
        """
        self._prefix = prefix.lower()
        self._fields = fields

    def read_map(
        self,
        schema: Schema,
        consumer: Callable[[str, "ShapeDeserializer"], None],
    ) -> None:
        trim = len(self._prefix)
        for field in self._fields:
            name = field.name.lower()
            if name.startswith(self._prefix) and name not in _PREFIX_HEADER_OMISSIONS:
                consumer(field.name[trim:], HTTPHeaderDeserializer(field.as_string()))


class HTTPResponseCodeDeserializer(SpecificShapeDeserializer):
    """Binds HTTP response codes to a deserializeable shape."""

    def __init__(self, response_code: int) -> None:
        """Initialize an HTTPResponseCodeDeserializer.

        :param response_code: The response code to bind.
        """
        self._response_code = response_code

    def read_byte(self, schema: Schema) -> int:
        return self._response_code

    def read_short(self, schema: Schema) -> int:
        return self._response_code

    def read_integer(self, schema: Schema) -> int:
        return self._response_code


class RawPayloadDeserializer(SpecificShapeDeserializer):
    """Binds an HTTP payload to a deserializeable shape."""

    def __init__(self, payload: "AsyncStreamingBlob") -> None:
        """Initialize a RawPayloadDeserializer.

        :param payload: The payload to bind. If the member that is bound to the payload
            is a string or blob, it MUST NOT be an async stream. Async streams MUST be
            buffered into a synchronous stream ahead of time.
        """
        self._payload = payload

    def read_string(self, schema: Schema) -> str:
        return self._consume_payload().decode("utf-8")

    def read_blob(self, schema: Schema) -> bytes:
        return self._consume_payload()

    def read_data_stream(self, schema: Schema) -> "AsyncStreamingBlob":
        if self._is_async_reader(self._payload):
            return self._payload
        return AsyncBytesReader(self._payload)

    def _is_async_reader(self, obj: Any) -> TypeGuard[AsyncByteStream]:
        return isinstance(obj, AsyncByteStream) and iscoroutinefunction(
            getattr(obj, "read")
        )

    def _consume_payload(self) -> bytes:
        if isinstance(self._payload, bytes):
            return self._payload
        if isinstance(self._payload, bytearray):
            return bytes(self._payload)
        if is_bytes_reader(self._payload):
            return self._payload.read()
        raise UnsupportedStreamError(
            "Unable to read async stream. This stream must be buffered prior "
            "to creating the deserializer."
        )
