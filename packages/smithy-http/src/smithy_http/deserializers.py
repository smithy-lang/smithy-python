#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import datetime
from collections.abc import Callable
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from smithy_core.codecs import Codec
from smithy_core.deserializers import ShapeDeserializer, SpecificShapeDeserializer
from smithy_core.documents import TypeRegistry
from smithy_core.errors import CallException, ModeledException
from smithy_core.exceptions import (
    ExpectationNotMetException,
    UnsupportedStreamException,
)
from smithy_core.interfaces import TypedProperties, is_bytes_reader, is_streaming_blob
from smithy_core.prelude import DOCUMENT
from smithy_core.schemas import APIOperation, Schema
from smithy_core.shapes import ShapeType
from smithy_core.traits import (
    HTTPHeaderTrait,
    HTTPPayloadTrait,
    HTTPPrefixHeadersTrait,
    HTTPResponseCodeTrait,
    HTTPTrait,
    TimestampFormatTrait,
)
from smithy_core.types import TimestampFormat
from smithy_core.utils import ensure_utc, strict_parse_bool, strict_parse_float

from smithy_http.aio.interfaces import ErrorExtractor, HTTPResponse
from smithy_http.interfaces import Field, Fields

if TYPE_CHECKING:
    from smithy_core.aio.interfaces import StreamingBlob as AsyncStreamingBlob
    from smithy_core.interfaces import StreamingBlob as SyncStreamingBlob


__all__ = ["HTTPErrorDeserializer", "HTTPResponseDeserializer"]


class HTTPResponseDeserializer(SpecificShapeDeserializer):
    """Binds :py:class:`HTTPResponse` properties to a DeserializableShape."""

    # Note: caller will have to read the body if it's async and not streaming
    def __init__(
        self,
        payload_codec: Codec,
        http_trait: HTTPTrait,
        response: HTTPResponse,
        body: "SyncStreamingBlob | None" = None,
    ) -> None:
        """Initialize an HTTPResponseDeserializer.

        :param payload_codec: The Codec to use to deserialize the payload, if present.
        :param http_trait: The HTTP trait of the operation being handled.
        :param response: The HTTP response to read from.
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
        has_body = False
        payload_member: Schema | None = None

        for member in schema.members.values():
            if (trait := member.get_trait(HTTPHeaderTrait)) is not None:
                header = self._response.fields.entries.get(trait.key.lower())
                if header is not None:
                    if member.shape_type is ShapeType.LIST:
                        consumer(member, HTTPHeaderListDeserializer(header))
                    else:
                        consumer(member, HTTPHeaderDeserializer(header.as_string()))
            elif (trait := member.get_trait(HTTPPrefixHeadersTrait)) is not None:
                consumer(
                    member,
                    HTTPHeaderMapDeserializer(self._response.fields, trait.prefix),
                )
            elif HTTPPayloadTrait in member:
                has_body = True
                payload_member = member
            elif HTTPResponseCodeTrait in member:
                consumer(member, HTTPResponseCodeDeserializer(self._response.status))
            else:
                has_body = True

        if has_body:
            deserializer = self._create_payload_deserializer(payload_member)
            if payload_member is not None:
                consumer(payload_member, deserializer)
            else:
                deserializer.read_struct(schema, consumer)

    def _create_payload_deserializer(
        self, payload_member: Schema | None
    ) -> ShapeDeserializer:
        body = self._body if self._body is not None else self._response.body
        if payload_member is not None and payload_member.shape_type in (
            ShapeType.BLOB,
            ShapeType.STRING,
        ):
            return RawPayloadDeserializer(body)

        if not is_streaming_blob(body):
            raise UnsupportedStreamException(
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
        for value in self._field.values:
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
        return self._payload

    def _consume_payload(self) -> bytes:
        if isinstance(self._payload, bytes):
            return self._payload
        if isinstance(self._payload, bytearray):
            return bytes(self._payload)
        if is_bytes_reader(self._payload):
            return self._payload.read()
        raise UnsupportedStreamException(
            "Unable to read async stream. This stream must be buffered prior "
            "to creating the deserializer."
        )


class HTTPErrorDeserializer:
    """Binds an error response to a modelled or unknown exception."""

    def __init__(
        self,
        payload_codec: Codec,
        extractor: ErrorExtractor,
        response: HTTPResponse,
        body: "SyncStreamingBlob",
    ) -> None:
        """Initialize an HTTPErrorDeserializer.

        :param payload_codec: The Codec to use to deserialize the payload, if present.
        :param extractor: The error extractor to get error shape id from the response.
        :param response: The HTTP response to read from.
        :param body: The HTTP response body in a synchronously readable form. This is
            necessary for async response bodies when there is no streaming member.
        """
        self._payload_codec = payload_codec
        self._response = response
        self._body = body
        self._extractor = extractor
        self._codec = payload_codec

    def read_error(
        self,
        operation: APIOperation[Any, Any],
        error_registry: TypeRegistry,
        context: TypedProperties,
    ) -> CallException:
        body = self._body
        if isinstance(body, bytearray):
            body = bytes(body)
        deserializer = self._payload_codec.create_deserializer(body)
        document = deserializer.read_document(DOCUMENT)

        # try to get the error shape-id from the extractor
        error_id = self._extractor.get_error(self._response)

        # if none, get it from the parsed document (e.g. '__type')
        if error_id is None:
            error_id = document.discriminator

        if error_id is not None:
            error_shape = error_registry.get(error_id)
            # make sure the error shape is derived from modeled exception
            if not isinstance(error_shape, ModeledException):
                raise ExpectationNotMetException(
                    f"Modeled errors must be derived from 'ModeledException', but got {error_shape}"
                )

            # return the deserialized error
            return error_shape.deserialize(deserializer)

        # unknown error (no header, no type/unrecognized type)
        fault = "other"
        if 400 <= self._response.status < 500:
            fault = "client"
        elif self._response.status >= 500:
            fault = "server"
        message = (
            f"Unknown error: {operation.output_schema.id} "
            f"- code: {self._response.status} "
            f"- reason: {self._response.reason}"
        )

        return CallException(message=message, fault=fault)
