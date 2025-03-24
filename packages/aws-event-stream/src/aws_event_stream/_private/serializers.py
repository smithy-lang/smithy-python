# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import datetime
import logging
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
from smithy_core.traits import ErrorTrait, EventHeaderTrait, MediaTypeTrait

from ..events import HEADER_VALUE, Byte, EventHeaderEncoder, EventMessage, Long, Short
from ..exceptions import InvalidHeaderValue
from . import (
    INITIAL_REQUEST_EVENT_TYPE,
    INITIAL_RESPONSE_EVENT_TYPE,
    get_payload_member,
)

logger = logging.getLogger(__name__)

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
        self.event_header_encoder_cls = EventHeaderEncoder

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

        headers: dict[str, HEADER_VALUE] = {}

        if ErrorTrait in schema:
            headers[":message-type"] = "exception"
            headers[":exception-type"] = schema.expect_member_name()
        else:
            headers[":message-type"] = "event"
            if schema.member_name is None:
                # If there's no member name, that must mean that the structure is
                # either an input or output structure, and so this represents the
                # initial message.
                headers[":event-type"] = self._initial_message_event_type
            else:
                headers[":event-type"] = schema.member_name

        payload = BytesIO()
        payload_serializer: ShapeSerializer = self._payload_codec.create_serializer(
            payload
        )

        header_serializer = EventHeaderSerializer(headers)

        media_type = self._payload_codec.media_type

        if (payload_member := get_payload_member(schema)) is not None:
            media_type = self._get_payload_media_type(payload_member, media_type)
            if payload_member.shape_type in (ShapeType.BLOB, ShapeType.STRING):
                payload_serializer = RawPayloadSerializer(payload)
            yield EventStreamBindingSerializer(header_serializer, payload_serializer)
        else:
            with payload_serializer.begin_struct(schema) as body_serializer:
                yield EventStreamBindingSerializer(header_serializer, body_serializer)

        payload_bytes = payload.getvalue()
        if payload_bytes:
            headers[":content-type"] = media_type

        self._result = EventMessage(headers=headers, payload=payload_bytes)

    def _get_payload_media_type(self, schema: Schema, default: str) -> str:
        if (media_type := schema.get_trait(MediaTypeTrait)) is not None:
            return media_type.value

        match schema.shape_type:
            case ShapeType.STRING:
                return _DEFAULT_STRING_CONTENT_TYPE
            case ShapeType.BLOB:
                return _DEFAULT_BLOB_CONTENT_TYPE
            case _:
                return default


class EventHeaderSerializer(SpecificShapeSerializer):
    def __init__(self, headers: dict[str, HEADER_VALUE]) -> None:
        self._headers = headers

    def _invalid_state(
        self, schema: "Schema | None" = None, message: str | None = None
    ) -> Never:
        if message is None:
            message = f"Invalid header value type: {schema}"
        raise InvalidHeaderValue(message)

    def write_boolean(self, schema: "Schema", value: bool) -> None:
        self._headers[schema.expect_member_name()] = value

    def write_byte(self, schema: "Schema", value: int) -> None:
        self._headers[schema.expect_member_name()] = Byte(value)

    def write_short(self, schema: "Schema", value: int) -> None:
        self._headers[schema.expect_member_name()] = Short(value)

    def write_integer(self, schema: "Schema", value: int) -> None:
        self._headers[schema.expect_member_name()] = value

    def write_long(self, schema: "Schema", value: int) -> None:
        self._headers[schema.expect_member_name()] = Long(value)

    def write_string(self, schema: "Schema", value: str) -> None:
        self._headers[schema.expect_member_name()] = value

    def write_blob(self, schema: "Schema", value: bytes) -> None:
        self._headers[schema.expect_member_name()] = value

    def write_timestamp(self, schema: "Schema", value: datetime.datetime) -> None:
        self._headers[schema.expect_member_name()] = value


class RawPayloadSerializer(SpecificShapeSerializer):
    def __init__(self, payload: BytesIO) -> None:
        self._payload = payload

    def write_string(self, schema: "Schema", value: str) -> None:
        self._payload.write(value.encode("utf-8"))

    def write_blob(self, schema: "Schema", value: bytes) -> None:
        self._payload.write(value)


class EventStreamBindingSerializer(InterceptingSerializer):
    def __init__(
        self,
        header_serializer: EventHeaderSerializer,
        payload_struct_serializer: ShapeSerializer,
    ) -> None:
        self._header_serializer = header_serializer
        self._payload_struct_serializer = payload_struct_serializer

    def before(self, schema: "Schema") -> ShapeSerializer:
        if EventHeaderTrait in schema:
            return self._header_serializer
        return self._payload_struct_serializer

    def after(self, schema: "Schema") -> None:
        pass
