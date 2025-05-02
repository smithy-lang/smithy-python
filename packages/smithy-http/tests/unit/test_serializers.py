#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import datetime
from asyncio import iscoroutinefunction
from dataclasses import dataclass, field
from datetime import UTC
from decimal import Decimal
from io import BytesIO
from typing import Any, ClassVar, Protocol, Self

import pytest
from smithy_core import URI
from smithy_core.aio.interfaces import StreamingBlob
from smithy_core.aio.types import AsyncBytesReader
from smithy_core.deserializers import DeserializeableShape, ShapeDeserializer
from smithy_core.prelude import (
    BIG_DECIMAL,
    BLOB,
    BOOLEAN,
    FLOAT,
    INTEGER,
    STRING,
    TIMESTAMP,
)
from smithy_core.schemas import Schema
from smithy_core.serializers import SerializeableShape, ShapeSerializer
from smithy_core.shapes import ShapeID, ShapeType
from smithy_core.traits import (
    EndpointTrait,
    HostLabelTrait,
    HTTPHeaderTrait,
    HTTPLabelTrait,
    HTTPPayloadTrait,
    HTTPPrefixHeadersTrait,
    HTTPQueryParamsTrait,
    HTTPQueryTrait,
    HTTPResponseCodeTrait,
    HTTPTrait,
    StreamingTrait,
    TimestampFormatTrait,
    Trait,
)
from smithy_http import Field, Fields, tuples_to_fields
from smithy_http.aio import HTTPResponse as _HTTPResponse
from smithy_http.deserializers import HTTPResponseDeserializer
from smithy_http.serializers import HTTPRequestSerializer, HTTPResponseSerializer
from smithy_json import JSONCodec

# TODO: empty header prefix, query map

BOOLEAN_LIST = Schema.collection(
    id=ShapeID("com.smithy#BooleanList"),
    shape_type=ShapeType.LIST,
    members={"member": {"index": 0, "target": BOOLEAN}},
)
STRING_LIST = Schema.collection(
    id=ShapeID("com.smithy#StringList"),
    shape_type=ShapeType.LIST,
    members={"member": {"index": 0, "target": STRING}},
)
INTEGER_LIST = Schema.collection(
    id=ShapeID("com.smithy#IntegerList"),
    shape_type=ShapeType.LIST,
    members={"member": {"index": 0, "target": INTEGER}},
)
FLOAT_LIST = Schema.collection(
    id=ShapeID("com.smithy#FloatList"),
    shape_type=ShapeType.LIST,
    members={"member": {"index": 0, "target": FLOAT}},
)
BIG_DECIMAL_LIST = Schema.collection(
    id=ShapeID("com.smithy#BigDecimalList"),
    shape_type=ShapeType.LIST,
    members={"member": {"index": 0, "target": BIG_DECIMAL}},
)
BARE_TIMESTAMP_LIST = Schema.collection(
    id=ShapeID("com.smithy#BareTimestampList"),
    shape_type=ShapeType.LIST,
    members={"member": {"index": 0, "target": TIMESTAMP}},
)
HTTP_DATE_TIMESTAMP_LIST = Schema.collection(
    id=ShapeID("com.smithy#HttpDateTimestampList"),
    shape_type=ShapeType.LIST,
    members={
        "member": {
            "index": 0,
            "target": TIMESTAMP,
            "traits": [TimestampFormatTrait("http-date")],
        }
    },
)
DATE_TIME_TIMESTAMP_LIST = Schema.collection(
    id=ShapeID("com.smithy#DateTimeTimestampList"),
    shape_type=ShapeType.LIST,
    members={
        "member": {
            "index": 0,
            "target": TIMESTAMP,
            "traits": [TimestampFormatTrait("date-time")],
        }
    },
)
EPOCH_TIMESTAMP_LIST = Schema.collection(
    id=ShapeID("com.smithy#EpochTimestampList"),
    shape_type=ShapeType.LIST,
    members={
        "member": {
            "index": 0,
            "target": TIMESTAMP,
            "traits": [TimestampFormatTrait("epoch-seconds")],
        }
    },
)
STRING_MAP = Schema.collection(
    id=ShapeID("com.smithy#StringMap"),
    shape_type=ShapeType.MAP,
    members={
        "key": {"index": 0, "target": STRING},
        "value": {"index": 1, "target": STRING},
    },
)


@dataclass
class _HTTPMapping(Protocol):
    boolean_member: bool | None = None
    boolean_list_member: list[bool] = field(default_factory=list[bool])
    integer_member: int | None = None
    integer_list_member: list[int] = field(default_factory=list[int])
    float_member: float | None = None
    float_list_member: list[float] = field(default_factory=list[float])
    big_decimal_member: Decimal | None = None
    big_decimal_list_member: list[Decimal] = field(default_factory=list[Decimal])
    string_member: str | None = None
    string_list_member: list[str] = field(default_factory=list[str])
    default_timestamp_member: datetime.datetime | None = None
    http_date_timestamp_member: datetime.datetime | None = None
    http_date_list_timestamp_member: list[datetime.datetime] = field(
        default_factory=list[datetime.datetime]
    )
    date_time_timestamp_member: datetime.datetime | None = None
    date_time_list_timestamp_member: list[datetime.datetime] = field(
        default_factory=list[datetime.datetime]
    )
    epoch_timestamp_member: datetime.datetime | None = None
    epoch_list_timestamp_member: list[datetime.datetime] = field(
        default_factory=list[datetime.datetime]
    )
    string_map_member: dict[str, str] = field(default_factory=dict[str, str])

    ID: ClassVar[ShapeID]
    SCHEMA: ClassVar[Schema]

    def __init_subclass__(
        cls, id: ShapeID, trait: type[Trait], map_trait: Trait
    ) -> None:
        cls.ID = id
        cls.SCHEMA = Schema.collection(
            id=id,
            members={
                "boolean_member": {
                    "index": 0,
                    "target": BOOLEAN,
                    "traits": [trait("boolean")],
                },
                "boolean_list_member": {
                    "index": 1,
                    "target": BOOLEAN_LIST,
                    "traits": [trait("booleanList")],
                },
                "integer_member": {
                    "index": 2,
                    "target": INTEGER,
                    "traits": [trait("integer")],
                },
                "integer_list_member": {
                    "index": 3,
                    "target": INTEGER_LIST,
                    "traits": [trait("integerList")],
                },
                "float_member": {
                    "index": 4,
                    "target": FLOAT,
                    "traits": [trait("float")],
                },
                "float_list_member": {
                    "index": 5,
                    "target": FLOAT_LIST,
                    "traits": [trait("floatList")],
                },
                "big_decimal_member": {
                    "index": 6,
                    "target": BIG_DECIMAL,
                    "traits": [trait("bigDecimal")],
                },
                "big_decimal_list_member": {
                    "index": 7,
                    "target": BIG_DECIMAL_LIST,
                    "traits": [trait("bigDecimalList")],
                },
                "string_member": {
                    "index": 8,
                    "target": STRING,
                    "traits": [trait("string")],
                },
                "string_list_member": {
                    "index": 9,
                    "target": STRING_LIST,
                    "traits": [trait("stringList")],
                },
                "default_timestamp_member": {
                    "index": 10,
                    "target": TIMESTAMP,
                    "traits": [trait("defaultTimestamp")],
                },
                "http_date_timestamp_member": {
                    "index": 11,
                    "target": TIMESTAMP,
                    "traits": [
                        trait("httpDateTimestamp"),
                        TimestampFormatTrait("http-date"),
                    ],
                },
                "http_date_list_timestamp_member": {
                    "index": 12,
                    "target": HTTP_DATE_TIMESTAMP_LIST,
                    "traits": [trait("httpDateListTimestamp")],
                },
                "date_time_timestamp_member": {
                    "index": 13,
                    "target": TIMESTAMP,
                    "traits": [
                        trait("dateTimeTimestamp"),
                        TimestampFormatTrait("date-time"),
                    ],
                },
                "date_time_list_timestamp_member": {
                    "index": 14,
                    "target": DATE_TIME_TIMESTAMP_LIST,
                    "traits": [trait("dateTimeListTimestamp")],
                },
                "epoch_timestamp_member": {
                    "index": 15,
                    "target": TIMESTAMP,
                    "traits": [
                        trait("epochTimestamp"),
                        TimestampFormatTrait("epoch-seconds"),
                    ],
                },
                "epoch_list_timestamp_member": {
                    "index": 16,
                    "target": EPOCH_TIMESTAMP_LIST,
                    "traits": [trait("epochListTimestamp")],
                },
                "string_map_member": {
                    "index": 17,
                    "target": STRING_MAP,
                    "traits": [map_trait],
                },
            },
        )

    def serialize(self, serializer: ShapeSerializer) -> None:
        with serializer.begin_struct(self.SCHEMA) as s:
            self.serialize_members(s)

    def serialize_members(self, serializer: ShapeSerializer) -> None:
        if self.boolean_member is not None:
            serializer.write_boolean(
                self.SCHEMA.members["boolean_member"], self.boolean_member
            )
        if self.boolean_list_member:
            with serializer.begin_list(
                self.SCHEMA.members["boolean_list_member"],
                len(self.boolean_list_member),
            ) as ls:
                s = BOOLEAN_LIST.members["member"]
                for e in self.boolean_list_member:
                    ls.write_boolean(s, e)
        if self.integer_member is not None:
            serializer.write_integer(
                self.SCHEMA.members["integer_member"], self.integer_member
            )
        if self.integer_list_member:
            with serializer.begin_list(
                self.SCHEMA.members["integer_list_member"],
                len(self.integer_list_member),
            ) as ls:
                s = INTEGER_LIST.members["member"]
                for e in self.integer_list_member:
                    ls.write_integer(s, e)
        if self.float_member is not None:
            serializer.write_float(
                self.SCHEMA.members["float_member"], self.float_member
            )
        if self.float_list_member:
            with serializer.begin_list(
                self.SCHEMA.members["float_list_member"], len(self.float_list_member)
            ) as ls:
                s = FLOAT_LIST.members["member"]
                for e in self.float_list_member:
                    ls.write_float(s, e)
        if self.big_decimal_member is not None:
            serializer.write_big_decimal(
                self.SCHEMA.members["big_decimal_member"], self.big_decimal_member
            )
        if self.big_decimal_list_member:
            with serializer.begin_list(
                self.SCHEMA.members["big_decimal_list_member"],
                len(self.big_decimal_list_member),
            ) as ls:
                s = BIG_DECIMAL_LIST.members["member"]
                for e in self.big_decimal_list_member:
                    ls.write_big_decimal(s, e)
        if self.string_member is not None:
            serializer.write_string(
                self.SCHEMA.members["string_member"], self.string_member
            )
        if self.string_list_member:
            with serializer.begin_list(
                self.SCHEMA.members["string_list_member"], len(self.string_list_member)
            ) as ls:
                s = STRING_LIST.members["member"]
                for e in self.string_list_member:
                    ls.write_string(s, e)
        if self.default_timestamp_member is not None:
            serializer.write_timestamp(
                self.SCHEMA.members["default_timestamp_member"],
                self.default_timestamp_member,
            )
        if self.http_date_timestamp_member is not None:
            serializer.write_timestamp(
                self.SCHEMA.members["http_date_timestamp_member"],
                self.http_date_timestamp_member,
            )
        if self.http_date_list_timestamp_member:
            with serializer.begin_list(
                self.SCHEMA.members["http_date_list_timestamp_member"],
                len(self.http_date_list_timestamp_member),
            ) as ls:
                s = HTTP_DATE_TIMESTAMP_LIST.members["member"]
                for e in self.http_date_list_timestamp_member:
                    ls.write_timestamp(s, e)
        if self.date_time_timestamp_member is not None:
            serializer.write_timestamp(
                self.SCHEMA.members["date_time_timestamp_member"],
                self.date_time_timestamp_member,
            )
        if self.date_time_list_timestamp_member:
            with serializer.begin_list(
                self.SCHEMA.members["date_time_list_timestamp_member"],
                len(self.date_time_list_timestamp_member),
            ) as ls:
                s = DATE_TIME_TIMESTAMP_LIST.members["member"]
                for e in self.date_time_list_timestamp_member:
                    ls.write_timestamp(s, e)
        if self.epoch_timestamp_member is not None:
            serializer.write_timestamp(
                self.SCHEMA.members["epoch_timestamp_member"],
                self.epoch_timestamp_member,
            )
        if self.epoch_list_timestamp_member:
            with serializer.begin_list(
                self.SCHEMA.members["epoch_list_timestamp_member"],
                len(self.epoch_list_timestamp_member),
            ) as ls:
                s = EPOCH_TIMESTAMP_LIST.members["member"]
                for e in self.epoch_list_timestamp_member:
                    ls.write_timestamp(s, e)
        if self.string_map_member:
            with serializer.begin_map(
                self.SCHEMA.members["string_map_member"], len(self.string_map_member)
            ) as ms:
                s = STRING_MAP.members["value"]
                for k, v in self.string_map_member.items():
                    ms.entry(k, lambda vs: vs.write_string(s, v))

    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> Self:
        kwargs: dict[str, Any] = {}

        def _consumer(schema: Schema, de: ShapeDeserializer) -> None:
            match schema.expect_member_index():
                case 0:
                    kwargs["boolean_member"] = de.read_boolean(
                        cls.SCHEMA.members["boolean_member"]
                    )
                case 1:
                    list_value: list[Any] = []
                    de.read_list(
                        cls.SCHEMA.members["boolean_list_member"],
                        lambda d: list_value.append(d.read_boolean(BOOLEAN)),
                    )
                    kwargs["boolean_list_member"] = list_value
                case 2:
                    kwargs["integer_member"] = de.read_integer(
                        cls.SCHEMA.members["integer_member"]
                    )
                case 3:
                    list_value: list[Any] = []
                    de.read_list(
                        cls.SCHEMA.members["integer_list_member"],
                        lambda d: list_value.append(d.read_integer(INTEGER)),
                    )
                    kwargs["integer_list_member"] = list_value
                case 4:
                    kwargs["float_member"] = de.read_float(
                        cls.SCHEMA.members["float_member"]
                    )
                case 5:
                    list_value: list[Any] = []
                    de.read_list(
                        cls.SCHEMA.members["float_list_member"],
                        lambda d: list_value.append(d.read_float(FLOAT)),
                    )
                    kwargs["float_list_member"] = list_value
                case 6:
                    kwargs["big_decimal_member"] = de.read_big_decimal(
                        cls.SCHEMA.members["big_decimal_member"]
                    )
                case 7:
                    list_value: list[Any] = []
                    de.read_list(
                        cls.SCHEMA.members["big_decimal_list_member"],
                        lambda d: list_value.append(d.read_big_decimal(BIG_DECIMAL)),
                    )
                    kwargs["big_decimal_list_member"] = list_value
                case 8:
                    kwargs["string_member"] = de.read_string(
                        cls.SCHEMA.members["string_member"]
                    )
                case 9:
                    list_value: list[Any] = []
                    de.read_list(
                        cls.SCHEMA.members["string_list_member"],
                        lambda d: list_value.append(d.read_string(STRING)),
                    )
                    kwargs["string_list_member"] = list_value
                case 10:
                    kwargs["default_timestamp_member"] = de.read_timestamp(
                        cls.SCHEMA.members["default_timestamp_member"]
                    )
                case 11:
                    kwargs["http_date_timestamp_member"] = de.read_timestamp(
                        cls.SCHEMA.members["http_date_timestamp_member"]
                    )
                case 12:
                    list_value: list[Any] = []
                    de.read_list(
                        cls.SCHEMA.members["http_date_list_timestamp_member"],
                        lambda d: list_value.append(
                            d.read_timestamp(HTTP_DATE_TIMESTAMP_LIST.members["member"])
                        ),
                    )
                    kwargs["http_date_list_timestamp_member"] = list_value
                case 13:
                    kwargs["date_time_timestamp_member"] = de.read_timestamp(
                        cls.SCHEMA.members["date_time_timestamp_member"]
                    )
                case 14:
                    list_value: list[Any] = []
                    de.read_list(
                        cls.SCHEMA.members["date_time_list_timestamp_member"],
                        lambda d: list_value.append(
                            d.read_timestamp(DATE_TIME_TIMESTAMP_LIST.members["member"])
                        ),
                    )
                    kwargs["date_time_list_timestamp_member"] = list_value
                case 15:
                    kwargs["epoch_timestamp_member"] = de.read_timestamp(
                        cls.SCHEMA.members["epoch_timestamp_member"]
                    )
                case 16:
                    list_value: list[Any] = []
                    de.read_list(
                        cls.SCHEMA.members["epoch_list_timestamp_member"],
                        lambda d: list_value.append(
                            d.read_timestamp(EPOCH_TIMESTAMP_LIST.members["member"])
                        ),
                    )
                    kwargs["epoch_list_timestamp_member"] = list_value
                case 17:
                    map_value: dict[str, Any] = {}
                    de.read_map(
                        cls.SCHEMA.members["string_map_member"],
                        lambda k, d: map_value.__setitem__(k, d.read_string(STRING)),
                    )
                    kwargs["string_map_member"] = map_value
                case _:
                    raise Exception(f"Unexpected schema: {schema}")

        deserializer.read_struct(schema=cls.SCHEMA, consumer=_consumer)
        return cls(**kwargs)


@dataclass
class HTTPHeaders(
    _HTTPMapping,
    id=ShapeID("com.smithy#HttpHeaders"),
    trait=HTTPHeaderTrait,
    map_trait=HTTPPrefixHeadersTrait("x-"),
): ...


@dataclass
class HTTPEmptyPrefixHeaders(
    _HTTPMapping,
    id=ShapeID("com.smithy#HttpHeaders"),
    trait=HTTPHeaderTrait,
    map_trait=HTTPPrefixHeadersTrait(""),
): ...


@dataclass
class HTTPQuery(
    _HTTPMapping,
    id=ShapeID("com.smithy#HTTPQuery"),
    trait=HTTPQueryTrait,
    map_trait=HTTPQueryParamsTrait(),
): ...


@dataclass
class HTTPResponseCode:
    code: int = 200

    ID: ClassVar[ShapeID] = ShapeID("com.smithy#HTTPResponseCode")
    SCHEMA: ClassVar[Schema] = Schema.collection(
        id=ID,
        members={
            "code": {"index": 0, "target": INTEGER, "traits": [HTTPResponseCodeTrait()]}
        },
    )

    def serialize(self, serializer: ShapeSerializer) -> None:
        with serializer.begin_struct(self.SCHEMA) as s:
            self.serialize_members(s)

    def serialize_members(self, serializer: ShapeSerializer) -> None:
        serializer.write_integer(self.SCHEMA.members["code"], self.code)

    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> Self:
        kwargs: dict[str, Any] = {}

        def _consumer(schema: Schema, de: ShapeDeserializer) -> None:
            match schema.expect_member_index():
                case 0:
                    kwargs["code"] = de.read_integer(cls.SCHEMA.members["code"])
                case _:
                    raise Exception(f"Unexpected schema: {schema}")

        deserializer.read_struct(schema=cls.SCHEMA, consumer=_consumer)
        return cls(**kwargs)


@dataclass
class HTTPImplicitPayload:
    header: str | None = None
    payload_member: str | None = None

    ID: ClassVar[ShapeID] = ShapeID("com.smithy#HTTPImplicitPayload")
    SCHEMA: ClassVar[Schema] = Schema.collection(
        id=ID,
        members={
            "header": {
                "index": 0,
                "target": STRING,
                "traits": [HTTPHeaderTrait("header")],
            },
            "payload_member": {"index": 1, "target": STRING},
        },
    )

    def serialize(self, serializer: ShapeSerializer) -> None:
        with serializer.begin_struct(self.SCHEMA) as s:
            self.serialize_members(s)

    def serialize_members(self, serializer: ShapeSerializer) -> None:
        if self.header is not None:
            serializer.write_string(self.SCHEMA.members["header"], self.header)
        if self.payload_member is not None:
            serializer.write_string(
                self.SCHEMA.members["payload_member"], self.payload_member
            )

    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> Self:
        kwargs: dict[str, Any] = {}

        def _consumer(schema: Schema, de: ShapeDeserializer) -> None:
            match schema.expect_member_index():
                case 0:
                    kwargs["header"] = de.read_string(cls.SCHEMA.members["header"])
                case 1:
                    kwargs["payload_member"] = de.read_string(
                        cls.SCHEMA.members["payload_member"]
                    )
                case _:
                    raise Exception(f"Unexpected schema: {schema}")

        deserializer.read_struct(schema=cls.SCHEMA, consumer=_consumer)
        return cls(**kwargs)


@dataclass
class HTTPStringPayload:
    payload: str

    ID: ClassVar[ShapeID] = ShapeID("com.smithy#HTTPStringPayload")
    SCHEMA: ClassVar[Schema] = Schema.collection(
        id=ID,
        members={
            "payload": {"index": 0, "target": STRING, "traits": [HTTPPayloadTrait()]}
        },
    )

    def serialize(self, serializer: ShapeSerializer) -> None:
        with serializer.begin_struct(self.SCHEMA) as s:
            self.serialize_members(s)

    def serialize_members(self, serializer: ShapeSerializer) -> None:
        serializer.write_string(self.SCHEMA.members["payload"], self.payload)

    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> Self:
        kwargs: dict[str, Any] = {}

        def _consumer(schema: Schema, de: ShapeDeserializer) -> None:
            match schema.expect_member_index():
                case 0:
                    kwargs["payload"] = de.read_string(cls.SCHEMA.members["payload"])
                case _:
                    raise Exception(f"Unexpected schema: {schema}")

        deserializer.read_struct(schema=cls.SCHEMA, consumer=_consumer)
        return cls(**kwargs)


@dataclass
class HTTPBlobPayload:
    payload: bytes

    ID: ClassVar[ShapeID] = ShapeID("com.smithy#HTTPBlobPayload")
    SCHEMA: ClassVar[Schema] = Schema.collection(
        id=ID,
        members={
            "payload": {"index": 0, "target": BLOB, "traits": [HTTPPayloadTrait()]}
        },
    )

    def serialize(self, serializer: ShapeSerializer) -> None:
        with serializer.begin_struct(self.SCHEMA) as s:
            self.serialize_members(s)

    def serialize_members(self, serializer: ShapeSerializer) -> None:
        serializer.write_blob(self.SCHEMA.members["payload"], self.payload)

    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> Self:
        kwargs: dict[str, Any] = {}

        def _consumer(schema: Schema, de: ShapeDeserializer) -> None:
            match schema.expect_member_index():
                case 0:
                    kwargs["payload"] = de.read_blob(cls.SCHEMA.members["payload"])
                case _:
                    raise Exception(f"Unexpected schema: {schema}")

        deserializer.read_struct(schema=cls.SCHEMA, consumer=_consumer)
        return cls(**kwargs)


@dataclass
class HTTPStreamingPayload:
    payload: StreamingBlob

    ID: ClassVar[ShapeID] = ShapeID("com.smithy#HTTPStreamingPayload")
    SCHEMA: ClassVar[Schema] = Schema.collection(
        id=ID,
        members={
            "payload": {
                "index": 0,
                "target": BLOB,
                "traits": [HTTPPayloadTrait(), StreamingTrait()],
            }
        },
    )

    def serialize(self, serializer: ShapeSerializer) -> None:
        with serializer.begin_struct(self.SCHEMA) as s:
            self.serialize_members(s)

    def serialize_members(self, serializer: ShapeSerializer) -> None:
        serializer.write_data_stream(self.SCHEMA.members["payload"], self.payload)

    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> Self:
        kwargs: dict[str, Any] = {}

        def _consumer(schema: Schema, de: ShapeDeserializer) -> None:
            match schema.expect_member_index():
                case 0:
                    kwargs["payload"] = de.read_data_stream(
                        cls.SCHEMA.members["payload"]
                    )
                case _:
                    raise Exception(f"Unexpected schema: {schema}")

        deserializer.read_struct(schema=cls.SCHEMA, consumer=_consumer)
        return cls(**kwargs)


@dataclass
class HTTPStructuredPayload:
    payload: HTTPStringPayload

    ID: ClassVar[ShapeID] = ShapeID("com.smithy#HTTPStructuredPayload")
    SCHEMA: ClassVar[Schema] = Schema.collection(
        id=ID,
        members={
            "payload": {
                "index": 0,
                "target": HTTPStringPayload.SCHEMA,
                "traits": [HTTPPayloadTrait()],
            }
        },
    )

    def serialize(self, serializer: ShapeSerializer) -> None:
        with serializer.begin_struct(self.SCHEMA) as s:
            self.serialize_members(s)

    def serialize_members(self, serializer: ShapeSerializer) -> None:
        serializer.write_struct(self.SCHEMA.members["payload"], self.payload)

    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> Self:
        kwargs: dict[str, Any] = {}

        def _consumer(schema: Schema, de: ShapeDeserializer) -> None:
            match schema.expect_member_index():
                case 0:
                    kwargs["payload"] = HTTPStringPayload.deserialize(de)
                case _:
                    raise Exception(f"Unexpected schema: {schema}")

        deserializer.read_struct(schema=cls.SCHEMA, consumer=_consumer)
        return cls(**kwargs)


@dataclass
class HTTPStringLabel:
    label: str

    ID: ClassVar[ShapeID] = ShapeID("com.smithy#HTTPStringLabel")
    SCHEMA: ClassVar[Schema] = Schema.collection(
        id=ID,
        members={"label": {"index": 0, "target": STRING, "traits": [HTTPLabelTrait()]}},
    )

    def serialize(self, serializer: ShapeSerializer) -> None:
        with serializer.begin_struct(self.SCHEMA) as s:
            self.serialize_members(s)

    def serialize_members(self, serializer: ShapeSerializer) -> None:
        serializer.write_string(self.SCHEMA.members["label"], self.label)

    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> Self:
        kwargs: dict[str, Any] = {}

        def _consumer(schema: Schema, de: ShapeDeserializer) -> None:
            match schema.expect_member_index():
                case 0:
                    kwargs["label"] = de.read_string(cls.SCHEMA.members["label"])
                case _:
                    raise Exception(f"Unexpected schema: {schema}")

        deserializer.read_struct(schema=cls.SCHEMA, consumer=_consumer)
        return cls(**kwargs)


@dataclass
class HTTPIntegerLabel:
    label: int

    ID: ClassVar[ShapeID] = ShapeID("com.smithy#HTTPIntegerLabel")
    SCHEMA: ClassVar[Schema] = Schema.collection(
        id=ID,
        members={
            "label": {"index": 0, "target": INTEGER, "traits": [HTTPLabelTrait()]}
        },
    )

    def serialize(self, serializer: ShapeSerializer) -> None:
        with serializer.begin_struct(self.SCHEMA) as s:
            self.serialize_members(s)

    def serialize_members(self, serializer: ShapeSerializer) -> None:
        serializer.write_integer(self.SCHEMA.members["label"], self.label)

    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> Self:
        kwargs: dict[str, Any] = {}

        def _consumer(schema: Schema, de: ShapeDeserializer) -> None:
            match schema.expect_member_index():
                case 0:
                    kwargs["label"] = de.read_integer(cls.SCHEMA.members["label"])
                case _:
                    raise Exception(f"Unexpected schema: {schema}")

        deserializer.read_struct(schema=cls.SCHEMA, consumer=_consumer)
        return cls(**kwargs)


@dataclass
class HTTPFloatLabel:
    label: float

    ID: ClassVar[ShapeID] = ShapeID("com.smithy#HTTPFloatLabel")
    SCHEMA: ClassVar[Schema] = Schema.collection(
        id=ID,
        members={"label": {"index": 0, "target": FLOAT, "traits": [HTTPLabelTrait()]}},
    )

    def serialize(self, serializer: ShapeSerializer) -> None:
        with serializer.begin_struct(self.SCHEMA) as s:
            self.serialize_members(s)

    def serialize_members(self, serializer: ShapeSerializer) -> None:
        serializer.write_float(self.SCHEMA.members["label"], self.label)

    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> Self:
        kwargs: dict[str, Any] = {}

        def _consumer(schema: Schema, de: ShapeDeserializer) -> None:
            match schema.expect_member_index():
                case 0:
                    kwargs["label"] = de.read_float(cls.SCHEMA.members["label"])
                case _:
                    raise Exception(f"Unexpected schema: {schema}")

        deserializer.read_struct(schema=cls.SCHEMA, consumer=_consumer)
        return cls(**kwargs)


@dataclass
class HTTPBigDecimalLabel:
    label: Decimal

    ID: ClassVar[ShapeID] = ShapeID("com.smithy#HTTPBigDecimalLabel")
    SCHEMA: ClassVar[Schema] = Schema.collection(
        id=ID,
        members={
            "label": {"index": 0, "target": BIG_DECIMAL, "traits": [HTTPLabelTrait()]}
        },
    )

    def serialize(self, serializer: ShapeSerializer) -> None:
        with serializer.begin_struct(self.SCHEMA) as s:
            self.serialize_members(s)

    def serialize_members(self, serializer: ShapeSerializer) -> None:
        serializer.write_big_decimal(self.SCHEMA.members["label"], self.label)

    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> Self:
        kwargs: dict[str, Any] = {}

        def _consumer(schema: Schema, de: ShapeDeserializer) -> None:
            match schema.expect_member_index():
                case 0:
                    kwargs["label"] = de.read_big_decimal(cls.SCHEMA.members["label"])
                case _:
                    raise Exception(f"Unexpected schema: {schema}")

        deserializer.read_struct(schema=cls.SCHEMA, consumer=_consumer)
        return cls(**kwargs)


@dataclass
class HTTPBooleanLabel:
    label: bool

    ID: ClassVar[ShapeID] = ShapeID("com.smithy#HTTPBooleanLabel")
    SCHEMA: ClassVar[Schema] = Schema.collection(
        id=ID,
        members={
            "label": {"index": 0, "target": BOOLEAN, "traits": [HTTPLabelTrait()]}
        },
    )

    def serialize(self, serializer: ShapeSerializer) -> None:
        with serializer.begin_struct(self.SCHEMA) as s:
            self.serialize_members(s)

    def serialize_members(self, serializer: ShapeSerializer) -> None:
        serializer.write_boolean(self.SCHEMA.members["label"], self.label)

    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> Self:
        kwargs: dict[str, Any] = {}

        def _consumer(schema: Schema, de: ShapeDeserializer) -> None:
            match schema.expect_member_index():
                case 0:
                    kwargs["label"] = de.read_boolean(cls.SCHEMA.members["label"])
                case _:
                    raise Exception(f"Unexpected schema: {schema}")

        deserializer.read_struct(schema=cls.SCHEMA, consumer=_consumer)
        return cls(**kwargs)


@dataclass
class HTTPDefaultTimestampLabel:
    label: datetime.datetime

    ID: ClassVar[ShapeID] = ShapeID("com.smithy#HTTPDefaultTimestampLabel")
    SCHEMA: ClassVar[Schema] = Schema.collection(
        id=ID,
        members={
            "label": {"index": 0, "target": TIMESTAMP, "traits": [HTTPLabelTrait()]}
        },
    )

    def serialize(self, serializer: ShapeSerializer) -> None:
        with serializer.begin_struct(self.SCHEMA) as s:
            self.serialize_members(s)

    def serialize_members(self, serializer: ShapeSerializer) -> None:
        serializer.write_timestamp(self.SCHEMA.members["label"], self.label)

    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> Self:
        kwargs: dict[str, Any] = {}

        def _consumer(schema: Schema, de: ShapeDeserializer) -> None:
            match schema.expect_member_index():
                case 0:
                    kwargs["label"] = de.read_timestamp(cls.SCHEMA.members["label"])
                case _:
                    raise Exception(f"Unexpected schema: {schema}")

        deserializer.read_struct(schema=cls.SCHEMA, consumer=_consumer)
        return cls(**kwargs)


@dataclass
class HTTPEpochTimestampLabel:
    label: datetime.datetime

    ID: ClassVar[ShapeID] = ShapeID("com.smithy#HTTPEpochTimestampLabel")
    SCHEMA: ClassVar[Schema] = Schema.collection(
        id=ID,
        members={
            "label": {
                "index": 0,
                "target": TIMESTAMP,
                "traits": [HTTPLabelTrait(), TimestampFormatTrait("epoch-seconds")],
            }
        },
    )

    def serialize(self, serializer: ShapeSerializer) -> None:
        with serializer.begin_struct(self.SCHEMA) as s:
            self.serialize_members(s)

    def serialize_members(self, serializer: ShapeSerializer) -> None:
        serializer.write_timestamp(self.SCHEMA.members["label"], self.label)

    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> Self:
        kwargs: dict[str, Any] = {}

        def _consumer(schema: Schema, de: ShapeDeserializer) -> None:
            match schema.expect_member_index():
                case 0:
                    kwargs["label"] = de.read_timestamp(cls.SCHEMA.members["label"])
                case _:
                    raise Exception(f"Unexpected schema: {schema}")

        deserializer.read_struct(schema=cls.SCHEMA, consumer=_consumer)
        return cls(**kwargs)


@dataclass
class HTTPDateTimestampLabel:
    label: datetime.datetime

    ID: ClassVar[ShapeID] = ShapeID("com.smithy#HTTPDateTimestampLabel")
    SCHEMA: ClassVar[Schema] = Schema.collection(
        id=ID,
        members={
            "label": {
                "index": 0,
                "target": TIMESTAMP,
                "traits": [HTTPLabelTrait(), TimestampFormatTrait("http-date")],
            }
        },
    )

    def serialize(self, serializer: ShapeSerializer) -> None:
        with serializer.begin_struct(self.SCHEMA) as s:
            self.serialize_members(s)

    def serialize_members(self, serializer: ShapeSerializer) -> None:
        serializer.write_timestamp(self.SCHEMA.members["label"], self.label)

    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> Self:
        kwargs: dict[str, Any] = {}

        def _consumer(schema: Schema, de: ShapeDeserializer) -> None:
            match schema.expect_member_index():
                case 0:
                    kwargs["label"] = de.read_timestamp(cls.SCHEMA.members["label"])
                case _:
                    raise Exception(f"Unexpected schema: {schema}")

        deserializer.read_struct(schema=cls.SCHEMA, consumer=_consumer)
        return cls(**kwargs)


@dataclass
class HTTPDateTimeTimestampLabel:
    label: datetime.datetime

    ID: ClassVar[ShapeID] = ShapeID("com.smithy#HTTPDateTimeTimestampLabel")
    SCHEMA: ClassVar[Schema] = Schema.collection(
        id=ID,
        members={
            "label": {
                "index": 0,
                "target": TIMESTAMP,
                "traits": [HTTPLabelTrait(), TimestampFormatTrait("date-time")],
            }
        },
    )

    def serialize(self, serializer: ShapeSerializer) -> None:
        with serializer.begin_struct(self.SCHEMA) as s:
            self.serialize_members(s)

    def serialize_members(self, serializer: ShapeSerializer) -> None:
        serializer.write_timestamp(self.SCHEMA.members["label"], self.label)

    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> Self:
        kwargs: dict[str, Any] = {}

        def _consumer(schema: Schema, de: ShapeDeserializer) -> None:
            match schema.expect_member_index():
                case 0:
                    kwargs["label"] = de.read_timestamp(cls.SCHEMA.members["label"])
                case _:
                    raise Exception(f"Unexpected schema: {schema}")

        deserializer.read_struct(schema=cls.SCHEMA, consumer=_consumer)
        return cls(**kwargs)


@dataclass
class HostLabel:
    label: str

    ID: ClassVar[ShapeID] = ShapeID("com.smithy#HostLabel")
    SCHEMA: ClassVar[Schema] = Schema.collection(
        id=ID,
        members={
            "label": {
                "index": 0,
                "target": STRING,
                "traits": [HostLabelTrait()],
            }
        },
    )

    def serialize(self, serializer: ShapeSerializer) -> None:
        with serializer.begin_struct(self.SCHEMA) as s:
            self.serialize_members(s)

    def serialize_members(self, serializer: ShapeSerializer) -> None:
        serializer.write_string(self.SCHEMA.members["label"], self.label)

    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> Self:
        kwargs: dict[str, Any] = {}

        def _consumer(schema: Schema, de: ShapeDeserializer) -> None:
            match schema.expect_member_index():
                case 0:
                    kwargs["label"] = de.read_string(cls.SCHEMA.members["label"])
                case _:
                    raise Exception(f"Unexpected schema: {schema}")

        deserializer.read_struct(schema=cls.SCHEMA, consumer=_consumer)
        return cls(**kwargs)


@dataclass
class HTTPMessage:
    method: str = "POST"
    destination: URI = field(default_factory=lambda: URI(host="", path="/"))
    fields: Fields = field(default_factory=Fields)
    body: StreamingBlob = field(repr=False, default=b"")
    status: int = 200


class Shape(SerializeableShape, DeserializeableShape, Protocol): ...


@dataclass
class HTTPMessageTestCase:
    shape: Shape
    request: HTTPMessage
    http_trait: HTTPTrait = field(
        default_factory=lambda: HTTPTrait({"method": "POST", "code": 200, "uri": "/"})
    )
    endpoint_trait: EndpointTrait | None = None


# All of these test cases need to be created indirectly because they have mutable
# values and the individual cases are re-used. It would be possible to make a
# test generator in conftest.py that achieves a similar effect, but then you lose
# typing.
def header_cases() -> list[HTTPMessageTestCase]:
    return [
        HTTPMessageTestCase(
            HTTPHeaders(boolean_member=True),
            HTTPMessage(
                fields=tuples_to_fields([("boolean", "true")]),
            ),
        ),
        HTTPMessageTestCase(
            HTTPHeaders(boolean_list_member=[True, False]),
            HTTPMessage(
                fields=tuples_to_fields(
                    [("booleanList", "true"), ("booleanList", "false")]
                ),
            ),
        ),
        HTTPMessageTestCase(
            HTTPHeaders(integer_member=1),
            HTTPMessage(
                fields=tuples_to_fields([("integer", "1")]),
            ),
        ),
        HTTPMessageTestCase(
            HTTPHeaders(integer_list_member=[1, 2]),
            HTTPMessage(
                fields=tuples_to_fields([("integerList", "1"), ("integerList", "2")]),
            ),
        ),
        HTTPMessageTestCase(
            HTTPHeaders(float_member=1.1),
            HTTPMessage(
                fields=tuples_to_fields([("float", "1.1")]),
            ),
        ),
        HTTPMessageTestCase(
            HTTPHeaders(float_list_member=[1.1, 2.2]),
            HTTPMessage(
                fields=tuples_to_fields([("floatList", "1.1"), ("floatList", "2.2")]),
            ),
        ),
        HTTPMessageTestCase(
            HTTPHeaders(big_decimal_member=Decimal("1.1")),
            HTTPMessage(
                fields=tuples_to_fields([("bigDecimal", "1.1")]),
            ),
        ),
        HTTPMessageTestCase(
            HTTPHeaders(big_decimal_list_member=[Decimal("1.1"), Decimal("2.2")]),
            HTTPMessage(
                fields=tuples_to_fields(
                    [("bigDecimalList", "1.1"), ("bigDecimalList", "2.2")]
                ),
            ),
        ),
        HTTPMessageTestCase(
            HTTPHeaders(string_member="foo"),
            HTTPMessage(
                fields=tuples_to_fields([("string", "foo")]),
            ),
        ),
        HTTPMessageTestCase(
            HTTPHeaders(string_list_member=["spam", "eggs"]),
            HTTPMessage(
                fields=tuples_to_fields(
                    [("stringList", "spam"), ("stringList", "eggs")]
                ),
            ),
        ),
        HTTPMessageTestCase(
            HTTPHeaders(
                default_timestamp_member=datetime.datetime(2025, 1, 1, tzinfo=UTC)
            ),
            HTTPMessage(
                fields=tuples_to_fields(
                    [("defaultTimestamp", "Wed, 01 Jan 2025 00:00:00 GMT")]
                ),
            ),
        ),
        HTTPMessageTestCase(
            HTTPHeaders(
                http_date_timestamp_member=datetime.datetime(2025, 1, 1, tzinfo=UTC)
            ),
            HTTPMessage(
                fields=tuples_to_fields(
                    [("httpDateTimestamp", "Wed, 01 Jan 2025 00:00:00 GMT")]
                ),
            ),
        ),
        HTTPMessageTestCase(
            HTTPHeaders(
                http_date_list_timestamp_member=[
                    datetime.datetime(2025, 1, 1, tzinfo=UTC),
                    datetime.datetime(2024, 1, 1, tzinfo=UTC),
                ]
            ),
            HTTPMessage(
                fields=tuples_to_fields(
                    [
                        ("httpDateListTimestamp", "Wed, 01 Jan 2025 00:00:00 GMT"),
                        ("httpDateListTimestamp", "Mon, 01 Jan 2024 00:00:00 GMT"),
                    ]
                ),
            ),
        ),
        HTTPMessageTestCase(
            HTTPHeaders(
                date_time_timestamp_member=datetime.datetime(2025, 1, 1, tzinfo=UTC)
            ),
            HTTPMessage(
                fields=tuples_to_fields(
                    [("dateTimeTimestamp", "2025-01-01T00:00:00Z")]
                ),
            ),
        ),
        HTTPMessageTestCase(
            HTTPHeaders(
                date_time_list_timestamp_member=[
                    datetime.datetime(2025, 1, 1, tzinfo=UTC),
                    datetime.datetime(2024, 1, 1, tzinfo=UTC),
                ]
            ),
            HTTPMessage(
                fields=tuples_to_fields(
                    [
                        ("dateTimeListTimestamp", "2025-01-01T00:00:00Z"),
                        ("dateTimeListTimestamp", "2024-01-01T00:00:00Z"),
                    ]
                ),
            ),
        ),
        HTTPMessageTestCase(
            HTTPHeaders(
                epoch_timestamp_member=datetime.datetime(2025, 1, 1, tzinfo=UTC)
            ),
            HTTPMessage(
                fields=tuples_to_fields([("epochTimestamp", "1735689600")]),
            ),
        ),
        HTTPMessageTestCase(
            HTTPHeaders(
                epoch_list_timestamp_member=[
                    datetime.datetime(2025, 1, 1, tzinfo=UTC),
                    datetime.datetime(2024, 1, 1, tzinfo=UTC),
                ]
            ),
            HTTPMessage(
                fields=tuples_to_fields(
                    [
                        ("epochListTimestamp", "1735689600"),
                        ("epochListTimestamp", "1704067200"),
                    ]
                ),
            ),
        ),
        HTTPMessageTestCase(
            HTTPHeaders(string_map_member={"foo": "bar", "baz": "bam"}),
            HTTPMessage(
                fields=tuples_to_fields([("x-foo", "bar"), ("x-baz", "bam")]),
            ),
        ),
    ]


def empty_prefix_header_ser_cases() -> list[HTTPMessageTestCase]:
    return [
        HTTPMessageTestCase(
            HTTPEmptyPrefixHeaders(
                string_map_member={"foo": "bar", "baz": "bam", "string": "string"},
            ),
            HTTPMessage(
                fields=tuples_to_fields(
                    [("foo", "bar"), ("baz", "bam"), ("string", "string")]
                ),
            ),
        ),
    ]


def empty_prefix_header_deser_cases() -> list[HTTPMessageTestCase]:
    return [
        HTTPMessageTestCase(
            HTTPEmptyPrefixHeaders(
                string_member="string",
                string_map_member={"foo": "bar", "baz": "bam", "string": "string"},
            ),
            HTTPMessage(
                fields=tuples_to_fields(
                    [("foo", "bar"), ("baz", "bam"), ("string", "string")]
                ),
            ),
        ),
    ]


def query_cases() -> list[HTTPMessageTestCase]:
    return [
        HTTPMessageTestCase(
            HTTPQuery(boolean_member=True),
            HTTPMessage(
                destination=URI(host="", path="/", query="boolean=true"),
            ),
        ),
        HTTPMessageTestCase(
            HTTPQuery(boolean_list_member=[True, False]),
            HTTPMessage(
                destination=URI(
                    host="", path="/", query="booleanList=true&booleanList=false"
                ),
            ),
        ),
        HTTPMessageTestCase(
            HTTPQuery(integer_member=1),
            HTTPMessage(destination=URI(host="", path="/", query="integer=1")),
        ),
        HTTPMessageTestCase(
            HTTPQuery(integer_list_member=[1, 2]),
            HTTPMessage(
                destination=URI(host="", path="/", query="integerList=1&integerList=2")
            ),
        ),
        HTTPMessageTestCase(
            HTTPQuery(float_member=1.1),
            HTTPMessage(destination=URI(host="", path="/", query="float=1.1")),
        ),
        HTTPMessageTestCase(
            HTTPQuery(float_list_member=[1.1, 2.2]),
            HTTPMessage(
                destination=URI(host="", path="/", query="floatList=1.1&floatList=2.2")
            ),
        ),
        HTTPMessageTestCase(
            HTTPQuery(big_decimal_member=Decimal("1.1")),
            HTTPMessage(destination=URI(host="", path="/", query="bigDecimal=1.1")),
        ),
        HTTPMessageTestCase(
            HTTPQuery(big_decimal_list_member=[Decimal("1.1"), Decimal("2.2")]),
            HTTPMessage(
                destination=URI(
                    host="", path="/", query="bigDecimalList=1.1&bigDecimalList=2.2"
                )
            ),
        ),
        HTTPMessageTestCase(
            HTTPQuery(string_member="foo"),
            HTTPMessage(destination=URI(host="", path="/", query="string=foo")),
        ),
        HTTPMessageTestCase(
            HTTPQuery(string_list_member=["spam", "eggs"]),
            HTTPMessage(
                destination=URI(
                    host="", path="/", query="stringList=spam&stringList=eggs"
                )
            ),
        ),
        HTTPMessageTestCase(
            HTTPQuery(
                default_timestamp_member=datetime.datetime(2025, 1, 1, tzinfo=UTC)
            ),
            HTTPMessage(
                destination=URI(
                    host="",
                    path="/",
                    query="defaultTimestamp=2025-01-01T00%3A00%3A00Z",
                )
            ),
        ),
        HTTPMessageTestCase(
            HTTPQuery(
                http_date_timestamp_member=datetime.datetime(2025, 1, 1, tzinfo=UTC)
            ),
            HTTPMessage(
                destination=URI(
                    host="",
                    path="/",
                    query="httpDateTimestamp=Wed%2C%2001%20Jan%202025%2000%3A00%3A00%20GMT",
                )
            ),
        ),
        HTTPMessageTestCase(
            HTTPQuery(
                http_date_list_timestamp_member=[
                    datetime.datetime(2025, 1, 1, tzinfo=UTC),
                    datetime.datetime(2024, 1, 1, tzinfo=UTC),
                ]
            ),
            HTTPMessage(
                destination=URI(
                    host="",
                    path="/",
                    query=(
                        "httpDateListTimestamp=Wed%2C%2001%20Jan%202025%2000%3A00%3A00%20GMT"
                        "&httpDateListTimestamp=Mon%2C%2001%20Jan%202024%2000%3A00%3A00%20GMT"
                    ),
                )
            ),
        ),
        HTTPMessageTestCase(
            HTTPQuery(
                date_time_timestamp_member=datetime.datetime(2025, 1, 1, tzinfo=UTC)
            ),
            HTTPMessage(
                destination=URI(
                    host="",
                    path="/",
                    query="dateTimeTimestamp=2025-01-01T00%3A00%3A00Z",
                )
            ),
        ),
        HTTPMessageTestCase(
            HTTPQuery(
                date_time_list_timestamp_member=[
                    datetime.datetime(2025, 1, 1, tzinfo=UTC),
                    datetime.datetime(2024, 1, 1, tzinfo=UTC),
                ]
            ),
            HTTPMessage(
                destination=URI(
                    host="",
                    path="/",
                    query=(
                        "dateTimeListTimestamp=2025-01-01T00%3A00%3A00Z"
                        "&dateTimeListTimestamp=2024-01-01T00%3A00%3A00Z"
                    ),
                )
            ),
        ),
        HTTPMessageTestCase(
            HTTPQuery(epoch_timestamp_member=datetime.datetime(2025, 1, 1, tzinfo=UTC)),
            HTTPMessage(
                destination=URI(host="", path="/", query="epochTimestamp=1735689600")
            ),
        ),
        HTTPMessageTestCase(
            HTTPQuery(
                epoch_list_timestamp_member=[
                    datetime.datetime(2025, 1, 1, tzinfo=UTC),
                    datetime.datetime(2024, 1, 1, tzinfo=UTC),
                ]
            ),
            HTTPMessage(
                destination=URI(
                    host="",
                    path="/",
                    query="epochListTimestamp=1735689600&epochListTimestamp=1704067200",
                )
            ),
        ),
        HTTPMessageTestCase(
            HTTPQuery(string_map_member={"foo": "bar", "baz": "bam"}),
            HTTPMessage(destination=URI(host="", path="/", query="foo=bar&baz=bam")),
        ),
        HTTPMessageTestCase(
            HTTPQuery(string_member="foo"),
            HTTPMessage(
                destination=URI(host="", path="/", query="spam=eggs&string=foo")
            ),
            http_trait=HTTPTrait({"method": "POST", "code": 200, "uri": "/?spam=eggs"}),
        ),
        HTTPMessageTestCase(
            HTTPQuery(string_member="foo"),
            HTTPMessage(destination=URI(host="", path="/", query="spam&string=foo")),
            http_trait=HTTPTrait({"method": "POST", "code": 200, "uri": "/?spam"}),
        ),
    ]


def label_cases() -> list[HTTPMessageTestCase]:
    return [
        HTTPMessageTestCase(
            HTTPStringLabel(label="foo/bar"),
            HTTPMessage(destination=URI(host="", path="/foo%2Fbar")),
            http_trait=HTTPTrait({"method": "POST", "code": 200, "uri": "/{label}"}),
        ),
        HTTPMessageTestCase(
            HTTPStringLabel(label="foo/bar"),
            HTTPMessage(destination=URI(host="", path="/foo/bar")),
            http_trait=HTTPTrait({"method": "POST", "code": 200, "uri": "/{label+}"}),
        ),
        HTTPMessageTestCase(
            HTTPFloatLabel(label=1.1),
            HTTPMessage(destination=URI(host="", path="/1.1")),
            http_trait=HTTPTrait({"method": "POST", "code": 200, "uri": "/{label}"}),
        ),
        HTTPMessageTestCase(
            HTTPBigDecimalLabel(label=Decimal("1.1")),
            HTTPMessage(destination=URI(host="", path="/1.1")),
            http_trait=HTTPTrait({"method": "POST", "code": 200, "uri": "/{label}"}),
        ),
        HTTPMessageTestCase(
            HTTPBooleanLabel(label=True),
            HTTPMessage(destination=URI(host="", path="/true")),
            http_trait=HTTPTrait({"method": "POST", "code": 200, "uri": "/{label}"}),
        ),
        HTTPMessageTestCase(
            HTTPDefaultTimestampLabel(label=datetime.datetime(2025, 1, 1, tzinfo=UTC)),
            HTTPMessage(destination=URI(host="", path="/2025-01-01T00%3A00%3A00Z")),
            http_trait=HTTPTrait({"method": "POST", "code": 200, "uri": "/{label}"}),
        ),
        HTTPMessageTestCase(
            HTTPEpochTimestampLabel(label=datetime.datetime(2025, 1, 1, tzinfo=UTC)),
            HTTPMessage(destination=URI(host="", path="/1735689600")),
            http_trait=HTTPTrait({"method": "POST", "code": 200, "uri": "/{label}"}),
        ),
        HTTPMessageTestCase(
            HTTPDateTimeTimestampLabel(label=datetime.datetime(2025, 1, 1, tzinfo=UTC)),
            HTTPMessage(destination=URI(host="", path="/2025-01-01T00%3A00%3A00Z")),
            http_trait=HTTPTrait({"method": "POST", "code": 200, "uri": "/{label}"}),
        ),
        HTTPMessageTestCase(
            HTTPDateTimestampLabel(label=datetime.datetime(2025, 1, 1, tzinfo=UTC)),
            HTTPMessage(
                destination=URI(
                    host="", path="/Wed%2C%2001%20Jan%202025%2000%3A00%3A00%20GMT"
                )
            ),
            http_trait=HTTPTrait({"method": "POST", "code": 200, "uri": "/{label}"}),
        ),
    ]


def host_cases() -> list[HTTPMessageTestCase]:
    return [
        HTTPMessageTestCase(
            HostLabel("foo"),
            HTTPMessage(
                destination=URI(host="foo.", path="/"), body=BytesIO(b'{"label":"foo"}')
            ),
            endpoint_trait=EndpointTrait({"hostPrefix": "{label}."}),
        ),
        HTTPMessageTestCase(
            HTTPHeaders(),
            HTTPMessage(destination=URI(host="foo.", path="/")),
            endpoint_trait=EndpointTrait({"hostPrefix": "foo."}),
        ),
    ]


def payload_cases() -> list[HTTPMessageTestCase]:
    return [
        HTTPMessageTestCase(
            HTTPImplicitPayload(header="foo", payload_member="bar"),
            HTTPMessage(
                fields=tuples_to_fields([("header", "foo")]),
                body=BytesIO(b'{"payload_member":"bar"}'),
            ),
        ),
        HTTPMessageTestCase(
            HTTPStringPayload(payload="foo"),
            HTTPMessage(
                fields=tuples_to_fields([("content-type", "text/plain")]), body=b"foo"
            ),
        ),
        HTTPMessageTestCase(
            HTTPBlobPayload(payload=b"\xde\xad\xbe\xef"),
            HTTPMessage(
                fields=tuples_to_fields([("content-type", "application/octet-stream")]),
                body=b"\xde\xad\xbe\xef",
            ),
        ),
        HTTPMessageTestCase(
            HTTPStructuredPayload(payload=HTTPStringPayload(payload="foo")),
            HTTPMessage(body=BytesIO(b'{"payload":"foo"}')),
        ),
    ]


def async_streaming_payload_cases() -> list[HTTPMessageTestCase]:
    return [
        HTTPMessageTestCase(
            HTTPStreamingPayload(payload=AsyncBytesReader(b"\xde\xad\xbe\xef")),
            HTTPMessage(
                fields=tuples_to_fields([("content-type", "application/octet-stream")]),
                body=AsyncBytesReader(b"\xde\xad\xbe\xef"),
            ),
        ),
    ]


REQUEST_SER_CASES = (
    header_cases()
    + empty_prefix_header_ser_cases()
    + query_cases()
    + label_cases()
    + host_cases()
    + payload_cases()
    + async_streaming_payload_cases()
)

CONTENT_TYPE_FIELD = Field(name="content-type", values=["application/json"])


@pytest.mark.parametrize("case", REQUEST_SER_CASES)
async def test_serialize_http_request(case: HTTPMessageTestCase) -> None:
    serializer = HTTPRequestSerializer(
        payload_codec=JSONCodec(),
        http_trait=case.http_trait,
        endpoint_trait=case.endpoint_trait,
    )
    case.shape.serialize(serializer)
    actual = serializer.result
    expected = case.request

    assert actual is not None
    assert actual.method == expected.method
    assert actual.destination.host == expected.destination.host
    assert actual.destination.path == expected.destination.path
    actual_query = actual.destination.query or ""
    expected_query = case.request.destination.query or ""
    assert actual_query == expected_query
    # set the content-type field here, otherwise cases would have to duplicate it everywhere,
    # but if the field is already set in the case, don't override it
    if expected.fields.get(CONTENT_TYPE_FIELD.name) is None:
        expected.fields.set_field(CONTENT_TYPE_FIELD)
    assert actual.fields == expected.fields

    if case.request.body:
        actual_body_value = await AsyncBytesReader(actual.body).read()
        expected_body_value = await AsyncBytesReader(case.request.body).read()
        assert actual_body_value == expected_body_value
        assert type(actual.body) is type(case.request.body)


RESPONSE_SER_CASES: list[HTTPMessageTestCase] = (
    header_cases() + empty_prefix_header_ser_cases() + payload_cases()
)


@pytest.mark.parametrize("case", RESPONSE_SER_CASES)
async def test_serialize_http_response(case: HTTPMessageTestCase) -> None:
    serializer = HTTPResponseSerializer(
        payload_codec=JSONCodec(), http_trait=case.http_trait
    )
    case.shape.serialize(serializer)
    actual = serializer.result
    expected = case.request

    assert actual is not None
    # Remove content-type from expected, we're re-using the request cases for brevity
    if expected.fields.get(CONTENT_TYPE_FIELD.name) is not None:
        del expected.fields[CONTENT_TYPE_FIELD.name]
    assert actual.fields == expected.fields
    assert actual.status == expected.status

    if case.request.body:
        actual_body_value = await AsyncBytesReader(actual.body).read()
        expected_body_value = await AsyncBytesReader(case.request.body).read()
        assert actual_body_value == expected_body_value
        assert type(actual.body) is type(case.request.body)


RESPONSE_DESER_CASES: list[HTTPMessageTestCase] = (
    header_cases() + empty_prefix_header_deser_cases() + payload_cases()
)


# TODO: Move this to a separate file
@pytest.mark.parametrize("case", RESPONSE_DESER_CASES)
async def test_deserialize_http_response(case: HTTPMessageTestCase) -> None:
    body = case.request.body
    if (read := getattr(body, "read", None)) is not None and iscoroutinefunction(read):
        body = BytesIO(await read())
    deserializer = HTTPResponseDeserializer(
        payload_codec=JSONCodec(),
        http_trait=case.http_trait,
        response=_HTTPResponse(
            body=case.request.body,
            status=case.request.status,
            fields=case.request.fields,
        ),
        body=body,  # type: ignore
    )
    actual = type(case.shape).deserialize(deserializer)
    assert actual == case.shape


async def test_deserialize_http_response_with_async_stream() -> None:
    stream = AsyncBytesReader(b"\xde\xad\xbe\xef")

    deserializer = HTTPResponseDeserializer(
        payload_codec=JSONCodec(),
        http_trait=HTTPTrait({"method": "POST", "code": 200, "uri": "/"}),
        response=_HTTPResponse(body=stream, status=200, fields=Fields()),
    )
    actual = HTTPStreamingPayload.deserialize(deserializer)
    assert actual == HTTPStreamingPayload(stream)
