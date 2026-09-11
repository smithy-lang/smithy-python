#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""Helpers for reading awsQuery response bodies that are not shape-modeled."""

from xml.etree.ElementTree import Element


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
