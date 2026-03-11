#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import datetime
from base64 import b64decode
from collections.abc import Callable
from decimal import Decimal
from xml.etree.ElementTree import Element

from smithy_core.deserializers import ShapeDeserializer, SpecificShapeDeserializer
from smithy_core.documents import Document
from smithy_core.exceptions import SmithyError
from smithy_core.schemas import Schema
from smithy_core.shapes import ShapeID, ShapeType
from smithy_core.traits import (
    TimestampFormatTrait,
    XmlAttributeTrait,
    XmlFlattenedTrait,
    XmlNameTrait,
)

from ..settings import XMLSettings
from .readers import XMLEvent, XMLEventReader


def _local_name(tag: str) -> str:
    """Strip namespace URI from an element tag: {uri}local -> local."""
    if tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


def _expected_root_name(schema: Schema) -> str | None:
    """Get the expected root element name for root validation."""
    if schema.shape_type not in (ShapeType.STRUCTURE, ShapeType.UNION):
        return None
    if xml_name := schema.get_trait(XmlNameTrait):
        return xml_name.value
    return schema.id.name


def _validate_element_name(expected: str, elem: Element) -> None:
    """Raise XMLParseError if the element's local name doesn't match expected."""
    found = _local_name(elem.tag)
    if found != expected:
        raise XMLParseError(f"Expected element '{expected}', got '{found}'")


def _xml_member_name(member_schema: Schema) -> str:
    """Get the XML element name for a member, respecting @xmlName."""
    if xml_name := member_schema.get_trait(XmlNameTrait):
        return xml_name.value
    return member_schema.expect_member_name()


def _parse_xml_float(text: str) -> float:
    """Parse an XML float string, handling NaN and Infinity."""
    match text:
        case "NaN":
            return float("nan")
        case "Infinity":
            return float("inf")
        case "-Infinity":
            return float("-inf")
        case _:
            return float(text)


class XMLParseError(SmithyError):
    def __init__(self, message: str) -> None:
        super().__init__(f"Error parsing XML: {message}")


class XMLShapeDeserializer(ShapeDeserializer):
    """Deserializer that reads XML from a streaming pull parser."""

    def __init__(
        self,
        settings: XMLSettings,
        reader: XMLEventReader,
        wrapper_elements: tuple[str, ...] = (),
    ) -> None:
        self._settings = settings
        self._reader = reader
        self._is_root = not bool(wrapper_elements)
        self._xml_names: dict[ShapeID, dict[str, Schema]] = {}
        self._preconsumed_start: Element | None = None

        # Wrapper elements are protocol transport containers (e.g. awsQuery's
        # <OpResponse><OpResult>). The last wrapper's start element is kept
        # so that the next read can reuse it.
        for wrapper in wrapper_elements:
            event = next(self._reader)
            if event.type != "start":
                raise XMLParseError(f"Expected start element, got '{event.type}'")
            _validate_element_name(wrapper, event.elem)
            self._preconsumed_start = event.elem

    def is_null(self) -> bool:
        return False

    def read_null(self) -> None:
        return None

    def read_boolean(self, schema: Schema) -> bool:
        text = self._read_text()
        match text:
            case "true":
                return True
            case "false":
                return False
            case _:
                raise XMLParseError(f"Expected 'true' or 'false', got '{text}'")

    def read_blob(self, schema: Schema) -> bytes:
        return b64decode(self._read_text())

    def read_integer(self, schema: Schema) -> int:
        return int(self._read_text())

    def read_float(self, schema: Schema) -> float:
        return _parse_xml_float(self._read_text())

    def read_big_decimal(self, schema: Schema) -> Decimal:
        return Decimal(self._read_text())

    def read_string(self, schema: Schema) -> str:
        return self._read_text()

    def read_document(self, schema: Schema) -> Document:
        raise NotImplementedError("XML does not support document types")

    def read_timestamp(self, schema: Schema) -> datetime.datetime:
        fmt = self._settings.default_timestamp_format
        if format_trait := schema.get_trait(TimestampFormatTrait):
            fmt = format_trait.format

        text = self._read_text()
        return fmt.deserialize(text)

    def read_struct(
        self,
        schema: Schema,
        consumer: Callable[[Schema, "ShapeDeserializer"], None],
    ) -> None:
        xml_names = self._get_xml_names(schema)
        start_from_wrapper = self._preconsumed_start is not None
        start_elem = self._consume_start_event()
        if self._is_root:
            self._is_root = False
            expected = _expected_root_name(schema)
            if expected is not None:
                _validate_element_name(expected, start_elem)

        # Wrapper elements are protocol transport containers, not modeled structs,
        # so their attributes cannot be deserialized as struct members.
        if not start_from_wrapper:
            for member_schema in schema.members.values():
                if member_schema.get_trait(XmlAttributeTrait) is None:
                    continue
                expected_attr_name = _xml_member_name(member_schema)
                for attr_name, attr_value in start_elem.attrib.items():
                    attr_local_name = _local_name(attr_name)
                    if attr_local_name == expected_attr_name:
                        consumer(
                            member_schema,
                            _AttributeDeserializer(attr_value, self._settings),
                        )
                        break

        # Flattened members lack an enclosing element, so there is no way to
        # know when all items have been parsed. Their events are collected
        # during iteration and replayed through a bounded reader afterwards.
        flattened_buffers: dict[str, list[XMLEvent]] = {}
        flattened_names = {
            xml_name: member_schema
            for xml_name, member_schema in xml_names.items()
            if member_schema.get_trait(XmlFlattenedTrait) is not None
        }

        while self._reader.peek().type != "end":
            tag = _local_name(self._reader.peek().elem.tag)

            if tag in flattened_names:
                flattened_buffers.setdefault(tag, []).extend(self._buffer_element())
            elif tag in xml_names:
                consumer(xml_names[tag], self)
            else:
                # Skip unknown tag
                self._consume_start_event()
                self._skip_to_end()

        next(self._reader)

        for tag, events in flattened_buffers.items():
            member_schema = flattened_names[tag]
            buffered_de = XMLShapeDeserializer(
                self._settings,
                XMLEventReader(iter(events)),
            )
            consumer(member_schema, buffered_de)

    def read_list(
        self,
        schema: Schema,
        consumer: Callable[["ShapeDeserializer"], None],
    ) -> None:
        is_flattened = schema.get_trait(XmlFlattenedTrait) is not None
        if not is_flattened:
            self._consume_start_event()
            while self._reader.peek().type != "end":
                consumer(self)
        else:
            while self._reader.has_next():
                consumer(self)

        if not is_flattened:
            next(self._reader)

    def read_map(
        self,
        schema: Schema,
        consumer: Callable[[str, "ShapeDeserializer"], None],
    ) -> None:
        is_flattened = schema.get_trait(XmlFlattenedTrait) is not None
        key_schema = schema.members["key"]
        value_schema = schema.members["value"]
        key_tag = _xml_member_name(key_schema)
        value_tag = _xml_member_name(value_schema)

        if not is_flattened:
            self._consume_start_event()
            while self._reader.peek().type != "end":
                self._read_map_entry(key_tag, value_tag, consumer)
        else:
            while self._reader.has_next():
                self._read_map_entry(key_tag, value_tag, consumer)

        if not is_flattened:
            next(self._reader)

    def _read_text(self) -> str:
        """Consume a complete element (start through end) and return its text."""
        elem = self._consume_start_event()
        self._skip_to_end()
        # elem.text is populated only after consuming the "end" event
        return elem.text or ""

    def _consume_start_event(self) -> Element:
        """Consume and return the next start element.

        If a start element was pre-consumed (e.g. from consuming wrapper elements),
        it is returned first and cleared.
        """
        if self._preconsumed_start is not None:
            elem = self._preconsumed_start
            self._preconsumed_start = None
            return elem
        event = next(self._reader)
        if event.type != "start":
            raise XMLParseError(f"Expected start element, got '{event.type}'")
        return event.elem

    def _skip_to_end(self) -> None:
        """Skip to the matching end event. Assumes start was already consumed."""
        depth = 1
        while depth > 0:
            event = next(self._reader)
            if event.type == "start":
                depth += 1
            elif event.type == "end":
                depth -= 1

    def _buffer_element(self) -> list[XMLEvent]:
        """Buffer a complete element's events (start through matching end)."""
        events: list[XMLEvent] = []
        event = next(self._reader)
        events.append(event)
        depth = 1
        while depth > 0:
            event = next(self._reader)
            events.append(event)
            if event.type == "start":
                depth += 1
            elif event.type == "end":
                depth -= 1
        return events

    def _get_xml_names(self, schema: Schema) -> dict[str, Schema]:
        """Get or build the XML element name -> member schema mapping for a shape."""
        if schema.id in self._xml_names:
            return self._xml_names[schema.id]
        result: dict[str, Schema] = {}
        for member_schema in schema.members.values():
            if member_schema.get_trait(XmlAttributeTrait) is not None:
                continue
            xml_name = _xml_member_name(member_schema)
            result[xml_name] = member_schema
        self._xml_names[schema.id] = result
        return result

    def _read_map_entry(
        self,
        key_tag: str,
        value_tag: str,
        consumer: Callable[[str, "ShapeDeserializer"], None],
    ) -> None:
        """Read one map entry element and emit key/value pairs via consumer."""
        self._consume_start_event()

        key: str | None = None
        while self._reader.peek().type != "end":
            child_tag = _local_name(self._reader.peek().elem.tag)
            if child_tag == key_tag:
                key = self._read_text()
            elif child_tag == value_tag:
                if key is None:
                    raise XMLParseError(
                        "Map key element must appear before value element"
                    )
                consumer(key, self)
            else:
                # Skip unknown child tag
                self._consume_start_event()
                self._skip_to_end()

        next(self._reader)


class _AttributeDeserializer(SpecificShapeDeserializer):
    """Deserializer for a value extracted from an XML attribute string."""

    def __init__(self, value: str, settings: XMLSettings) -> None:
        self._value = value
        self._settings = settings

    def read_string(self, schema: Schema) -> str:
        return self._value

    def read_boolean(self, schema: Schema) -> bool:
        match self._value:
            case "true":
                return True
            case "false":
                return False
            case _:
                raise XMLParseError(f"Expected 'true' or 'false', got '{self._value}'")

    def read_byte(self, schema: Schema) -> int:
        return self.read_integer(schema)

    def read_short(self, schema: Schema) -> int:
        return self.read_integer(schema)

    def read_integer(self, schema: Schema) -> int:
        return int(self._value)

    def read_long(self, schema: Schema) -> int:
        return self.read_integer(schema)

    def read_big_integer(self, schema: Schema) -> int:
        return self.read_integer(schema)

    def read_float(self, schema: Schema) -> float:
        return _parse_xml_float(self._value)

    def read_double(self, schema: Schema) -> float:
        return self.read_float(schema)

    def read_big_decimal(self, schema: Schema) -> Decimal:
        return Decimal(self._value)

    def read_timestamp(self, schema: Schema) -> datetime.datetime:
        fmt = self._settings.default_timestamp_format
        if format_trait := schema.get_trait(TimestampFormatTrait):
            fmt = format_trait.format

        return fmt.deserialize(self._value)
