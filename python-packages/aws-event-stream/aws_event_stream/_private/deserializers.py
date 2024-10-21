# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import datetime
from collections.abc import Callable

from smithy_core.aio.interfaces import AsyncByteStream, AsyncCloseable
from smithy_core.codecs import Codec
from smithy_core.deserializers import (
    DeserializeableShape,
    ShapeDeserializer,
    SpecificShapeDeserializer,
)
from smithy_core.schemas import Schema
from smithy_core.utils import expect_type
from smithy_event_stream.aio.interfaces import AsyncEventReceiver

from ..events import HEADERS_DICT, Event
from ..exceptions import EventError, UnmodeledEventError
from . import INITIAL_REQUEST_EVENT_TYPE, INITIAL_RESPONSE_EVENT_TYPE
from .traits import EVENT_HEADER_TRAIT, EVENT_PAYLOAD_TRAIT

INITIAL_MESSAGE_TYPES = (INITIAL_REQUEST_EVENT_TYPE, INITIAL_RESPONSE_EVENT_TYPE)


class AWSAsyncEventReceiver[E: DeserializeableShape](AsyncEventReceiver[E]):
    def __init__(
        self,
        payload_codec: Codec,
        source: AsyncByteStream,
        deserializer: Callable[[ShapeDeserializer], E],
        is_client_mode: bool = True,
    ) -> None:
        self._payload_codec = payload_codec
        self._source = source
        self._is_client_mode = is_client_mode
        self._deserializer = deserializer

    async def receive(self) -> E | None:
        event = await Event.decode_async(self._source)
        deserializer = EventDeserializer(
            event=event,
            payload_codec=self._payload_codec,
            is_client_mode=self._is_client_mode,
        )
        return self._deserializer(deserializer)

    async def close(self) -> None:
        if isinstance(self._source, AsyncCloseable):
            await self._source.close()


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

        payload_deserializer = None
        if self._event.message.payload:
            payload_deserializer = self._payload_codec.create_deserializer(
                self._event.message.payload
            )

        message_deserializer = EventMessageDeserializer(headers, payload_deserializer)

        match headers.get(":message-type"):
            case "event":
                member_name = expect_type(str, headers[":event-type"])
                if member_name in INITIAL_MESSAGE_TYPES:
                    # If it's an initial message, skip straight to deserialization.
                    message_deserializer.read_struct(schema, consumer)
                else:
                    consumer(schema.members[member_name], message_deserializer)
            case "exception":
                member_name = expect_type(str, headers[":exception-type"])
                consumer(schema.members[member_name], message_deserializer)
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


class EventMessageDeserializer(SpecificShapeDeserializer):
    def __init__(
        self, headers: HEADERS_DICT, payload_deserializer: ShapeDeserializer | None
    ) -> None:
        self._headers = headers
        self._payload_deserializer = payload_deserializer

    def read_struct(
        self,
        schema: Schema,
        consumer: Callable[[Schema, ShapeDeserializer], None],
    ) -> None:
        headers_deserializer = EventHeaderDeserializer(self._headers)
        for key in self._headers.keys():
            member_schema = schema.members.get(key)
            if member_schema is not None and EVENT_HEADER_TRAIT in member_schema.traits:
                consumer(member_schema, headers_deserializer)

        if self._payload_deserializer:
            if (payload_member := self._get_payload_member(schema)) is not None:
                consumer(payload_member, self._payload_deserializer)
            else:
                self._payload_deserializer.read_struct(schema, consumer)

    def _get_payload_member(self, schema: "Schema") -> "Schema | None":
        for member in schema.members.values():
            if EVENT_PAYLOAD_TRAIT in member.traits:
                return member
        return None


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
