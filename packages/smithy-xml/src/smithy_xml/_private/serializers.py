#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from base64 import b64encode
from collections.abc import Callable, Iterable
from contextlib import AbstractContextManager
from datetime import datetime
from decimal import Decimal
from types import TracebackType
from typing import Protocol, Self

from smithy_core.documents import Document
from smithy_core.exceptions import SerializationError
from smithy_core.interfaces import BytesWriter
from smithy_core.schemas import Schema
from smithy_core.serializers import (
    InterceptingSerializer,
    MapSerializer,
    ShapeSerializer,
)
from smithy_core.traits import (
    TimestampFormatTrait,
    XMLAttributeTrait,
    XMLFlattenedTrait,
    XMLNamespaceTrait,
)
from smithy_core.utils import serialize_float

from ..settings import XMLSettings
from .traits import member_name, namespace_attribute, own_trait, root_name

# Text content only needs the markup characters escaped. Carriage returns are
# escaped as well because XML parsers normalize them to line feeds otherwise.
_TEXT_ESCAPES = str.maketrans({"&": "&amp;", "<": "&lt;", ">": "&gt;", "\r": "&#13;"})

# Attribute values additionally need quotes escaped, and whitespace other than
# spaces escaped so that attribute value normalization doesn't alter them.
_ATTRIBUTE_ESCAPES = str.maketrans(
    {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "\n": "&#10;",
        "\r": "&#13;",
        "\t": "&#9;",
    }
)


def _escape_text(value: str) -> str:
    return value.translate(_TEXT_ESCAPES)


def _format_attribute(name: str, value: str) -> str:
    return f' {name}="{value.translate(_ATTRIBUTE_ESCAPES)}"'


def _format_namespace(trait: XMLNamespaceTrait | None) -> str:
    if trait is None:
        return ""
    return _format_attribute(*namespace_attribute(trait))


class _Fragments(Protocol):
    """A destination for serialized XML fragments.

    This is either a plain list, used to buffer the children of an element until
    its attributes are known, or a :py:class:`_SinkFragments` that writes directly
    to the output at the root of the document.
    """

    def append(self, fragment: str, /) -> None: ...

    def extend(self, fragments: Iterable[str], /) -> None: ...


class _SinkFragments:
    """Writes fragments directly to the underlying byte sink."""

    __slots__ = ("_sink",)

    def __init__(self, sink: BytesWriter) -> None:
        self._sink = sink

    def append(self, fragment: str, /) -> None:
        self._sink.write(fragment.encode("utf-8"))

    def extend(self, fragments: Iterable[str], /) -> None:
        self._sink.write("".join(fragments).encode("utf-8"))


class XMLShapeSerializer(ShapeSerializer):
    """Serializes shapes into XML.

    Each value is written as an element named after the member being written,
    respecting ``@xmlName`` and ``@xmlNamespace``. Members with ``@xmlAttribute``
    are instead written as attributes of the enclosing structure's element.

    Because attributes may be written after child elements, a structure's children
    are buffered as string fragments until the structure is closed, at which point
    the complete element is written to the parent. Everything else is written
    directly to the nearest buffer, so at most one copy is made per nesting level.
    """

    def __init__(
        self,
        settings: XMLSettings,
        *,
        fragments: _Fragments,
        attributes: list[str] | None = None,
        is_root: bool = False,
        name_override: str | None = None,
        namespace_override: str | None = None,
    ) -> None:
        """Initialize an XMLShapeSerializer.

        Use :py:meth:`for_sink` to create the serializer for a document.

        :param settings: The XML settings to use.
        :param fragments: The buffer to write elements to.
        :param attributes: The attribute list of the enclosing structure element,
            if the enclosing element is a structure.
        :param is_root: Whether this serializer writes the root of the document.
        :param name_override: A fixed element name to use instead of the name
            derived from the schema. Used for flattened collection entries, which
            are named after the containing structure's member.
        :param namespace_override: A fixed, pre-formatted namespace declaration to
            use instead of the one derived from the schema.
        """
        self._settings = settings
        self._fragments = fragments
        self._attributes = attributes
        self._is_root = is_root
        self._name_override = name_override
        self._namespace_override = namespace_override

    @classmethod
    def for_sink(cls, sink: BytesWriter, settings: XMLSettings) -> Self:
        """Create a serializer that writes a document to the given sink."""
        return cls(settings, fragments=_SinkFragments(sink), is_root=True)

    def begin_struct(self, schema: Schema) -> AbstractContextManager[ShapeSerializer]:
        return _XMLStructSerializer(
            settings=self._settings,
            parent=self._fragments,
            name=self._element_name(schema),
            namespace=self._namespace(schema),
        )

    def begin_list(
        self, schema: Schema, size: int
    ) -> AbstractContextManager[ShapeSerializer]:
        return _XMLListSerializer(
            settings=self._settings,
            parent=self._fragments,
            schema=schema,
            name=self._element_name(schema),
            namespace=self._namespace(schema),
        )

    def begin_map(
        self, schema: Schema, size: int
    ) -> AbstractContextManager[MapSerializer]:
        return _XMLMapSerializer(
            settings=self._settings,
            parent=self._fragments,
            schema=schema,
            name=self._element_name(schema),
            namespace=self._namespace(schema),
        )

    def write_null(self, schema: Schema) -> None:
        # XML has no representation for null values, so they are omitted.
        return None

    def write_boolean(self, schema: Schema, value: bool) -> None:
        self._write_text(schema, "true" if value else "false")

    def write_integer(self, schema: Schema, value: int) -> None:
        # int() unwraps IntEnum members, whose str() would otherwise be their name.
        self._write_text(schema, str(int(value)))

    def write_float(self, schema: Schema, value: float) -> None:
        self._write_text(schema, serialize_float(value))

    def write_big_decimal(self, schema: Schema, value: Decimal) -> None:
        self._write_text(schema, serialize_float(value))

    def write_string(self, schema: Schema, value: str) -> None:
        # str() unwraps StrEnum members.
        self._write_text(schema, str(value))

    def write_blob(self, schema: Schema, value: bytes) -> None:
        self._write_text(schema, b64encode(value).decode("utf-8"))

    def write_timestamp(self, schema: Schema, value: datetime) -> None:
        format = self._settings.default_timestamp_format
        if self._settings.use_timestamp_format:
            if (format_trait := schema.get_trait(TimestampFormatTrait)) is not None:
                format = format_trait.format
        self._write_text(schema, str(format.serialize(value)))

    def write_document(self, schema: Schema, value: Document) -> None:
        raise SerializationError("XML does not support document types.")

    def _write_text(self, schema: Schema, text: str) -> None:
        if schema.get_trait(XMLAttributeTrait) is not None:
            if self._attributes is None:
                raise SerializationError(
                    "XML attributes may only be written as members of a structure, "
                    f"but {schema.id} has no enclosing structure."
                )
            self._attributes.append(_format_attribute(self._element_name(schema), text))
            return

        name = self._element_name(schema)
        self._fragments.append(
            f"<{name}{self._namespace(schema)}>{_escape_text(text)}</{name}>"
        )

    def _element_name(self, schema: Schema) -> str:
        if self._name_override is not None:
            return self._name_override
        if self._is_root:
            return root_name(schema)
        return member_name(schema)

    def _namespace(self, schema: Schema) -> str:
        """Get the namespace declaration attribute for the schema's element.

        Returns an empty string if there is no namespace to declare.
        """
        if self._namespace_override is not None:
            return self._namespace_override

        if self._is_root:
            # A root shape's own namespace applies. If it's a member, the merged
            # traits give precedence to the member's namespace over the target's.
            if (trait := schema.get_trait(XMLNamespaceTrait)) is not None:
                return _format_namespace(trait)
            if self._settings.default_namespace is not None:
                # A prefixed default namespace declares xmlns:<prefix> rather than
                # the bare xmlns, matching the modeled @xmlNamespace's prefix.
                prefix = self._settings.default_namespace_prefix
                attr_name = f"xmlns:{prefix}" if prefix else "xmlns"
                return _format_attribute(attr_name, self._settings.default_namespace)
            return ""

        # Nested shapes' own namespaces don't apply, only the containing member's.
        return _format_namespace(own_trait(schema, XMLNamespaceTrait))


class _XMLStructSerializer(InterceptingSerializer):
    """Serializes the members of a structure or union as a single element.

    Children are buffered so that attribute members can be written in any order.
    """

    def __init__(
        self,
        settings: XMLSettings,
        parent: _Fragments,
        name: str,
        namespace: str,
    ) -> None:
        self._parent = parent
        self._name = name
        self._attributes: list[str] = [namespace] if namespace else []
        self._children: list[str] = []
        self._member_serializer = XMLShapeSerializer(
            settings, fragments=self._children, attributes=self._attributes
        )

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if exc_value is not None:
            return
        name = self._name
        self._parent.append(f"<{name}{''.join(self._attributes)}>")
        if self._children:
            self._parent.extend(self._children)
        self._parent.append(f"</{name}>")

    def before(self, schema: Schema) -> ShapeSerializer:
        return self._member_serializer

    def after(self, schema: Schema) -> None:
        pass


class _XMLListSerializer(InterceptingSerializer):
    """Serializes list entries.

    Wrapped lists write an enclosing element with one child per entry, named after
    the list's member (``member`` by default). Flattened lists write each entry
    directly into the parent, named after the containing structure's member.
    """

    def __init__(
        self,
        settings: XMLSettings,
        parent: _Fragments,
        schema: Schema,
        name: str,
        namespace: str,
    ) -> None:
        self._parent = parent
        self._name = name
        self._namespace = namespace
        self._is_flattened = schema.get_trait(XMLFlattenedTrait) is not None

        namespace_override: str | None = None
        if self._is_flattened:
            # Flattened entries use the containing member's namespace if present,
            # otherwise they fall back to the list member's own namespace.
            if namespace:
                namespace_override = namespace
            else:
                target = schema.member_target or schema
                namespace_override = _format_namespace(
                    own_trait(target.members["member"], XMLNamespaceTrait)
                )

        self._entry_serializer = XMLShapeSerializer(
            settings,
            fragments=parent,
            name_override=name if self._is_flattened else None,
            namespace_override=namespace_override,
        )

    def __enter__(self) -> Self:
        if not self._is_flattened:
            self._parent.append(f"<{self._name}{self._namespace}>")
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if exc_value is None and not self._is_flattened:
            self._parent.append(f"</{self._name}>")

    def before(self, schema: Schema) -> ShapeSerializer:
        return self._entry_serializer

    def after(self, schema: Schema) -> None:
        pass


class _XMLMapSerializer(MapSerializer):
    """Serializes map entries.

    Wrapped maps write an enclosing element containing one ``entry`` element per
    entry. Flattened maps write each entry directly into the parent, named after
    the containing structure's member. Each entry contains a key element and a
    value element, named ``key`` and ``value`` unless renamed with ``@xmlName``.
    """

    def __init__(
        self,
        settings: XMLSettings,
        parent: _Fragments,
        schema: Schema,
        name: str,
        namespace: str,
    ) -> None:
        self._parent = parent
        self._name = name
        self._namespace = namespace
        self._is_flattened = schema.get_trait(XMLFlattenedTrait) is not None

        target = schema.member_target or schema
        key_schema = target.members["key"]
        key_name = member_name(key_schema)
        key_namespace = _format_namespace(own_trait(key_schema, XMLNamespaceTrait))
        self._key_start = f"<{key_name}{key_namespace}>"
        self._key_end = f"</{key_name}>"

        if self._is_flattened:
            self._entry_start = f"<{name}{namespace}>"
            self._entry_end = f"</{name}>"
        else:
            self._entry_start = "<entry>"
            self._entry_end = "</entry>"

        self._value_serializer = XMLShapeSerializer(settings, fragments=parent)

    def __enter__(self) -> Self:
        if not self._is_flattened:
            self._parent.append(f"<{self._name}{self._namespace}>")
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if exc_value is None and not self._is_flattened:
            self._parent.append(f"</{self._name}>")

    def entry(self, key: str, value_writer: Callable[[ShapeSerializer], None]) -> None:
        self._parent.append(
            f"{self._entry_start}{self._key_start}{_escape_text(key)}{self._key_end}"
        )
        value_writer(self._value_serializer)
        self._parent.append(self._entry_end)
