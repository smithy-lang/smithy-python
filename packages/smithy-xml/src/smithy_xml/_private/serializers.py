#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from base64 import b64encode
from collections.abc import Callable
from contextlib import AbstractContextManager
from datetime import datetime
from decimal import Decimal
from types import TracebackType
from typing import Self
from xml.etree.ElementTree import Element, SubElement, tostring

from smithy_core.documents import Document
from smithy_core.interfaces import BytesWriter
from smithy_core.schemas import Schema
from smithy_core.serializers import (
    InterceptingSerializer,
    MapSerializer,
    ShapeSerializer,
    SpecificShapeSerializer,
)
from smithy_core.shapes import ShapeType
from smithy_core.traits import (
    TimestampFormatTrait,
    XmlAttributeTrait,
    XmlFlattenedTrait,
    XmlNamespaceTrait,
    XmlNameTrait,
)

from ..settings import XMLSettings

_INF: float = float("inf")
_NEG_INF: float = float("-inf")


def _xml_member_name(member_schema: Schema) -> str:
    """Get the XML element name for a member, respecting @xmlName."""
    if xml_name := member_schema.get_trait(XmlNameTrait):
        return xml_name.value
    return member_schema.expect_member_name()


def _xml_root_name(schema: Schema) -> str:
    """Get the XML root element name, respecting @xmlName and member targets."""
    if xml_name := schema.get_trait(XmlNameTrait):
        return xml_name.value
    if schema.member_target is not None:
        return schema.expect_member_target().id.name
    return schema.id.name


def _set_xml_namespace(
    element: Element,
    schema: Schema,
    settings: XMLSettings,
    *,
    is_root: bool = False,
) -> None:
    """Apply @xmlNamespace to an element, or the default namespace if root."""
    if namespace_trait := schema.get_trait(XmlNamespaceTrait):
        if namespace_trait.prefix:
            element.set(f"xmlns:{namespace_trait.prefix}", namespace_trait.uri)
        else:
            element.set("xmlns", namespace_trait.uri)
        return

    if is_root and settings.default_namespace:
        element.set("xmlns", settings.default_namespace)


def _format_xml_float(value: float) -> str:
    """Format a float for XML, handling NaN and Infinity."""
    if value != value:
        return "NaN"
    if value == _INF:
        return "Infinity"
    if value == _NEG_INF:
        return "-Infinity"
    return repr(value)


def _is_flattened_collection_schema(schema: Schema) -> bool:
    """Check if a schema is a flattened list or map."""
    return schema.get_trait(XmlFlattenedTrait) is not None and schema.shape_type in (
        ShapeType.LIST,
        ShapeType.MAP,
    )


class XMLShapeSerializer(ShapeSerializer):
    """Serializes Smithy shapes into XML and writes the result to a BytesWriter.

    Builds an in-memory XML tree backed by an element stack. ``write_*``
    methods target the top element, and struct/list/map serializers push and
    pop child elements to control nesting. ``flush`` writes the tree to the
    sink.
    """

    def __init__(self, sink: BytesWriter, settings: XMLSettings) -> None:
        self._sink = sink
        self.settings = settings
        self._root: Element | None = None
        self.element_stack: list[Element] = []

    @property
    def current(self) -> Element:
        return self.element_stack[-1]

    def ensure_root(self, schema: Schema) -> None:
        if self._root is not None:
            return
        root = Element(_xml_root_name(schema))
        _set_xml_namespace(root, schema, self.settings, is_root=True)
        self._root = root
        self.element_stack.append(root)

    def begin_struct(
        self, schema: "Schema"
    ) -> AbstractContextManager["ShapeSerializer"]:
        return XMLStructSerializer(self, schema)

    def begin_list(
        self, schema: "Schema", size: int
    ) -> AbstractContextManager["ShapeSerializer"]:
        return XMLListSerializer(self, schema)

    def begin_map(
        self, schema: "Schema", size: int
    ) -> AbstractContextManager["MapSerializer"]:
        return XMLMapSerializer(self, schema)

    def write_null(self, schema: "Schema") -> None:
        self.ensure_root(schema)

    def write_boolean(self, schema: "Schema", value: bool) -> None:
        self.ensure_root(schema)
        self.current.text = "true" if value else "false"

    def write_integer(self, schema: "Schema", value: int) -> None:
        self.ensure_root(schema)
        self.current.text = str(value)

    def write_float(self, schema: "Schema", value: float) -> None:
        self.ensure_root(schema)
        self.current.text = _format_xml_float(value)

    def write_big_decimal(self, schema: "Schema", value: Decimal) -> None:
        self.ensure_root(schema)
        self.current.text = str(value.normalize())

    def write_string(self, schema: "Schema", value: str) -> None:
        self.ensure_root(schema)
        self.current.text = value

    def write_blob(self, schema: "Schema", value: bytes) -> None:
        self.ensure_root(schema)
        self.current.text = b64encode(value).decode("utf-8")

    def write_timestamp(self, schema: "Schema", value: datetime) -> None:
        self.ensure_root(schema)
        fmt = self.settings.default_timestamp_format
        if format_trait := schema.get_trait(TimestampFormatTrait):
            fmt = format_trait.format
        self.current.text = str(fmt.serialize(value))

    def write_document(self, schema: "Schema", value: Document) -> None:
        raise NotImplementedError("XML does not support document types.")

    def flush(self) -> None:
        if self._root is None:
            return
        xml_bytes = tostring(self._root, encoding="utf-8", xml_declaration=False)
        self._sink.write(xml_bytes)

        self._root = None
        self.element_stack.clear()


class XMLStructSerializer(InterceptingSerializer):
    """Serializes struct members as child XML elements.

    ``before`` pushes a child element for the member onto the parent's stack,
    and ``after`` pops it. Attributes and flattened collections are special-cased
    to skip the push/pop.
    """

    def __init__(self, parent: XMLShapeSerializer, schema: Schema) -> None:
        self._parent = parent
        self._schema = schema

    def __enter__(self) -> Self:
        self._parent.ensure_root(self._schema)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        pass

    def before(self, schema: "Schema") -> ShapeSerializer:
        member_name = _xml_member_name(schema)

        # Attributes are written on the current element, not as children.
        if schema.get_trait(XmlAttributeTrait) is not None:
            return XMLAttributeSerializer(
                self._parent.current, member_name, self._parent.settings
            )

        # Flattened collections have no wrapper element. Items are added
        # directly under the current element without changing the stack.
        if _is_flattened_collection_schema(schema):
            return self._parent

        # Non-flattened collections push a wrapper element onto the stack.
        child = SubElement(self._parent.current, member_name)
        _set_xml_namespace(child, schema, self._parent.settings)
        self._parent.element_stack.append(child)
        return self._parent

    def after(self, schema: "Schema") -> None:
        # Attributes and flattened collections didn't push, so don't pop.
        if schema.get_trait(XmlAttributeTrait) is not None:
            return
        if _is_flattened_collection_schema(schema):
            return
        self._parent.element_stack.pop()


class XMLListSerializer(InterceptingSerializer):
    """Serializes list items as repeated child elements.

    ``before`` pushes a child element for each item, ``after`` pops it.
    """

    def __init__(self, parent: XMLShapeSerializer, schema: Schema) -> None:
        self._parent = parent
        self._schema = schema
        is_flattened = schema.get_trait(XmlFlattenedTrait) is not None

        if is_flattened:
            if schema.member_target is not None:
                self._item_tag = _xml_member_name(schema)
            else:
                self._item_tag = _xml_root_name(schema)
        else:
            self._item_tag = _xml_member_name(schema.members["member"])

    def __enter__(self) -> Self:
        self._parent.ensure_root(self._schema)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        pass

    def before(self, schema: "Schema") -> ShapeSerializer:
        child = SubElement(self._parent.current, self._item_tag)
        _set_xml_namespace(child, schema, self._parent.settings)
        self._parent.element_stack.append(child)
        return self._parent

    def after(self, schema: "Schema") -> None:
        self._parent.element_stack.pop()


class XMLMapSerializer(MapSerializer):
    """Serializes map entries as ``<entry><key>…</key><value>…</value></entry>`` elements.

    Each ``entry`` call pushes the value element onto the stack for the
    value writer callback, then pops it.
    """

    def __init__(self, parent: XMLShapeSerializer, schema: Schema) -> None:
        self._parent = parent
        self._schema = schema
        self._is_flattened = schema.get_trait(XmlFlattenedTrait) is not None

        self._key_schema = schema.members["key"]
        self._value_schema = schema.members["value"]
        self._key_tag = _xml_member_name(self._key_schema)
        self._value_tag = _xml_member_name(self._value_schema)

        if self._is_flattened:
            if schema.member_target is not None:
                self._entry_tag = _xml_member_name(schema)
            else:
                self._entry_tag = _xml_root_name(schema)
        else:
            self._entry_tag = "entry"

    def __enter__(self) -> Self:
        self._parent.ensure_root(self._schema)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        pass

    def entry(self, key: str, value_writer: Callable[[ShapeSerializer], None]) -> None:
        settings = self._parent.settings
        entry_el = SubElement(self._parent.current, self._entry_tag)
        if self._is_flattened:
            _set_xml_namespace(entry_el, self._schema, settings)

        key_el = SubElement(entry_el, self._key_tag)
        _set_xml_namespace(key_el, self._key_schema, settings)
        key_el.text = key

        value_el = SubElement(entry_el, self._value_tag)
        _set_xml_namespace(value_el, self._value_schema, settings)
        self._parent.element_stack.append(value_el)
        value_writer(self._parent)
        self._parent.element_stack.pop()


class XMLAttributeSerializer(SpecificShapeSerializer):
    """Serializer that writes values as XML attributes on the parent element."""

    def __init__(self, element: Element, attr_name: str, settings: XMLSettings) -> None:
        self._element = element
        self._attr_name = attr_name
        self._settings = settings

    def write_null(self, schema: "Schema") -> None:
        pass

    def write_boolean(self, schema: "Schema", value: bool) -> None:
        self._element.set(self._attr_name, "true" if value else "false")

    def write_byte(self, schema: "Schema", value: int) -> None:
        self.write_integer(schema, value)

    def write_short(self, schema: "Schema", value: int) -> None:
        self.write_integer(schema, value)

    def write_integer(self, schema: "Schema", value: int) -> None:
        self._element.set(self._attr_name, str(value))

    def write_long(self, schema: "Schema", value: int) -> None:
        self.write_integer(schema, value)

    def write_big_integer(self, schema: "Schema", value: int) -> None:
        self.write_integer(schema, value)

    def write_float(self, schema: "Schema", value: float) -> None:
        self._element.set(self._attr_name, _format_xml_float(value))

    def write_double(self, schema: "Schema", value: float) -> None:
        self.write_float(schema, value)

    def write_big_decimal(self, schema: "Schema", value: Decimal) -> None:
        self._element.set(self._attr_name, str(value.normalize()))

    def write_string(self, schema: "Schema", value: str) -> None:
        self._element.set(self._attr_name, value)

    def write_timestamp(self, schema: "Schema", value: datetime) -> None:
        fmt = self._settings.default_timestamp_format
        if format_trait := schema.get_trait(TimestampFormatTrait):
            fmt = format_trait.format
        self._element.set(self._attr_name, str(fmt.serialize(value)))
