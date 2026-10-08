#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import dataclasses
import math
from collections.abc import Mapping, Sequence
from typing import cast
from xml.dom.minidom import Element, Node, parseString


def deep_equal(a: object, b: object) -> bool:
    """Structural equality for deserialized shapes that treats ``NaN == NaN``."""
    if isinstance(a, float) and isinstance(b, float):
        return a == b or (math.isnan(a) and math.isnan(b))
    if dataclasses.is_dataclass(a) and dataclasses.is_dataclass(b):
        if type(a) is not type(b):
            return False
        return all(
            deep_equal(getattr(a, f.name), getattr(b, f.name))
            for f in dataclasses.fields(a)
            if f.compare
        )
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        a_seq = cast(Sequence[object], a)
        b_seq = cast(Sequence[object], b)
        return len(a_seq) == len(b_seq) and all(
            deep_equal(x, y) for x, y in zip(a_seq, b_seq)
        )
    if isinstance(a, dict) and isinstance(b, dict):
        a_map = cast(Mapping[object, object], a)
        b_map = cast(Mapping[object, object], b)
        return a_map.keys() == b_map.keys() and all(
            deep_equal(a_map[k], b_map[k]) for k in a_map
        )
    # bool subclasses int; the subclass check would admit 1 == True without this.
    if isinstance(a, bool) != isinstance(b, bool):
        return False
    return (isinstance(a, type(b)) or isinstance(b, type(a))) and a == b  # pyright: ignore[reportUnknownArgumentType]


def xml_equal(a: bytes, b: bytes) -> bool:
    """Semantic equality for XML documents.

    Only the order of same-named sibling elements (such as list items) is
    significant; structure members, attributes, whitespace-only text, and
    whitespace around text may differ. Namespace declarations are compared as
    attributes.
    """
    return _canonical_xml(a) == _canonical_xml(b)


def _canonical_xml(document: bytes) -> object:
    root = parseString(document).documentElement  # noqa: S318
    assert root is not None  # noqa: S101
    return _canonical_element(root)


def _canonical_element(element: Element) -> object:
    text: str = ""
    children: list[tuple[str, object]] = []
    for node in element.childNodes:
        if node.nodeType in (Node.TEXT_NODE, Node.CDATA_SECTION_NODE):
            text += cast(str, node.data)  # type: ignore
        elif node.nodeType == Node.ELEMENT_NODE:
            children.append((node.tagName, _canonical_element(node)))
    # A stable sort keeps same-named siblings in document order.
    children.sort(key=lambda child: child[0])
    return (element.tagName, dict(element.attributes.items()), text.strip(), children)
