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

from ..events import EventHeaderEncoder, EventMessage
from ..exceptions import InvalidHeaderValue
from .traits import ERROR_TRAIT, EVENT_HEADER_TRAIT, EVENT_PAYLOAD_TRAIT

_INITIAL_REQUEST_EVENT_TYPE = "initial-request"
_INITIAL_RESPONSE_EVENT_TYPE = "initial-response"


class EventSerializer(SpecificShapeSerializer):
    def __init__(
        self,
        payload_codec: Codec,
        is_client_mode: bool = True,
    ) -> None:
        self._payload_codec = payload_codec
        self._result: EventMessage | None = None
        if is_client_mode:
            self._initial_message_event_type = _INITIAL_REQUEST_EVENT_TYPE
        else:
            self._initial_message_event_type = _INITIAL_RESPONSE_EVENT_TYPE

    def get_result(self) -> EventMessage | None:
        return self._result

    @contextmanager
    def begin_struct(self, schema: "Schema") -> Iterator[ShapeSerializer]:
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

        if not self._has_payload_member(schema):
            with payload_serializer.begin_struct(schema) as body_serializer:
                yield EventStreamBindingSerializer(header_serializer, body_serializer)
        else:
            yield EventStreamBindingSerializer(header_serializer, payload_serializer)

        self._result = EventMessage(
            headers_bytes=headers_encoder.get_result(), payload=payload.getvalue()
        )

    def _has_payload_member(self, schema: "Schema") -> bool:
        for member in schema.members.values():
            if EVENT_PAYLOAD_TRAIT in member.traits:
                return True
        return False


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
        if EVENT_HEADER_TRAIT in schema.traits:
            return self._header_serializer
        return self._payload_serializer

    def after(self, schema: "Schema") -> None:
        pass
