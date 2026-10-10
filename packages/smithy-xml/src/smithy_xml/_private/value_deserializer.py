#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import datetime
from base64 import b64decode
from collections.abc import Callable, Iterable
from decimal import Decimal
from xml.etree.ElementTree import Element

from smithy_core.deserializers import ShapeDeserializer
from smithy_core.documents import Document
from smithy_core.schemas import Schema
from smithy_core.shapes import ShapeID
from smithy_core.traits import (
    TimestampFormatTrait,
    XMLAttributeTrait,
    XMLFlattenedTrait,
)

from ..settings import XMLSettings
from .deserializers import (
    AttributeDeserializer,
    XMLParseError,
    local_attr_name,
    local_name,
    parse_xml_float,
    validate_element_name,
)
from .traits import member_xml_name


class XMLValueDeserializer(ShapeDeserializer):
    """Deserializer backed by a fully materialized ElementTree value."""

    def __init__(
        self,
        settings: XMLSettings,
        root: Element,
        wrapper_elements: tuple[str, ...] = (),
        *,
        elements: tuple[Element, ...] | None = None,
        xml_names: dict[ShapeID, dict[str, Schema]] | None = None,
    ) -> None:
        self._settings = settings
        self._xml_names = xml_names if xml_names is not None else {}
        self._elements = elements
        self._from_wrapper = bool(wrapper_elements)

        current = root
        for index, wrapper in enumerate(wrapper_elements):
            validate_element_name(wrapper, current)
            if index < len(wrapper_elements) - 1:
                child = next(iter(current), None)
                if child is None:
                    raise XMLParseError(
                        f"Expected wrapper element '{wrapper_elements[index + 1]}'"
                    )
                current = child
        self._element = current

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
        return parse_xml_float(self._read_text())

    def read_big_decimal(self, schema: Schema) -> Decimal:
        return Decimal(self._read_text())

    def read_string(self, schema: Schema) -> str:
        return self._read_text()

    def read_document(self, schema: Schema) -> Document:
        raise NotImplementedError("XML does not support document types")

    def read_timestamp(self, schema: Schema) -> datetime.datetime:
        format = self._settings.default_timestamp_format
        if self._settings.use_timestamp_format:
            if format_trait := schema.get_trait(TimestampFormatTrait):
                format = format_trait.format
        return format.deserialize(self._read_text())

    def read_struct(
        self,
        schema: Schema,
        consumer: Callable[[Schema, ShapeDeserializer], None],
    ) -> None:
        element = self._element
        xml_names = self._get_xml_names(schema)

        if not self._from_wrapper:
            for member_schema in schema.members.values():
                if member_schema.get_trait(XMLAttributeTrait) is None:
                    continue
                expected_name = local_attr_name(member_xml_name(member_schema))
                for attribute_name, value in element.attrib.items():
                    if local_name(attribute_name) == expected_name:
                        consumer(
                            member_schema,
                            AttributeDeserializer(value, self._settings),
                        )
                        break

        flattened: dict[str, list[Element]] = {}
        for child in element:
            name = local_name(child.tag)
            member_schema = xml_names.get(name)
            if member_schema is None:
                continue
            if member_schema.get_trait(XMLFlattenedTrait) is not None:
                flattened.setdefault(name, []).append(child)
            else:
                consumer(member_schema, self._for_element(child))

        for name, elements in flattened.items():
            consumer(
                xml_names[name],
                self._for_elements(elements),
            )

    def read_list(
        self,
        schema: Schema,
        consumer: Callable[[ShapeDeserializer], None],
    ) -> None:
        elements: Iterable[Element]
        if schema.get_trait(XMLFlattenedTrait) is not None:
            elements = self._elements or (self._element,)
        else:
            elements = self._element

        for element in elements:
            consumer(self._for_element(element))

    def read_map(
        self,
        schema: Schema,
        consumer: Callable[[str, ShapeDeserializer], None],
    ) -> None:
        key_tag = member_xml_name(schema.members["key"])
        value_tag = member_xml_name(schema.members["value"])
        entries: Iterable[Element]
        if schema.get_trait(XMLFlattenedTrait) is not None:
            entries = self._elements or (self._element,)
        else:
            entries = self._element

        for entry in entries:
            self._read_map_entry(entry, key_tag, value_tag, consumer)

    def _read_map_entry(
        self,
        entry: Element,
        key_tag: str,
        value_tag: str,
        consumer: Callable[[str, ShapeDeserializer], None],
    ) -> None:
        key: str | None = None
        for child in entry:
            name = local_name(child.tag)
            if name == key_tag:
                key = child.text or ""
            elif name == value_tag:
                if key is None:
                    raise XMLParseError(
                        "Map key element must appear before value element"
                    )
                consumer(key, self._for_element(child))

    def _read_text(self) -> str:
        return self._element.text or ""

    def _for_element(self, element: Element) -> "XMLValueDeserializer":
        return XMLValueDeserializer(
            settings=self._settings,
            root=element,
            xml_names=self._xml_names,
        )

    def _for_elements(self, elements: list[Element]) -> "XMLValueDeserializer":
        return XMLValueDeserializer(
            settings=self._settings,
            root=elements[0],
            elements=tuple(elements),
            xml_names=self._xml_names,
        )

    def _get_xml_names(self, schema: Schema) -> dict[str, Schema]:
        if schema.id in self._xml_names:
            return self._xml_names[schema.id]
        result = {
            member_xml_name(member_schema): member_schema
            for member_schema in schema.members.values()
            if member_schema.get_trait(XMLAttributeTrait) is None
        }
        self._xml_names[schema.id] = result
        return result
