#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from base64 import b64encode
from collections.abc import Callable
from contextlib import AbstractContextManager
from datetime import datetime
from decimal import Decimal
from types import TracebackType
from typing import Self
from urllib.parse import quote

from smithy_core.documents import Document
from smithy_core.exceptions import SerializationError
from smithy_core.interfaces import BytesWriter
from smithy_core.schemas import Schema
from smithy_core.serializers import (
    InterceptingSerializer,
    MapSerializer,
    ShapeSerializer,
)
from smithy_core.traits import TimestampFormatTrait, XmlFlattenedTrait, XmlNameTrait
from smithy_core.types import TimestampFormat
from smithy_core.utils import serialize_float


def _percent_encode_query(value: str) -> str:
    """Encode a query key or value using RFC 3986 percent-encoding."""
    return quote(value, safe="-_.~")


def _resolve_name(schema: Schema, default: str) -> str:
    """Return ``@xmlName`` when present, otherwise ``default``."""
    if (xml_name := schema.get_trait(XmlNameTrait)) is not None:
        return xml_name.value
    return default


def _is_flattened(schema: Schema) -> bool:
    """Return whether a collection is ``@xmlFlattened``."""
    return schema.get_trait(XmlFlattenedTrait) is not None


class QueryShapeSerializer(ShapeSerializer):
    """Serializes Smithy shapes into AWS Query form parameters.

    Tracks a dotted key path and accumulates ``(key, value)`` pairs in a
    shared buffer. Struct/list/map serializers create children that extend the
    path, and primitives append terminal values at the current path. ``flush``
    emits the buffered pairs as the query payload.
    """

    def __init__(
        self,
        *,
        sink: BytesWriter,
        action: str | None = None,
        version: str | None = None,
        path: tuple[str, ...] = (),
        params: list[tuple[str, str]] | None = None,
        default_timestamp_format: TimestampFormat = TimestampFormat.DATE_TIME,
    ) -> None:
        self._sink = sink
        self._action = action
        self._version = version
        self._path = path
        self._params = [] if params is None else params
        self._default_timestamp_format = default_timestamp_format

    def child(self, *segments: str) -> "QueryShapeSerializer":
        return QueryShapeSerializer(
            sink=self._sink,
            path=(*self._path, *segments),
            params=self._params,
            default_timestamp_format=self._default_timestamp_format,
        )

    def append(self, value: str) -> None:
        if not self._path:
            raise SerializationError(
                "Unable to serialize AWS Query value without a key path."
            )
        self._params.append((".".join(self._path), value))

    def begin_struct(self, schema: Schema) -> AbstractContextManager[ShapeSerializer]:
        return QueryStructSerializer(self)

    def begin_list(
        self, schema: Schema, size: int
    ) -> AbstractContextManager[ShapeSerializer]:
        if size == 0:
            self.append("")
        return QueryListSerializer(self, schema)

    def begin_map(
        self, schema: Schema, size: int
    ) -> AbstractContextManager[MapSerializer]:
        return QueryMapSerializer(self, schema)

    def write_null(self, schema: Schema) -> None:
        return None

    def write_boolean(self, schema: Schema, value: bool) -> None:
        self.append("true" if value else "false")

    def write_integer(self, schema: Schema, value: int) -> None:
        self.append(str(value))

    def write_float(self, schema: Schema, value: float) -> None:
        self.append(serialize_float(value))

    def write_big_decimal(self, schema: Schema, value: Decimal) -> None:
        self.append(serialize_float(value))

    def write_string(self, schema: Schema, value: str) -> None:
        self.append(value)

    def write_blob(self, schema: Schema, value: bytes) -> None:
        self.append(b64encode(value).decode("utf-8"))

    def write_timestamp(self, schema: Schema, value: datetime) -> None:
        format = self._default_timestamp_format
        if (trait := schema.get_trait(TimestampFormatTrait)) is not None:
            format = trait.format
        self.append(str(format.serialize(value)))

    def write_document(self, schema: Schema, value: Document) -> None:
        raise SerializationError("Query protocols do not support document types.")

    def flush(self) -> None:
        serialized: list[tuple[str, str]] = []
        if self._action is not None and self._version is not None:
            serialized.extend(
                [
                    ("Action", self._action),
                    ("Version", self._version),
                ]
            )
        serialized.extend(self._params)
        body = "&".join(
            f"{_percent_encode_query(key)}={_percent_encode_query(value)}"
            for key, value in serialized
        ).encode("utf-8")
        self._sink.write(body)


class QueryStructSerializer(InterceptingSerializer):
    """Serializes struct members as child query paths.

    ``before`` creates a child serializer rooted at the member name, honoring
    ``@xmlName``.
    """

    def __init__(self, parent: QueryShapeSerializer) -> None:
        self._parent = parent

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        pass

    def before(self, schema: Schema) -> ShapeSerializer:
        return self._parent.child(_resolve_name(schema, schema.expect_member_name()))

    def after(self, schema: Schema) -> None:
        pass


class QueryListSerializer(InterceptingSerializer):
    """Serializes list entries as indexed child query paths.

    ``before`` increments a 1-based index and creates the item path as either
    ``<member>.<index>`` or ``<index>`` when the list is flattened.
    """

    def __init__(self, parent: QueryShapeSerializer, schema: Schema) -> None:
        self._parent = parent
        self._is_flattened = _is_flattened(schema)
        self._item_name = _resolve_name(schema.members["member"], "member")
        self._index = 0

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        pass

    def before(self, schema: Schema) -> ShapeSerializer:
        self._index += 1
        if self._is_flattened:
            return self._parent.child(str(self._index))
        return self._parent.child(self._item_name, str(self._index))

    def after(self, schema: Schema) -> None:
        pass


class QueryMapSerializer(MapSerializer):
    """Serializes map entries as indexed key and value query paths.

    Each entry increments a 1-based index, uses ``entry.<index>`` (or
    ``<index>`` when flattened), writes the key at ``...<keyName>``, and
    serializes the value at ``...<valueName>``.
    """

    def __init__(self, parent: QueryShapeSerializer, schema: Schema) -> None:
        self._parent = parent
        self._is_flattened = _is_flattened(schema)
        self._key_name = _resolve_name(schema.members["key"], "key")
        self._value_name = _resolve_name(schema.members["value"], "value")
        self._index = 0

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        pass

    def entry(self, key: str, value_writer: Callable[[ShapeSerializer], None]) -> None:
        self._index += 1
        if self._is_flattened:
            entry_path = (str(self._index),)
        else:
            entry_path = ("entry", str(self._index))

        self._parent.child(*entry_path, self._key_name).append(key)
        value_writer(self._parent.child(*entry_path, self._value_name))
