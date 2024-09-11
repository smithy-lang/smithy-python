# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import datetime
from collections.abc import Iterator
from contextlib import contextmanager
from io import BytesIO
from typing import Never

from smithy_core.codecs import Codec
from smithy_core.schemas import Schema
from smithy_core.serializers import (
    InterceptingSerializer,
    ShapeSerializer,
    SpecificShapeSerializer,
)
from smithy_core.shapes import ShapeType
from smithy_core.utils import expect_type

from ..events import EventHeaderEncoder, EventMessage
from ..exceptions import InvalidHeaderValue
from . import INITIAL_REQUEST_EVENT_TYPE, INITIAL_RESPONSE_EVENT_TYPE
from .traits import (
    ERROR_TRAIT,
    EVENT_HEADER_TRAIT,
    EVENT_PAYLOAD_TRAIT,
    MEDIA_TYPE_TRAIT,
)

_DEFAULT_STRING_CONTENT_TYPE = "text/plain"
_DEFAULT_BLOB_CONTENT_TYPE = "application/octet-stream"


class EventSerializer(SpecificShapeSerializer):
    def __init__(
        self,
        payload_codec: Codec,
        is_client_mode: bool = True,
    ) -> None:
        self._payload_codec = payload_codec
        self._result: EventMessage | None = None
        if is_client_mode:
            self._initial_message_event_type = INITIAL_REQUEST_EVENT_TYPE
        else:
            self._initial_message_event_type = INITIAL_RESPONSE_EVENT_TYPE

    def get_result(self) -> EventMessage | None:
        return self._result

    @contextmanager
    def begin_struct(self, schema: "Schema") -> Iterator[ShapeSerializer]:
        # Event stream definitions are unions. Nothing about the union shape actually
        # matters for the purposes of event stream serialization though, we just care
        # about the specific member we're serializing. So here we yield immediately,
        # and the next time this method is called it'll be by the member that we
        # actually care about.
        #
        # Note that if we're serializing an operation input or output, it won't be a
        # union at all, so this won't get triggered. Thankfully, that's what we want.
        if schema.shape_type is ShapeType.UNION:
            try:
                yield self
            finally:
                return

        headers_encoder = EventHeaderEncoder()

        if ERROR_TRAIT in schema.traits:
            headers_encoder.encode_string(":message-type", "exception")
            headers_encoder.encode_string(
                ":exception-type", schema.expect_member_name()
            )
        else:
            headers_encoder.encode_string(":message-type", "event")
            if schema.member_name is None:
                # If there's no member name, that must mean that the structure is
                # either an input or output structure, and so this represents the
                # initial message.
                headers_encoder.encode_string(
                    ":event-type", self._initial_message_event_type
                )
            else:
                headers_encoder.encode_string(":event-type", schema.member_name)

        payload = BytesIO()
        payload_serializer: ShapeSerializer = self._payload_codec.create_serializer(
            payload
        )
        header_serializer = EventHeaderSerializer(headers_encoder)

        media_type = self._payload_codec.media_type

        if (payload_member := self._get_payload_member(schema)) is not None:
            media_type = self._get_payload_media_type(payload_member, media_type)
            yield EventStreamBindingSerializer(header_serializer, payload_serializer)
        else:
            with payload_serializer.begin_struct(schema) as body_serializer:
                yield EventStreamBindingSerializer(header_serializer, body_serializer)

        payload_bytes = payload.getvalue()
        if payload_bytes:
            headers_encoder.encode_string(":content-type", media_type)

        self._result = EventMessage(
            headers_bytes=headers_encoder.get_result(), payload=payload_bytes
        )

    def _get_payload_member(self, schema: Schema) -> Schema | None:
        for member in schema.members.values():
            if EVENT_PAYLOAD_TRAIT in member.traits:
                return schema
        return None

    def _get_payload_media_type(self, schema: Schema, default: str) -> str:
        if (media_type := schema.traits.get(MEDIA_TYPE_TRAIT)) is not None:
            return expect_type(str, media_type.value)

        match schema.shape_type:
            case ShapeType.STRING:
                return _DEFAULT_STRING_CONTENT_TYPE
            case ShapeType.BLOB:
                return _DEFAULT_BLOB_CONTENT_TYPE
            case _:
                return default


class EventHeaderSerializer(SpecificShapeSerializer):

    def __init__(self, encoder: EventHeaderEncoder) -> None:
        self._encoder = encoder

    def _invalid_state(
        self, schema: "Schema | None" = None, message: str | None = None
    ) -> Never:
        if message is None:
            message = f"Invalid header value type: {schema}"
        raise InvalidHeaderValue(message)

    def write_boolean(self, schema: "Schema", value: bool) -> None:
        self._encoder.encode_boolean(schema.expect_member_name(), value)

    def write_byte(self, schema: "Schema", value: int) -> None:
        self._encoder.encode_byte(schema.expect_member_name(), value)

    def write_short(self, schema: "Schema", value: int) -> None:
        self._encoder.encode_short(schema.expect_member_name(), value)

    def write_integer(self, schema: "Schema", value: int) -> None:
        self._encoder.encode_integer(schema.expect_member_name(), value)

    def write_long(self, schema: "Schema", value: int) -> None:
        self._encoder.encode_long(schema.expect_member_name(), value)

    def write_string(self, schema: "Schema", value: str) -> None:
        self._encoder.encode_string(schema.expect_member_name(), value)

    def write_blob(self, schema: "Schema", value: bytes) -> None:
        self._encoder.encode_blob(schema.expect_member_name(), value)

    def write_timestamp(self, schema: "Schema", value: datetime.datetime) -> None:
        self._encoder.encode_timestamp(schema.expect_member_name(), value)


class EventStreamBindingSerializer(InterceptingSerializer):
    def __init__(
        self,
        header_serializer: EventHeaderSerializer,
        payload_serializer: ShapeSerializer,
    ) -> None:
        self._header_serializer = header_serializer
        self._payload_serializer = payload_serializer

    def before(self, schema: "Schema") -> ShapeSerializer:
        print(f"FOUND TRAITS: {schema.traits}")
        if EVENT_HEADER_TRAIT in schema.traits:
            return self._header_serializer
        return self._payload_serializer

    def after(self, schema: "Schema") -> None:
        pass
