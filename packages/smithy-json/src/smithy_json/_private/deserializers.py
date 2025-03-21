#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import datetime
from base64 import b64decode
from collections.abc import Callable, Iterator, Mapping, Sequence
from decimal import Decimal
from typing import Literal, NamedTuple, Protocol, cast

import ijson  # type: ignore
from ijson.common import ObjectBuilder  # type: ignore
from smithy_core.deserializers import ShapeDeserializer
from smithy_core.documents import Document
from smithy_core.exceptions import SmithyException
from smithy_core.interfaces import BytesReader
from smithy_core.schemas import Schema
from smithy_core.shapes import ShapeID, ShapeType
from smithy_core.traits import JSONNameTrait, TimestampFormatTrait
from smithy_core.types import TimestampFormat

from .documents import JSONDocument

# TODO: put these type hints in a pyi somewhere. There here because ijson isn't
# typed.
type JSONParseEventType = Literal[
    "null",
    "string",
    "number",
    "boolean",
    "start_array",
    "end_array",
    "start_map",
    "map_key",
    "end_map",
]

type JSONParseEventValue = str | int | float | Decimal | bool | None

type JSON = Mapping[str, "JSON"] | Sequence["JSON"] | JSONParseEventValue


class JSONParseEvent(NamedTuple):
    path: str
    type: JSONParseEventType
    value: JSONParseEventValue


class JSONTokenError(SmithyException):
    def __init__(self, expected: str, event: JSONParseEvent) -> None:
        super().__init__(
            f"Error parsing JSON. Expected token of type `{expected}` at path "
            f"`{event.path}`, but found: `{event.type}`: {event.value}"
        )


class TypedObjectBuilder(Protocol):
    value: JSON

    def event(self, event: JSONParseEventType, value: JSONParseEventValue): ...


class BufferedParser:
    """A wrapper around the ijson parser that allows peeking."""

    def __init__(
        self, stream: Iterator[tuple[str, JSONParseEventType, JSONParseEventValue]]
    ) -> None:
        self._stream = stream
        self._pending: JSONParseEvent | None = None

    def __iter__(self):
        return self

    def __next__(self) -> JSONParseEvent:
        if self._pending is not None:
            result = self._pending
            self._pending = None
            return result
        return self._next()

    def _next(self) -> JSONParseEvent:
        return JSONParseEvent(*next(self._stream))

    def peek(self) -> JSONParseEvent:
        if self._pending is None:
            self._pending = self._next()
        return self._pending


class JSONShapeDeserializer(ShapeDeserializer):
    def __init__(
        self,
        source: BytesReader,
        *,
        use_json_name: bool = True,
        use_timestamp_format: bool = True,
        default_timestamp_format: TimestampFormat = TimestampFormat.DATE_TIME,
    ) -> None:
        self._stream = BufferedParser(ijson.parse(source))
        self._use_json_name = use_json_name
        self._use_timestamp_format = use_timestamp_format
        self._default_timestamp_format = default_timestamp_format

        # A mapping of json name to member name for each shape. Since the deserializer
        # is shared and we don't know which shapes will be deserialized, this is
        # populated on an as-needed basis.
        self._json_names: dict[ShapeID, dict[str, str]] = {}

    def is_null(self) -> bool:
        return self._stream.peek().type == "null"

    def read_null(self) -> None:
        event = next(self._stream)
        if event.value is not None:
            raise JSONTokenError("null", event)
        return None

    def read_boolean(self, schema: Schema) -> bool:
        event = next(self._stream)
        if not isinstance(event.value, bool):
            raise JSONTokenError("boolean", event)
        return event.value

    def read_blob(self, schema: Schema) -> bytes:
        event = next(self._stream)
        if event.type != "string" or not isinstance(event.value, str):
            raise JSONTokenError("string", event)
        return b64decode(event.value)

    def read_integer(self, schema: Schema) -> int:
        event = next(self._stream)
        if not isinstance(event.value, int):
            raise JSONTokenError("number", event)
        return event.value

    def read_float(self, schema: Schema) -> float:
        event = next(self._stream)
        match event.value:
            case Decimal():
                return float(event.value)
            case int() | float():
                return event.value
            case "Infinity" | "-Infinity" | "NaN":
                return float(event.value)
            case _:
                raise JSONTokenError("number", event)

    def read_big_decimal(self, schema: Schema) -> Decimal:
        event = next(self._stream)
        match event.value:
            case Decimal():
                return event.value
            case int() | float():
                return Decimal.from_float(event.value)
            case _:
                raise JSONTokenError("number", event)

    def read_string(self, schema: Schema) -> str:
        event = next(self._stream)
        if event.type not in ("string", "map_key") or not isinstance(event.value, str):
            raise JSONTokenError("string | map_key", event)
        return event.value

    def read_document(self, schema: Schema) -> Document:
        start = next(self._stream)
        if start.type not in ("start_map", "start_array"):
            return JSONDocument(
                start.value,
                schema=schema,
                use_json_name=self._use_json_name,
                default_timestamp_format=self._default_timestamp_format,
                use_timestamp_format=self._use_timestamp_format,
            )

        end_type = "end_map" if start.type == "start_map" else "end_array"
        builder = cast(TypedObjectBuilder, ObjectBuilder())
        builder.event(start.type, start.value)
        while (
            event := next(self._stream)
        ).path != start.path or event.type != end_type:
            builder.event(event.type, event.value)

        return JSONDocument(
            builder.value,
            schema=schema,
            use_json_name=self._use_json_name,
            default_timestamp_format=self._default_timestamp_format,
            use_timestamp_format=self._use_timestamp_format,
        )

    def read_timestamp(self, schema: Schema) -> datetime.datetime:
        format = self._default_timestamp_format
        if self._use_timestamp_format:
            if format_trait := schema.get_trait(TimestampFormatTrait):
                format = format_trait.format

        match format:
            case TimestampFormat.EPOCH_SECONDS:
                return format.deserialize(self.read_float(schema=schema))
            case _:
                return format.deserialize(self.read_string(schema=schema))

    def read_struct(
        self, schema: Schema, consumer: Callable[[Schema, "ShapeDeserializer"], None]
    ):
        event = next(self._stream)
        if event.type != "start_map":
            raise JSONTokenError("start_map", event)

        while self._stream.peek().type != "end_map":
            key = self.read_string(schema=schema)
            member = self._resolve_member(schema=schema, key=key)
            if not member:
                self._skip()
                continue
            if self.is_null() and member.shape_type is not ShapeType.DOCUMENT:
                self.read_null()
                continue
            consumer(member, self)

        next(self._stream)

    def _resolve_member(self, schema: Schema, key: str) -> Schema | None:
        if self._use_json_name:
            if schema.id not in self._json_names:
                self._cache_json_names(schema=schema)
            if key in self._json_names[schema.id]:
                return schema.members.get(self._json_names[schema.id][key])
            return None

        return schema.members.get(key)

    def _cache_json_names(self, schema: Schema):
        result: dict[str, str] = {}
        for member_name, member_schema in schema.members.items():
            name: str = member_name
            if json_name := member_schema.get_trait(JSONNameTrait):
                name = json_name.value
            result[name] = member_name
        self._json_names[schema.id] = result

    def read_list(
        self, schema: Schema, consumer: Callable[["ShapeDeserializer"], None]
    ):
        event = next(self._stream)
        if event.type != "start_array":
            raise JSONTokenError("start_array", event)

        while self._stream.peek().type != "end_array":
            consumer(self)

        next(self._stream)

    def read_map(
        self,
        schema: Schema,
        consumer: Callable[[str, "ShapeDeserializer"], None],
    ):
        event = next(self._stream)
        if event.type != "start_map":
            raise JSONTokenError("start_map", event)

        key_schema = schema.members["key"]
        while self._stream.peek().type != "end_map":
            consumer(self.read_string(schema=key_schema), self)

        next(self._stream)

    def _skip(self) -> None:
        start = next(self._stream)
        if start.type not in ("start_map", "start_array"):
            return

        end_type = "end_map" if start.type == "start_map" else "end_array"

        while (
            event := next(self._stream)
        ).path != start.path or event.type != end_type:
            continue
