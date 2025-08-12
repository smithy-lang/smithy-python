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
    HTTPHeaderTrait,
    HTTPPrefixHeadersTrait,
    HTTPTrait,
    MediaTypeTrait,
    TimestampFormatTrait,
)
from smithy_core.types import TimestampFormat
from smithy_core.utils import ensure_utc, strict_parse_bool, strict_parse_float

from .aio.interfaces import HTTPResponse
from .bindings import Binding, ResponseBindingMatcher
from .interfaces import Field, Fields
from .utils import split_header

if TYPE_CHECKING:
    from smithy_core.aio.interfaces import StreamingBlob as AsyncStreamingBlob
    from smithy_core.interfaces import StreamingBlob as SyncStreamingBlob


__all__ = ["HTTPResponseDeserializer"]


class HTTPResponseDeserializer(SpecificShapeDeserializer):
    """Binds :py:class:`HTTPResponse` properties to a DeserializableShape."""

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
        binding_matcher = ResponseBindingMatcher(schema)

        for member in schema.members.values():
            match binding_matcher.match(member):
                case Binding.HEADER:
                    trait = member.expect_trait(HTTPHeaderTrait)
                    header = self._response.fields.entries.get(trait.key.lower())
                    if header is not None:
                        if member.shape_type is ShapeType.LIST:
                            consumer(member, HTTPHeaderListDeserializer(header))
                        else:
                            consumer(member, HTTPHeaderDeserializer(header.as_string()))
                case Binding.PREFIX_HEADERS:
                    trait = member.expect_trait(HTTPPrefixHeadersTrait)
                    consumer(
                        member,
                        HTTPHeaderMapDeserializer(self._response.fields, trait.prefix),
                    )
                case Binding.STATUS:
                    consumer(
                        member, HTTPResponseCodeDeserializer(self._response.status)
                    )
                case Binding.PAYLOAD:
                    if binding_matcher.event_stream_member is None:
                        assert binding_matcher.payload_member is not None  # noqa: S101
                        if self._should_read_payload(binding_matcher.payload_member):
                            deserializer = self._create_payload_deserializer(
                                binding_matcher.payload_member
                            )
                            consumer(binding_matcher.payload_member, deserializer)
                case _:
                    pass

        if binding_matcher.has_body and not self._has_empty_body(
            self._response, self._body
        ):
            deserializer = self._create_body_deserializer()
            deserializer.read_struct(schema, consumer)

    def _should_read_payload(self, schema: Schema) -> bool:
        if schema.shape_type not in (
            ShapeType.LIST,
            ShapeType.MAP,
            ShapeType.UNION,
            ShapeType.STRUCTURE,
        ):
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

    def _create_payload_deserializer(self, payload_member: Schema) -> ShapeDeserializer:
        if payload_member.shape_type in (
            ShapeType.BLOB,
            ShapeType.STRING,
            ShapeType.ENUM,
        ):
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

    def __init__(self, value: str) -> None:
        """Initialize an HTTPHeaderDeserializer.

        :param value: The string value of the header.
        """
        self._value = value

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
        if MediaTypeTrait in schema:
            return b64decode(self._value).decode("utf-8")
        return self._value

    def read_timestamp(self, schema: Schema) -> datetime.datetime:
        format = TimestampFormat.HTTP_DATE
        if (trait := schema.get_trait(TimestampFormatTrait)) is not None:
            format = trait.format
        return ensure_utc(format.deserialize(self._value))


class HTTPHeaderListDeserializer(SpecificShapeDeserializer):
    """Binds HTTP header lists to a deserializable shape."""

    def __init__(self, field: Field) -> None:
        """Initialize an HTTPHeaderListDeserializer.

        :param field: The field to deserialize.
        """
        self._field = field

    def read_list(
        self, schema: Schema, consumer: Callable[["ShapeDeserializer"], None]
    ) -> None:
        values = self._field.values
        if len(values) == 1:
            is_http_date_list = False
            value_schema = schema.members["member"]
            if value_schema.shape_type is ShapeType.TIMESTAMP:
                trait = value_schema.get_trait(TimestampFormatTrait)
                is_http_date_list = (
                    trait is None or trait.format is TimestampFormat.HTTP_DATE
                )
            values = split_header(values[0], is_http_date_list)
        for value in values:
            consumer(HTTPHeaderDeserializer(value))


class HTTPHeaderMapDeserializer(SpecificShapeDeserializer):
    """Binds HTTP header maps to a deserializable shape."""

    def __init__(self, fields: Fields, prefix: str = "") -> None:
        """Initialize an HTTPHeaderMapDeserializer.

        :param fields: The collection of headers to search for map values.
        :param prefix: An optional prefix to limit which headers are pulled in to the
            map. By default, all headers are pulled in, including headers that are bound
            to other properties on the shape.
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
            if field.name.lower().startswith(self._prefix):
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
