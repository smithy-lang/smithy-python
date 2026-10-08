#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""XML shape serializer.

Output is accumulated as string fragments in one shared list and encoded once when
the root element closes. A structure reserves a slot for its start tag and fills it
on close, so ``@xmlAttribute`` members can be written in any member order without
buffering the structure's children.
"""

import datetime
from base64 import b64encode
from collections.abc import Callable
from decimal import Decimal
from types import TracebackType
from typing import NamedTuple, Self

from smithy_core.documents import Document
from smithy_core.exceptions import SerializationError
from smithy_core.interfaces import BytesWriter
from smithy_core.schemas import Schema
from smithy_core.serializers import MapSerializer, ShapeSerializer
from smithy_core.shapes import ShapeID
from smithy_core.traits import (
    TimestampFormatTrait,
    XMLAttributeTrait,
    XMLFlattenedTrait,
    XMLNamespaceTrait,
)
from smithy_core.utils import serialize_float

from ..settings import XMLSettings
from .traits import direct_trait, member_xml_name, root_xml_name


class XMLShapeSerializer(ShapeSerializer):
    """Serializes a top-level shape as an XML document.

    The root element is named by the shape's ``@xmlName`` or shape name and carries
    the shape's ``@xmlNamespace``, falling back to the codec's default namespace.
    The document is written to the sink when the root element closes.
    """

    def __init__(
        self,
        sink: BytesWriter,
        settings: XMLSettings,
        elements: "dict[ShapeID, _Element]",
    ) -> None:
        self._sink = sink
        self._ctx = _Context(settings, elements)

    def _root(self, schema: Schema) -> tuple[str, str]:
        name = root_xml_name(schema)
        namespace = schema.get_trait(XMLNamespaceTrait)
        if namespace is not None:
            xmlns = _xmlns(namespace)
        elif (default := self._ctx.settings.default_namespace) is not None:
            xmlns = f' xmlns="{_escape_attr(default)}"'
        else:
            xmlns = ""
        return f"<{name}{xmlns}", f"</{name}>"

    def begin_struct(self, schema: Schema) -> "_StructWriter":
        start, end = self._root(schema)
        return _StructWriter(self._ctx, start, end, self._sink)

    def begin_list(self, schema: Schema, size: int) -> "_ListWriter":
        raise SerializationError("XML documents must have a structure or union root.")

    def begin_map(self, schema: Schema, size: int) -> "_MapWriter":
        raise SerializationError("XML documents must have a structure or union root.")

    def _write_root_text(self, schema: Schema, text: str) -> None:
        start, end = self._root(schema)
        self._sink.write(f"{start}>{_escape_text(text)}{end}".encode())

    def write_null(self, schema: Schema) -> None:
        pass

    def write_boolean(self, schema: Schema, value: bool) -> None:
        self._write_root_text(schema, "true" if value else "false")

    def write_integer(self, schema: Schema, value: int) -> None:
        self._write_root_text(schema, str(value))

    def write_float(self, schema: Schema, value: float) -> None:
        self._write_root_text(schema, serialize_float(value))

    def write_big_decimal(self, schema: Schema, value: Decimal) -> None:
        self._write_root_text(schema, serialize_float(value))

    def write_string(self, schema: Schema, value: str) -> None:
        self._write_root_text(schema, value)

    def write_blob(self, schema: Schema, value: bytes) -> None:
        self._write_root_text(schema, b64encode(value).decode("ascii"))

    def write_timestamp(self, schema: Schema, value: datetime.datetime) -> None:
        self._write_root_text(schema, self._ctx.format_timestamp(schema, value))

    def write_document(self, schema: Schema, value: Document) -> None:
        raise SerializationError("XML does not support document types.")


def _escape_text(value: str) -> str:
    # Carriage returns are encoded so XML end-of-line normalization keeps them.
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\r", "&#xD;")
    )


def _escape_attr(value: str) -> str:
    return (
        _escape_text(value)
        .replace('"', "&quot;")
        .replace("\n", "&#xA;")
        .replace("\t", "&#x9;")
    )


def _xmlns(trait: XMLNamespaceTrait | None) -> str:
    if trait is None:
        return ""
    if trait.prefix:
        return f' xmlns:{trait.prefix}="{_escape_attr(trait.uri)}"'
    return f' xmlns="{_escape_attr(trait.uri)}"'


class _Element(NamedTuple):
    """Precomputed XML rendering of a member schema."""

    start: str
    """The unterminated start tag, e.g. ``<name xmlns="..."``."""

    end: str
    """The end tag, e.g. ``</name>``."""

    name: str
    is_attribute: bool
    is_flattened: bool


def _member_element(schema: Schema) -> _Element:
    name = member_xml_name(schema)
    return _Element(
        start=f"<{name}{_xmlns(direct_trait(schema, XMLNamespaceTrait))}",
        end=f"</{name}>",
        name=name,
        is_attribute=XMLAttributeTrait in schema,
        is_flattened=XMLFlattenedTrait in schema,
    )


class _Context:
    """State shared by every writer of one serializer.

    Element renderings are cached by member shape ID on the codec so they are
    computed once per member rather than once per value.
    """

    __slots__ = ("_elements", "parts", "settings")

    def __init__(
        self, settings: XMLSettings, elements: dict[ShapeID, _Element]
    ) -> None:
        self.parts: list[str] = []
        self.settings = settings
        self._elements = elements

    def element(self, schema: Schema) -> _Element:
        try:
            return self._elements[schema.id]
        except KeyError:
            element = self._elements[schema.id] = _member_element(schema)
            return element

    def format_timestamp(self, schema: Schema, value: datetime.datetime) -> str:
        format = self.settings.default_timestamp_format
        if self.settings.use_timestamp_format:
            if (trait := schema.get_trait(TimestampFormatTrait)) is not None:
                format = trait.format
        return str(format.serialize(value))


class _ValueWriter(ShapeSerializer):
    """Base writer that renders each value as text inside some element.

    Subclasses decide which element (``_element``) wraps a value and how the text
    is placed (``_write_text``).
    """

    _ctx: _Context

    def _element(self, schema: Schema) -> _Element: ...

    def _write_text(self, schema: Schema, text: str) -> None:
        element = self._element(schema)
        self._ctx.parts.append(f"{element.start}>{_escape_text(text)}{element.end}")

    def begin_struct(self, schema: Schema) -> "_StructWriter":
        element = self._element(schema)
        return _StructWriter(self._ctx, element.start, element.end)

    def begin_list(self, schema: Schema, size: int) -> "_ListWriter":
        element = self._element(schema)
        if element.is_flattened:
            # Each item is written as the member's own element, with no wrapper.
            return _ListWriter(self._ctx, element._replace(is_flattened=False), None)
        self._ctx.parts.append(f"{element.start}>")
        item = self._ctx.element(schema.members["member"])
        return _ListWriter(self._ctx, item, element.end)

    def begin_map(self, schema: Schema, size: int) -> "_MapWriter":
        element = self._element(schema)
        if element.is_flattened:
            return _MapWriter(self._ctx, schema, element.start, element.end, None)
        self._ctx.parts.append(f"{element.start}>")
        return _MapWriter(self._ctx, schema, "<entry", "</entry>", element.end)

    def write_null(self, schema: Schema) -> None:
        pass

    def write_boolean(self, schema: Schema, value: bool) -> None:
        self._write_text(schema, "true" if value else "false")

    def write_integer(self, schema: Schema, value: int) -> None:
        self._write_text(schema, str(value))

    def write_float(self, schema: Schema, value: float) -> None:
        self._write_text(schema, serialize_float(value))

    def write_big_decimal(self, schema: Schema, value: Decimal) -> None:
        self._write_text(schema, serialize_float(value))

    def write_string(self, schema: Schema, value: str) -> None:
        self._write_text(schema, value)

    def write_blob(self, schema: Schema, value: bytes) -> None:
        self._write_text(schema, b64encode(value).decode("ascii"))

    def write_timestamp(self, schema: Schema, value: datetime.datetime) -> None:
        self._write_text(schema, self._ctx.format_timestamp(schema, value))

    def write_document(self, schema: Schema, value: Document) -> None:
        raise SerializationError("XML does not support document types.")


class _StructWriter(_ValueWriter):
    """Writes the members of a structure or union inside its element."""

    def __init__(
        self,
        ctx: _Context,
        start: str,
        end: str,
        sink: BytesWriter | None = None,
    ) -> None:
        self._ctx = ctx
        self._start = start
        self._end = end
        self._sink = sink
        self._attributes = ""
        self._slot = len(ctx.parts)
        # Reserve the start tag's position; it is completed once all attributes
        # have been seen.
        ctx.parts.append("")

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            return
        parts = self._ctx.parts
        parts[self._slot] = f"{self._start}{self._attributes}>"
        parts.append(self._end)
        if self._sink is not None:
            self._sink.write("".join(parts).encode("utf-8"))
            parts.clear()

    def _element(self, schema: Schema) -> _Element:
        return self._ctx.element(schema)

    def _write_text(self, schema: Schema, text: str) -> None:
        element = self._ctx.element(schema)
        if element.is_attribute:
            self._attributes += f' {element.name}="{_escape_attr(text)}"'
        else:
            self._ctx.parts.append(f"{element.start}>{_escape_text(text)}{element.end}")


class _ListWriter(_ValueWriter):
    """Writes every list item as the same element."""

    def __init__(self, ctx: _Context, item: _Element, end: str | None) -> None:
        self._ctx = ctx
        self._item = item
        self._end = end

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if exc_type is None and self._end is not None:
            self._ctx.parts.append(self._end)

    def _element(self, schema: Schema) -> _Element:
        return self._item


class _MapWriter(MapSerializer):
    """Writes map entries as ``<entry><key>..</key><value>..</value></entry>``.

    Flattened maps use the member's element in place of ``entry`` and omit the
    wrapping element.
    """

    def __init__(
        self,
        ctx: _Context,
        schema: Schema,
        entry_start: str,
        entry_end: str,
        end: str | None,
    ) -> None:
        self._ctx = ctx
        self._entry_start = f"{entry_start}>"
        self._entry_end = entry_end
        self._end = end
        key = ctx.element(schema.members["key"])
        self._key_start = f"{key.start}>"
        self._key_end = key.end
        self._value_writer = _ListWriter(
            ctx, ctx.element(schema.members["value"]), None
        )

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if exc_type is None and self._end is not None:
            self._ctx.parts.append(self._end)

    def entry(self, key: str, value_writer: Callable[[ShapeSerializer], None]) -> None:
        parts = self._ctx.parts
        parts.append(
            f"{self._entry_start}{self._key_start}{_escape_text(key)}{self._key_end}"
        )
        value_writer(self._value_writer)
        parts.append(self._entry_end)
