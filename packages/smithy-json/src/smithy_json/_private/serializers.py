#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from base64 import b64encode
from collections.abc import Callable, Mapping, Sequence
from contextlib import AbstractContextManager
from datetime import datetime
from decimal import Decimal
from io import BufferedWriter, RawIOBase
from types import TracebackType
from typing import Self

from smithy_core.documents import Document, DocumentValue
from smithy_core.interfaces import BytesWriter
from smithy_core.schemas import Schema
from smithy_core.serializers import (
    InterceptingSerializer,
    MapSerializer,
    ShapeSerializer,
)
from smithy_core.traits import JSONNameTrait, TimestampFormatTrait
from smithy_core.types import TimestampFormat

from . import Flushable

_INF: float = float("inf")
_NEG_INF: float = float("-inf")


class JSONShapeSerializer(ShapeSerializer):
    _stream: "StreamingJSONEncoder"
    _use_json_name: bool
    _use_timestamp_format: bool
    _default_timestamp_format: TimestampFormat

    def __init__(
        self,
        sink: BytesWriter,
        use_json_name: bool = True,
        use_timestamp_format: bool = True,
        default_timestamp_format: TimestampFormat = TimestampFormat.DATE_TIME,
    ) -> None:
        self._stream = StreamingJSONEncoder(sink)
        self._use_json_name = use_json_name
        self._use_timestamp_format = use_timestamp_format
        self._default_timestamp_format = default_timestamp_format

    def begin_struct(
        self, schema: "Schema"
    ) -> AbstractContextManager["ShapeSerializer"]:
        return JSONStructSerializer(self._stream, self, self._use_json_name)

    def begin_list(
        self, schema: "Schema", size: int
    ) -> AbstractContextManager["ShapeSerializer"]:
        return JSONListSerializer(self._stream, self)

    def begin_map(
        self, schema: "Schema", size: int
    ) -> AbstractContextManager["MapSerializer"]:
        return JSONMapSerializer(self._stream, self)

    def write_null(self, schema: "Schema") -> None:
        self._stream.write_null()

    def write_boolean(self, schema: "Schema", value: bool) -> None:
        self._stream.write_bool(value)

    def write_integer(self, schema: "Schema", value: int) -> None:
        self._stream.write_int(value)

    def write_float(self, schema: "Schema", value: float) -> None:
        self._stream.write_float(value)

    def write_big_decimal(self, schema: "Schema", value: Decimal) -> None:
        self._stream.write_float(value)

    def write_string(self, schema: "Schema", value: str) -> None:
        self._stream.write_string(value)

    def write_blob(self, schema: "Schema", value: bytes) -> None:
        self._stream.write_string(b64encode(value).decode("utf-8"))

    def write_timestamp(self, schema: "Schema", value: datetime) -> None:
        format = self._default_timestamp_format
        if self._use_timestamp_format:
            if format_trait := schema.get_trait(TimestampFormatTrait):
                format = format_trait.format

        self._stream.write_document_value(format.serialize(value))

    def write_document(self, schema: "Schema", value: Document) -> None:
        value.serialize_contents(self)

    def flush(self) -> None:
        self._stream.flush()


class JSONStructSerializer(InterceptingSerializer):
    _stream: "StreamingJSONEncoder"
    _parent: JSONShapeSerializer
    _use_json_name: bool
    _is_first_member = True

    def __init__(
        self,
        stream: "StreamingJSONEncoder",
        parent: JSONShapeSerializer,
        use_json_name: bool,
    ) -> None:
        self._stream = stream
        self._parent = parent
        self._use_json_name = use_json_name

    def __enter__(self) -> Self:
        self._stream.write_object_start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if not exc_value:
            self._stream.write_object_end()

    def before(self, schema: "Schema") -> ShapeSerializer:
        if self._is_first_member:
            self._is_first_member = False
        else:
            self._stream.write_more()

        member_name = schema.expect_member_name()
        if self._use_json_name and (json_name := schema.get_trait(JSONNameTrait)):
            member_name = json_name.value

        self._stream.write_key(member_name)
        return self._parent

    def after(self, schema: "Schema") -> None:
        pass


class JSONListSerializer(InterceptingSerializer):
    _stream: "StreamingJSONEncoder"
    _parent: JSONShapeSerializer
    _is_first_entry = True

    def __init__(
        self, stream: "StreamingJSONEncoder", parent: JSONShapeSerializer
    ) -> None:
        self._stream = stream
        self._parent = parent

    def __enter__(self) -> Self:
        self._stream.write_array_start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if not exc_value:
            self._stream.write_array_end()

    def before(self, schema: "Schema") -> ShapeSerializer:
        if self._is_first_entry:
            self._is_first_entry = False
        else:
            self._stream.write_more()

        return self._parent

    def after(self, schema: "Schema") -> None:
        pass


class JSONMapSerializer(MapSerializer):
    _stream: "StreamingJSONEncoder"
    _parent: JSONShapeSerializer
    _is_first_entry = True

    def __init__(
        self, stream: "StreamingJSONEncoder", parent: JSONShapeSerializer
    ) -> None:
        self._stream = stream
        self._parent = parent

    def __enter__(self) -> Self:
        self._stream.write_object_start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if not exc_value:
            self._stream.write_object_end()

    def entry(self, key: str, value_writer: Callable[[ShapeSerializer], None]) -> None:
        if self._is_first_entry:
            self._is_first_entry = False
        else:
            self._stream.write_more()

        self._stream.write_key(key)
        value_writer(self._parent)


class StreamingJSONEncoder:
    def __init__(
        self,
        sink: BytesWriter,
        default_timestamp_format: TimestampFormat = TimestampFormat.DATE_TIME,
    ) -> None:
        self._sink = sink
        if isinstance(sink, RawIOBase):
            self._sink = BufferedWriter(sink)
        self._default_timestamp_format = default_timestamp_format

    def write_object_start(self) -> None:
        self._sink.write(b"{")

    def write_object_end(self) -> None:
        self._sink.write(b"}")

    def write_array_start(self) -> None:
        self._sink.write(b"[")

    def write_array_end(self) -> None:
        self._sink.write(b"]")

    def write_key(self, key: str) -> None:
        self.write_string(key)
        self._sink.write(b":")

    def write_more(self):
        self._sink.write(b",")

    def write_document_value(
        self, value: DocumentValue, *, timestamp_format: TimestampFormat | None = None
    ) -> None:
        match value:
            case str():
                self.write_string(value)
            case bool():
                self.write_bool(value)
            case int():
                self.write_int(value)
            case float() | Decimal():
                self.write_float(value)
            case None:
                self.write_null()
            case bytes():
                self.write_string(b64encode(value).decode("utf-8"))
            case datetime():
                format = timestamp_format or self._default_timestamp_format
                self.write_document_value(value=format.serialize(value))
            case Mapping():
                self.write_object_start()
                first = True
                for k, v in value.items():
                    if not first:
                        self.write_more()
                    else:
                        first = False
                    self.write_key(k)
                    self.write_document_value(v)
                self.write_object_end()
            case Sequence():
                self.write_array_start()
                if value:
                    self.write_document_value(value[0])
                    for i in range(1, len(value)):
                        self.write_more()
                        self.write_document_value(value[i])
                self.write_array_end()

    def write_string(self, value: str) -> None:
        self._sink.write(b'"')
        self._sink.write(
            value.replace("\\", "\\\\").replace('"', '\\"').encode("utf-8")
        )
        self._sink.write(b'"')

    def write_int(self, value: int) -> None:
        self._sink.write(repr(value).encode("utf-8"))

    def write_float(self, value: float | Decimal) -> None:
        if not self._write_non_numeric_float(value=value):
            if isinstance(value, Decimal):
                self._sink.write(str(value.normalize()).encode("utf-8"))
            else:
                self._sink.write(repr(value).encode("utf-8"))

    def _write_non_numeric_float(self, value: float | Decimal) -> bool:
        if value != value:
            self._sink.write(b"NaN")
            return True

        if value == _INF:
            self._sink.write(b'"Infinity"')
            return True

        if value == _NEG_INF:
            self._sink.write(b'"-Infinity"')
            return True

        return False

    def write_bool(self, value: bool) -> None:
        self._sink.write(b"true" if value else b"false")

    def write_null(self):
        self._sink.write(b"null")

    def flush(self) -> None:
        if isinstance(self._sink, Flushable):
            self._sink.flush()
