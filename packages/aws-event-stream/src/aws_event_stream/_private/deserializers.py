# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import datetime
import logging
from collections.abc import Callable

from smithy_core.codecs import Codec
from smithy_core.deserializers import (
    ShapeDeserializer,
    SpecificShapeDeserializer,
)
from smithy_core.schemas import Schema
from smithy_core.shapes import ShapeType
from smithy_core.traits import EventHeaderTrait
from smithy_core.utils import expect_type

from ..events import HEADERS_DICT, Event
from ..exceptions import EventError, UnmodeledEventError
from . import (
    INITIAL_REQUEST_EVENT_TYPE,
    INITIAL_RESPONSE_EVENT_TYPE,
    get_payload_member,
)

logger = logging.getLogger(__name__)

INITIAL_MESSAGE_TYPES = (INITIAL_REQUEST_EVENT_TYPE, INITIAL_RESPONSE_EVENT_TYPE)


class EventDeserializer(SpecificShapeDeserializer):
    def __init__(
        self, event: Event, payload_codec: Codec, is_client_mode: bool = True
    ) -> None:
        self._event = event
        self._payload_codec = payload_codec
        self._is_client_mode = is_client_mode

    def read_struct(
        self,
        schema: Schema,
        consumer: Callable[[Schema, ShapeDeserializer], None],
    ) -> None:
        headers = self._event.message.headers

        match headers.get(":message-type"):
            case "event":
                member_name = expect_type(str, headers[":event-type"])
                if member_name in INITIAL_MESSAGE_TYPES:
                    # If it's an initial message, skip straight to deserialization.
                    message_deserializer = self._create_deserializer(schema, headers)
                    message_deserializer.read_struct(schema, consumer)
                else:
                    member_schema = schema.members[member_name]
                    message_deserializer = self._create_deserializer(
                        member_schema, headers
                    )
                    consumer(member_schema, message_deserializer)
            case "exception":
                member_name = expect_type(str, headers[":exception-type"])
                member_schema = schema.members[member_name]
                message_deserializer = self._create_deserializer(member_schema, headers)
                consumer(member_schema, message_deserializer)
            case "error":
                # The `application/vnd.amazon.eventstream` format allows for explicitly
                # unmodeled exceptions. These exceptions MUST have the `:error-code`
                # and `:error-message` headers set, and they MUST be strings.
                raise UnmodeledEventError(
                    expect_type(str, headers[":error-code"]),
                    expect_type(str, headers[":error-message"]),
                )
            case _:
                raise EventError(f"Unknown event structure: {self._event}")

    def _create_deserializer(
        self, schema: Schema, headers: HEADERS_DICT
    ) -> ShapeDeserializer:
        payload_member = get_payload_member(schema)
        payload_deserializer = self._create_payload_deserializer(payload_member)
        return EventMessageDeserializer(headers, payload_deserializer, payload_member)

    def _create_payload_deserializer(
        self, payload_member: Schema | None
    ) -> ShapeDeserializer | None:
        if not self._event.message.payload:
            return

        if payload_member is not None and payload_member.shape_type in (
            ShapeType.BLOB,
            ShapeType.STRING,
        ):
            return RawPayloadDeserializer(self._event.message.payload)

        return self._payload_codec.create_deserializer(self._event.message.payload)


class RawPayloadDeserializer(SpecificShapeDeserializer):
    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def read_string(self, schema: Schema) -> str:
        return self._payload.decode("utf-8")

    def read_blob(self, schema: Schema) -> bytes:
        return self._payload


class EventMessageDeserializer(SpecificShapeDeserializer):
    def __init__(
        self,
        headers: HEADERS_DICT,
        payload_deserializer: ShapeDeserializer | None,
        payload_member: Schema | None,
    ) -> None:
        self._headers = headers
        self._payload_deserializer = payload_deserializer
        self._payload_member = payload_member

    def read_struct(
        self,
        schema: Schema,
        consumer: Callable[[Schema, ShapeDeserializer], None],
    ) -> None:
        headers_deserializer = EventHeaderDeserializer(self._headers)
        for key in self._headers.keys():
            member_schema = schema.members.get(key)
            if member_schema is not None and EventHeaderTrait in member_schema:
                consumer(member_schema, headers_deserializer)

        if self._payload_deserializer:
            if self._payload_member is not None:
                consumer(self._payload_member, self._payload_deserializer)
            else:
                self._payload_deserializer.read_struct(schema, consumer)


class EventHeaderDeserializer(SpecificShapeDeserializer):
    def __init__(self, headers: HEADERS_DICT) -> None:
        self._headers = headers

    def read_boolean(self, schema: "Schema") -> bool:
        return expect_type(bool, self._headers[schema.expect_member_name()])

    def read_blob(self, schema: "Schema") -> bytes:
        return expect_type(bytes, self._headers[schema.expect_member_name()])

    def read_byte(self, schema: "Schema") -> int:
        return expect_type(int, self._headers[schema.expect_member_name()])

    def read_short(self, schema: "Schema") -> int:
        return expect_type(int, self._headers[schema.expect_member_name()])

    def read_integer(self, schema: "Schema") -> int:
        return expect_type(int, self._headers[schema.expect_member_name()])

    def read_long(self, schema: "Schema") -> int:
        return expect_type(int, self._headers[schema.expect_member_name()])

    def read_string(self, schema: "Schema") -> str:
        return expect_type(str, self._headers[schema.expect_member_name()])

    def read_timestamp(self, schema: "Schema") -> datetime.datetime:
        # TODO: do we support timestamp format here? One would assume not since the
        # format has a specific timestamp type.
        return expect_type(
            datetime.datetime, self._headers[schema.expect_member_name()]
        )
