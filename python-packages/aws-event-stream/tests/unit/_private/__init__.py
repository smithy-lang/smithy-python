# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import datetime
from dataclasses import dataclass
from typing import Any, ClassVar, Literal, Self

from smithy_core.deserializers import ShapeDeserializer
from smithy_core.exceptions import SmithyException
from smithy_core.prelude import (
    BLOB,
    BOOLEAN,
    BYTE,
    INTEGER,
    LONG,
    SHORT,
    STRING,
    TIMESTAMP,
)
from smithy_core.schemas import Schema
from smithy_core.serializers import ShapeSerializer
from smithy_core.shapes import ShapeID, ShapeType
from smithy_core.traits import Trait

from aws_event_stream.events import Byte, EventMessage, Long, Short

EVENT_HEADER_TRAIT = Trait(id=ShapeID("smithy.api#eventHeader"))
EVENT_PAYLOAD_TRAIT = Trait(id=ShapeID("smithy.api#eventPayload"))
ERROR_TRAIT = Trait(id=ShapeID("smithy.api#error"), value="client")
REQUIRED_TRAIT = Trait(id=ShapeID("smithy.api#required"))
STREAMING_TRAIT = Trait(id=ShapeID("smith.api#streaming"))


SCHEMA_MESSAGE_EVENT = Schema.collection(
    id=ShapeID("smithy.example#MessageEvent"),
    members={
        "boolHeader": {"index": 0, "target": BOOLEAN, "traits": [EVENT_HEADER_TRAIT]},
        "byteHeader": {"index": 1, "target": BYTE, "traits": [EVENT_HEADER_TRAIT]},
        "shortHeader": {"index": 2, "target": SHORT, "traits": [EVENT_HEADER_TRAIT]},
        "intHeader": {"index": 3, "target": INTEGER, "traits": [EVENT_HEADER_TRAIT]},
        "longHeader": {"index": 4, "target": LONG, "traits": [EVENT_HEADER_TRAIT]},
        "blobHeader": {"index": 5, "target": BLOB, "traits": [EVENT_HEADER_TRAIT]},
        "stringHeader": {"index": 6, "target": STRING, "traits": [EVENT_HEADER_TRAIT]},
        "timestampHeader": {
            "index": 7,
            "target": TIMESTAMP,
            "traits": [EVENT_HEADER_TRAIT],
        },
        "bodyMember": {"index": 8, "target": STRING},
    },
)

SCHEMA_PAYLOAD_EVENT = Schema.collection(
    id=ShapeID("smithy.example#PayloadEvent"),
    members={
        "header": {
            "index": 0,
            "target": STRING,
            "traits": [EVENT_HEADER_TRAIT, REQUIRED_TRAIT],
        },
        "payload": {
            "index": 1,
            "target": STRING,
            "traits": [EVENT_PAYLOAD_TRAIT, REQUIRED_TRAIT],
        },
    },
)

SCHEMA_BLOB_PAYLOAD_EVENT = Schema.collection(
    id=ShapeID("smithy.example#BlobPayloadEvent"),
    members={
        "header": {
            "index": 0,
            "target": STRING,
            "traits": [EVENT_HEADER_TRAIT, REQUIRED_TRAIT],
        },
        "payload": {
            "index": 1,
            "target": BLOB,
            "traits": [EVENT_PAYLOAD_TRAIT, REQUIRED_TRAIT],
        },
    },
)

SCHEMA_ERROR_EVENT = Schema.collection(
    id=ShapeID("smithy.example#ErrorEvent"),
    members={"message": {"index": 0, "target": STRING, "traits": [REQUIRED_TRAIT]}},
    traits=[ERROR_TRAIT],
)

SCHEMA_EVENT_STREAM = Schema.collection(
    id=ShapeID("smithy.example#EventStream"),
    shape_type=ShapeType.UNION,
    traits=[STREAMING_TRAIT],
    members={
        "message": {"index": 0, "target": SCHEMA_MESSAGE_EVENT},
        "payload": {"index": 1, "target": SCHEMA_PAYLOAD_EVENT},
        "blobPayload": {"index": 2, "target": SCHEMA_BLOB_PAYLOAD_EVENT},
        "error": {"index": 3, "target": SCHEMA_ERROR_EVENT},
    },
)

SCHEMA_INITIAL_MESSAGE = Schema.collection(
    id=ShapeID("smithy.example#EventStreamOperationInputOutput"),
    members={
        "message": {"index": 0, "target": STRING},
        # Event stream members will not be part of the operation input / output
        # shape schemas.
        # "stream": {
        #     "index": 1,
        #     "target": SCHEMA_EVENT_STREAM
        # },
    },
)


@dataclass
class MessageEvent:
    bool_header: bool | None = None
    byte_header: int | None = None
    short_header: int | None = None
    int_header: int | None = None
    long_header: int | None = None
    blob_header: bytes | None = None
    string_header: str | None = None
    timestamp_header: datetime.datetime | None = None
    body_member: str | None = None

    def serialize(self, serializer: ShapeSerializer):
        with serializer.begin_struct(SCHEMA_MESSAGE_EVENT) as s:
            self.serialize_members(s)

    def serialize_members(self, serializer: ShapeSerializer) -> None:
        if self.bool_header is not None:
            serializer.write_boolean(
                SCHEMA_MESSAGE_EVENT.members["boolHeader"], self.bool_header
            )

        if self.byte_header is not None:
            serializer.write_byte(
                SCHEMA_MESSAGE_EVENT.members["byteHeader"], self.byte_header
            )

        if self.short_header is not None:
            serializer.write_short(
                SCHEMA_MESSAGE_EVENT.members["shortHeader"], self.short_header
            )

        if self.int_header is not None:
            serializer.write_integer(
                SCHEMA_MESSAGE_EVENT.members["intHeader"], self.int_header
            )

        if self.long_header is not None:
            serializer.write_long(
                SCHEMA_MESSAGE_EVENT.members["longHeader"], self.long_header
            )

        if self.blob_header is not None:
            serializer.write_blob(
                SCHEMA_MESSAGE_EVENT.members["blobHeader"], self.blob_header
            )

        if self.string_header is not None:
            serializer.write_string(
                SCHEMA_MESSAGE_EVENT.members["stringHeader"], self.string_header
            )

        if self.timestamp_header is not None:
            serializer.write_timestamp(
                SCHEMA_MESSAGE_EVENT.members["timestampHeader"], self.timestamp_header
            )

        if self.body_member is not None:
            serializer.write_string(
                SCHEMA_MESSAGE_EVENT.members["bodyMember"], self.body_member
            )

    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> Self:
        kwargs: dict[str, Any] = {}

        def _consumer(schema: Schema, de: ShapeDeserializer) -> None:
            match schema.expect_member_index():
                case 0:
                    kwargs["bool_header"] = de.read_boolean(
                        SCHEMA_MESSAGE_EVENT.members["boolHeader"]
                    )

                case 1:
                    kwargs["byte_header"] = de.read_byte(
                        SCHEMA_MESSAGE_EVENT.members["byteHeader"]
                    )

                case 2:
                    kwargs["short_header"] = de.read_short(
                        SCHEMA_MESSAGE_EVENT.members["shortHeader"]
                    )

                case 3:
                    kwargs["int_header"] = de.read_integer(
                        SCHEMA_MESSAGE_EVENT.members["intHeader"]
                    )

                case 4:
                    kwargs["long_header"] = de.read_long(
                        SCHEMA_MESSAGE_EVENT.members["longHeader"]
                    )

                case 5:
                    kwargs["blob_header"] = de.read_blob(
                        SCHEMA_MESSAGE_EVENT.members["blobHeader"]
                    )

                case 6:
                    kwargs["string_header"] = de.read_string(
                        SCHEMA_MESSAGE_EVENT.members["stringHeader"]
                    )

                case 7:
                    kwargs["timestamp_header"] = de.read_timestamp(
                        SCHEMA_MESSAGE_EVENT.members["timestampHeader"]
                    )

                case 8:
                    kwargs["body_member"] = de.read_string(
                        SCHEMA_MESSAGE_EVENT.members["bodyMember"]
                    )

                case _:
                    raise SmithyException(f"Unexpected member schema: {schema}")

        deserializer.read_struct(schema=SCHEMA_MESSAGE_EVENT, consumer=_consumer)
        return cls(**kwargs)


@dataclass
class EventStreamMessageEvent:
    value: MessageEvent

    def serialize(self, serializer: ShapeSerializer):
        serializer.write_struct(SCHEMA_EVENT_STREAM, self)

    def serialize_members(self, serializer: ShapeSerializer):
        serializer.write_struct(SCHEMA_EVENT_STREAM.members["message"], self.value)


@dataclass
class PayloadEvent:
    header: str
    payload: str

    def serialize(self, serializer: ShapeSerializer):
        with serializer.begin_struct(SCHEMA_PAYLOAD_EVENT) as s:
            self.serialize_members(s)

    def serialize_members(self, serializer: ShapeSerializer) -> None:
        serializer.write_string(SCHEMA_PAYLOAD_EVENT.members["header"], self.header)
        serializer.write_string(SCHEMA_PAYLOAD_EVENT.members["payload"], self.payload)

    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> Self:
        kwargs: dict[str, Any] = {}

        def _consumer(schema: Schema, de: ShapeDeserializer) -> None:
            match schema.expect_member_index():
                case 0:
                    kwargs["header"] = de.read_string(
                        SCHEMA_PAYLOAD_EVENT.members["header"]
                    )
                case 1:
                    kwargs["payload"] = de.read_string(
                        SCHEMA_PAYLOAD_EVENT.members["payload"]
                    )
                case _:
                    raise SmithyException(f"Unexpected member schema: {schema}")

        deserializer.read_struct(schema=SCHEMA_PAYLOAD_EVENT, consumer=_consumer)
        return cls(**kwargs)


@dataclass
class EventStreamPayloadEvent:
    value: PayloadEvent

    def serialize(self, serializer: ShapeSerializer):
        serializer.write_struct(SCHEMA_EVENT_STREAM, self)

    def serialize_members(self, serializer: ShapeSerializer):
        serializer.write_struct(SCHEMA_EVENT_STREAM.members["payload"], self.value)


@dataclass
class BlobPayloadEvent:
    header: str
    payload: bytes

    def serialize(self, serializer: ShapeSerializer):
        with serializer.begin_struct(SCHEMA_BLOB_PAYLOAD_EVENT) as s:
            self.serialize_members(s)

    def serialize_members(self, serializer: ShapeSerializer) -> None:
        serializer.write_string(
            SCHEMA_BLOB_PAYLOAD_EVENT.members["header"], self.header
        )
        serializer.write_blob(
            SCHEMA_BLOB_PAYLOAD_EVENT.members["payload"], self.payload
        )

    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> Self:
        kwargs: dict[str, Any] = {}

        def _consumer(schema: Schema, de: ShapeDeserializer) -> None:
            match schema.expect_member_index():
                case 0:
                    kwargs["header"] = de.read_string(
                        SCHEMA_BLOB_PAYLOAD_EVENT.members["header"]
                    )
                case 1:
                    kwargs["payload"] = de.read_blob(
                        SCHEMA_BLOB_PAYLOAD_EVENT.members["payload"]
                    )
                case _:
                    raise SmithyException(f"Unexpected member schema: {schema}")

        deserializer.read_struct(schema=SCHEMA_BLOB_PAYLOAD_EVENT, consumer=_consumer)
        return cls(**kwargs)


@dataclass
class EventStreamBlobPayloadEvent:
    value: BlobPayloadEvent

    def serialize(self, serializer: ShapeSerializer):
        serializer.write_struct(SCHEMA_EVENT_STREAM, self)

    def serialize_members(self, serializer: ShapeSerializer):
        serializer.write_struct(
            SCHEMA_EVENT_STREAM.members["blobPayload"], self.value
        )


@dataclass
class ErrorEvent:
    code: ClassVar[str] = "NoSuchResource"
    fault: ClassVar[Literal["client", "server"]] = "client"

    message: str

    def serialize(self, serializer: ShapeSerializer):
        with serializer.begin_struct(SCHEMA_ERROR_EVENT) as s:
            self.serialize_members(s)

    def serialize_members(self, serializer: ShapeSerializer) -> None:
        serializer.write_string(SCHEMA_ERROR_EVENT.members["message"], self.message)

    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> Self:
        kwargs: dict[str, Any] = {}

        def _consumer(schema: Schema, de: ShapeDeserializer) -> None:
            match schema.expect_member_index():
                case 0:
                    kwargs["message"] = de.read_string(
                        SCHEMA_ERROR_EVENT.members["message"]
                    )
                case _:
                    raise SmithyException(f"Unexpected member schema: {schema}")

        deserializer.read_struct(schema=SCHEMA_ERROR_EVENT, consumer=_consumer)
        return cls(**kwargs)


@dataclass
class EventStreamErrorEvent:
    value: ErrorEvent

    def serialize(self, serializer: ShapeSerializer):
        serializer.write_struct(SCHEMA_EVENT_STREAM, self)

    def serialize_members(self, serializer: ShapeSerializer):
        serializer.write_struct(SCHEMA_EVENT_STREAM.members["error"], self.value)


@dataclass
class EventStreamUnknownEvent:
    tag: str

    def serialize(self, serializer: ShapeSerializer):
        raise SmithyException("Unknown union variants may not be serialized.")

    def serialize_members(self, serializer: ShapeSerializer):
        raise SmithyException("Unknown union variants may not be serialized.")


type EventStream = EventStreamMessageEvent | EventStreamPayloadEvent | EventStreamBlobPayloadEvent | EventStreamErrorEvent | EventStreamUnknownEvent


class EventStreamDeserializer:
    _result: EventStream | None = None

    def deserialize(self, deserializer: ShapeDeserializer) -> EventStream:
        self._result = None
        deserializer.read_struct(SCHEMA_EVENT_STREAM, self._consumer)

        if self._result is None:
            raise SmithyException("Unions must have exactly one value, but found none.")

        return self._result

    def _consumer(self, schema: Schema, de: ShapeDeserializer) -> None:
        match schema.expect_member_index():
            case 0:
                self._set_result(EventStreamMessageEvent(MessageEvent.deserialize(de)))

            case 1:
                self._set_result(EventStreamPayloadEvent(PayloadEvent.deserialize(de)))

            case 2:
                self._set_result(
                    EventStreamBlobPayloadEvent(BlobPayloadEvent.deserialize(de))
                )

            case 3:
                self._set_result(EventStreamErrorEvent(ErrorEvent.deserialize(de)))

            case _:
                raise SmithyException(f"Unexpected member schema: {schema}")

    def _set_result(self, value: EventStream) -> None:
        if self._result is not None:
            raise SmithyException(
                "Unions must have exactly one value, but found more than one."
            )
        self._result = value


@dataclass
class EventStreamOperationInputOutput:
    message: str

    def serialize(self, serializer: ShapeSerializer):
        with serializer.begin_struct(SCHEMA_INITIAL_MESSAGE) as s:
            self.serialize_members(s)

    def serialize_members(self, serializer: ShapeSerializer) -> None:
        serializer.write_string(SCHEMA_INITIAL_MESSAGE.members["message"], self.message)

    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> Self:
        kwargs: dict[str, Any] = {}

        def _consumer(schema: Schema, de: ShapeDeserializer) -> None:
            match schema.expect_member_index():
                case 0:
                    kwargs["message"] = de.read_string(
                        SCHEMA_INITIAL_MESSAGE.members["message"]
                    )
                case _:
                    raise SmithyException(f"Unexpected member schema: {schema}")

        deserializer.read_struct(schema=SCHEMA_INITIAL_MESSAGE, consumer=_consumer)
        return cls(**kwargs)


EVENT_STREAM_SERDE_CASES = [
    (
        EventStreamMessageEvent(MessageEvent(bool_header=True)),
        EventMessage(
            headers={
                ":message-type": "event",
                ":event-type": "message",
                "boolHeader": True,
                ":content-type": "application/json",
            },
            payload=b"{}",
        ),
    ),
    (
        EventStreamMessageEvent(MessageEvent(bool_header=False)),
        EventMessage(
            headers={
                ":message-type": "event",
                ":event-type": "message",
                "boolHeader": False,
                ":content-type": "application/json",
            },
            payload=b"{}",
        ),
    ),
    (
        EventStreamMessageEvent(MessageEvent(byte_header=1)),
        EventMessage(
            headers={
                ":message-type": "event",
                ":event-type": "message",
                "byteHeader": Byte(1),
                ":content-type": "application/json",
            },
            payload=b"{}",
        ),
    ),
    (
        EventStreamMessageEvent(MessageEvent(short_header=1)),
        EventMessage(
            headers={
                ":message-type": "event",
                ":event-type": "message",
                "shortHeader": Short(1),
                ":content-type": "application/json",
            },
            payload=b"{}",
        ),
    ),
    (
        EventStreamMessageEvent(MessageEvent(int_header=1)),
        EventMessage(
            headers={
                ":message-type": "event",
                ":event-type": "message",
                "intHeader": 1,
                ":content-type": "application/json",
            },
            payload=b"{}",
        ),
    ),
    (
        EventStreamMessageEvent(MessageEvent(long_header=1)),
        EventMessage(
            headers={
                ":message-type": "event",
                ":event-type": "message",
                "longHeader": Long(1),
                ":content-type": "application/json",
            },
            payload=b"{}",
        ),
    ),
    (
        EventStreamMessageEvent(MessageEvent(blob_header=b"blob")),
        EventMessage(
            headers={
                ":message-type": "event",
                ":event-type": "message",
                "blobHeader": b"blob",
                ":content-type": "application/json",
            },
            payload=b"{}",
        ),
    ),
    (
        EventStreamMessageEvent(MessageEvent(string_header="string")),
        EventMessage(
            headers={
                ":message-type": "event",
                ":event-type": "message",
                "stringHeader": "string",
                ":content-type": "application/json",
            },
            payload=b"{}",
        ),
    ),
    (
        EventStreamMessageEvent(
            MessageEvent(
                timestamp_header=datetime.datetime(
                    1970, 1, 1, 0, 0, 0, 8000, tzinfo=datetime.UTC
                )
            )
        ),
        EventMessage(
            headers={
                ":message-type": "event",
                ":event-type": "message",
                "timestampHeader": datetime.datetime(
                    1970, 1, 1, 0, 0, 0, 8000, tzinfo=datetime.UTC
                ),
                ":content-type": "application/json",
            },
            payload=b"{}",
        ),
    ),
    (
        EventStreamMessageEvent(MessageEvent(body_member="body")),
        EventMessage(
            headers={
                ":message-type": "event",
                ":event-type": "message",
                ":content-type": "application/json",
            },
            payload=b'{"bodyMember":"body"}',
        ),
    ),
    (
        EventStreamPayloadEvent(PayloadEvent(header="header", payload="payload")),
        EventMessage(
            headers={
                ":message-type": "event",
                ":event-type": "payload",
                "header": "header",
                ":content-type": "text/plain",
            },
            payload=b"payload",
        ),
    ),
    (
        EventStreamBlobPayloadEvent(
            BlobPayloadEvent(header="header", payload=b"\x07beep\x07")
        ),
        EventMessage(
            headers={
                ":message-type": "event",
                ":event-type": "blobPayload",
                "header": "header",
                ":content-type": "application/octet-stream",
            },
            payload=b"\x07beep\x07",
        ),
    ),
    (
        EventStreamErrorEvent(ErrorEvent(message="error message")),
        EventMessage(
            headers={
                ":message-type": "exception",
                ":exception-type": "error",
                ":content-type": "application/json",
            },
            payload=b'{"message":"error message"}',
        ),
    ),
]


INITIAL_REQUEST_CASE = (
    EventStreamOperationInputOutput(message="The initial request!"),
    EventMessage(
        headers={
            ":message-type": "event",
            ":event-type": "initial-request",
            ":content-type": "application/json",
        },
        payload=b'{"message":"The initial request!"}',
    ),
)


INITIAL_RESPONSE_CASE = (
    EventStreamOperationInputOutput(message="The initial response!"),
    EventMessage(
        headers={
            ":message-type": "event",
            ":event-type": "initial-response",
            ":content-type": "application/json",
        },
        payload=b'{"message":"The initial response!"}',
    ),
)
