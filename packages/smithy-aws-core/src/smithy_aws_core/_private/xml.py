#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""Helpers shared by the XML-based AWS protocols."""

from typing import TYPE_CHECKING
from xml.etree.ElementTree import Element, ParseError, fromstring

from smithy_core.codecs import Codec
from smithy_core.deserializers import ShapeDeserializer
from smithy_core.exceptions import MissingDependencyError
from smithy_core.interfaces import BytesReader, BytesWriter
from smithy_core.serializers import ShapeSerializer

try:
    from smithy_xml import XMLCodec

    _HAS_XML = True
except ImportError:
    _HAS_XML = False  # type: ignore

if TYPE_CHECKING:
    from smithy_xml import XMLCodec


def assert_xml() -> None:
    if not _HAS_XML:
        raise MissingDependencyError(
            "Attempted to use XML codec, but smithy-xml is not installed."
        )


def local_name(tag: str) -> str:
    """Strip namespace URI from an element tag: {uri}local -> local."""
    if tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


def find_child(element: Element, name: str) -> Element | None:
    """Return the first child element whose local name matches ``name``."""
    for child in element:
        if local_name(child.tag) == name:
            return child
    return None


def parse_xml_root(body: bytes) -> Element | None:
    """Parse the root element of an XML document, or None if it isn't valid XML."""
    try:
        return fromstring(body)  # noqa: S314
    except ParseError:
        return None


def parse_xml_error_code(body: bytes, wrapper_elements: tuple[str, ...]) -> str | None:
    """Parse the ``Code`` field from an XML error response.

    :param body: The response body.
    :param wrapper_elements: The elements enclosing the error fields, outermost
        first. The root element must match the first wrapper.
    """
    element = parse_xml_root(body)
    if element is None:
        return None

    if wrapper_elements:
        if local_name(element.tag) != wrapper_elements[0]:
            return None
        for wrapper in wrapper_elements[1:]:
            next_element = find_child(element, wrapper)
            if next_element is None:
                return None
            element = next_element

    code_element = find_child(element, "Code")
    return code_element.text if code_element is not None else None


def parse_rest_xml_error(body: bytes) -> tuple[str | None, tuple[str, ...]]:
    """Parse the error code and wrapper elements from a restXml error response.

    Error responses are either wrapped, ``<ErrorResponse><Error>...``, or bare,
    ``<Error>...``. Both forms are detected from the body itself.

    :param body: The response body.
    :returns: The error code, if found, and the wrapper elements enclosing the
        error fields. The wrapper elements are empty if the body isn't an XML
        error response.
    """
    root = parse_xml_root(body) if body else None
    if root is None:
        return None, ()

    root_name = local_name(root.tag)
    if root_name == "ErrorResponse":
        wrapper_elements = ("ErrorResponse", "Error")
        error = find_child(root, "Error")
    elif root_name == "Error":
        wrapper_elements = ("Error",)
        error = root
    else:
        return None, ()

    if error is None:
        return None, wrapper_elements
    code_element = find_child(error, "Code")
    if code_element is None or not code_element.text:
        return None, wrapper_elements
    return code_element.text, wrapper_elements


class WrappedXMLCodec(Codec):
    """An XML codec whose deserializers first consume protocol wrapper elements.

    This lets HTTP binding deserializers, which create deserializers without any
    extra arguments, read error fields nested inside e.g.
    ``<ErrorResponse><Error>``.
    """

    def __init__(self, codec: "XMLCodec", wrapper_elements: tuple[str, ...]) -> None:
        self._codec = codec
        self._wrapper_elements = wrapper_elements

    @property
    def media_type(self) -> str:
        return self._codec.media_type

    def create_serializer(self, sink: BytesWriter) -> ShapeSerializer:
        return self._codec.create_serializer(sink)

    def create_deserializer(self, source: bytes | BytesReader) -> ShapeDeserializer:
        return self._codec.create_deserializer(
            source, wrapper_elements=self._wrapper_elements
        )
