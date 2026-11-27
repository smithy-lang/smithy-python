# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Conversion of HTML documentation to Markdown for generated docstrings.

Smithy documentation is CommonMark, but AWS models write it as HTML. AWS
documentation uses few tags: ``p``, ``code``, ``a``, ``ul``, ``ol``, ``li``,
``b``, ``i``, ``note`` and ``important`` cover nearly all of it. The rest are
mostly placeholders such as ``<region>``, which are kept as inline code.

The output follows the Java generator's, which converts with Pandoc: lists use
``-`` items, ``note`` and ``important`` become ``Note:`` and ``Warning:``
sections, ``fullname`` is dropped, and text isn't escaped for Markdown.
"""

from __future__ import annotations

import re
import textwrap
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Final

from . import model as _model

__all__ = ["documentation_is_html", "html_to_markdown"]

_WIDTH: Final = 72
_AWS_SERVICE: Final = _model.ShapeId("aws.api", "service")

# Tags whose content is dropped, as in the Java generator.
_DROPPED: Final = frozenset({"fullname"})
_VOID: Final = frozenset({"br", "hr", "img", "wbr"})
_BLOCKS: Final = frozenset(
    {
        "p",
        "div",
        "ul",
        "ol",
        "li",
        "dl",
        "dt",
        "dd",
        "pre",
        "blockquote",
        "note",
        "important",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "table",
        "thead",
        "tbody",
        "tr",
        "td",
        "th",
        "br",
        "hr",
    }
)
_INLINE: Final = frozenset(
    {
        "a",
        "b",
        "strong",
        "i",
        "em",
        "cite",
        "u",
        "code",
        "tt",
        "samp",
        "kbd",
        "var",
        "span",
        "sup",
        "sub",
        "small",
        "img",
        "wbr",
    }
)
_KNOWN: Final = _BLOCKS | _INLINE | _DROPPED | {"html", "body", "section"}
_ADMONITIONS: Final = {"note": "Note", "important": "Warning"}
_CODE: Final = frozenset({"code", "tt", "samp", "kbd"})
# A wrapped line that starts with one of these would read as a list, a heading or
# a quote, so it's joined to the line before.
# Stands in for a space of a code span while text is wrapped. Unicode reserves it,
# so documentation never has it.
_CODE_SPACE: Final = "\U000ffffe"
_BLOCK_START: Final = re.compile(r"(?:[-*+>#]|\d+[.)])(?:\s|$)")


def documentation_is_html(service: _model.ServiceShape | None) -> bool:
    """Whether a service's documentation is HTML, as AWS services' is.

    Other Smithy documentation is CommonMark, which docstrings use as it is.
    """
    return service is not None and service.has_trait(_AWS_SERVICE)


def html_to_markdown(html: str) -> str:
    """Convert HTML documentation to Markdown wrapped at 72 columns."""
    parser = _TreeBuilder()
    parser.feed(html)
    parser.close()
    return "\n\n".join(_blocks(parser.root.children, _WIDTH)).strip()


@dataclass(slots=True)
class _Element:
    tag: str
    attributes: dict[str, str] = field(default_factory=dict[str, str])
    children: list[_Element | str] = field(default_factory=list["_Element | str"])


class _TreeBuilder(HTMLParser):
    """Builds a tree of the known tags. Others stay as literal text."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = _Element("root")
        self._stack = [self.root]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag not in _KNOWN:
            # Placeholders such as <Region> have no end tag, so they hold nothing.
            self._stack[-1].children.append(_literal(self.get_starttag_text(), tag))
            return
        if tag in _BLOCKS:
            # A block ends an open paragraph, and an item ends the item before it.
            closes = {"li": ("li",), "dt": ("dt", "dd"), "dd": ("dt", "dd")}.get(
                tag, ()
            )
            while self._stack[-1].tag == "p" or self._stack[-1].tag in closes:
                self._stack.pop()
        element = _Element(tag, {name: value or "" for name, value in attrs})
        self._stack[-1].children.append(element)
        if tag not in _VOID:
            self._stack.append(element)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in _KNOWN:
            self._stack[-1].children.append(
                _Element(tag, {name: value or "" for name, value in attrs})
            )
        else:
            self._stack[-1].children.append(_literal(self.get_starttag_text(), tag))

    def handle_endtag(self, tag: str) -> None:
        if tag not in _KNOWN:
            self._stack[-1].children.append(_Element("literal", {"text": f"</{tag}>"}))
            return
        # An end tag with no open start tag is ignored.
        for index in range(len(self._stack) - 1, 0, -1):
            if self._stack[index].tag == tag:
                del self._stack[index:]
                return

    def handle_data(self, data: str) -> None:
        self._stack[-1].children.append(data)


def _literal(text: str | None, tag: str) -> _Element:
    return _Element("literal", {"text": text or f"<{tag}>"})


def _blocks(children: list[_Element | str], width: int) -> list[str]:
    """Render children as Markdown blocks, grouping inline content into paragraphs."""
    blocks: list[str] = []
    inline: list[str] = []

    def flush() -> None:
        text = re.sub(r"\s+", " ", "".join(inline)).strip()
        inline.clear()
        if text:
            blocks.append(_wrap(text, width))

    for child in children:
        if isinstance(child, str) or child.tag not in _BLOCKS:
            inline.append(_inline(child))
            continue
        flush()
        blocks.extend(_block(child, width))
    flush()
    return [block for block in blocks if block]


def _block(element: _Element, width: int) -> list[str]:
    match element.tag:
        case "ul" | "ol":
            return [_list(element, width)]
        case "dl":
            return _definitions(element, width)
        case "pre":
            text = _text(element).strip("\n")
            fence = "````" if "```" in text else "```"
            return [f"{fence}\n{text}\n{fence}"] if text.strip() else []
        case "note" | "important":
            body = _blocks(element.children, width - 4)
            if not body:
                return []
            return [f"{_ADMONITIONS[element.tag]}:\n" + _indent("\n\n".join(body), 4)]
        case "blockquote":
            body = "\n\n".join(_blocks(element.children, width - 2))
            return ["\n".join(f"> {line}".rstrip() for line in body.split("\n"))]
        case "h1" | "h2" | "h3" | "h4" | "h5" | "h6":
            text = re.sub(r"\s+", " ", _inline_children(element)).strip()
            return [_wrap(f"**{text}**", width)] if text else []
        case "tr":
            cells = [
                re.sub(r"\s+", " ", _inline_children(cell)).strip()
                for cell in element.children
                if isinstance(cell, _Element)
            ]
            return [_wrap(" | ".join(cell for cell in cells if cell), width)]
        case "br" | "hr":
            return []
        case _:
            return _blocks(element.children, width)


def _list(element: _Element, width: int) -> str:
    items = [
        child
        for child in element.children
        if isinstance(child, _Element) and child.tag == "li"
    ]
    rendered: list[tuple[str, int]] = []
    for index, item in enumerate(items, 1):
        marker = "- " if element.tag == "ul" else f"{index}. "
        body = _blocks(item.children, width - len(marker))
        if body:
            text = _indent("\n\n".join(body), len(marker))[len(marker) :]
            rendered.append((marker + text, len(body)))
    # A list whose items are each one block is tight, like Pandoc writes it.
    separator = "\n" if all(count == 1 for _, count in rendered) else "\n\n"
    return separator.join(text for text, _ in rendered)


def _definitions(element: _Element, width: int) -> list[str]:
    blocks: list[str] = []
    for child in element.children:
        if not isinstance(child, _Element):
            continue
        if child.tag == "dt":
            text = re.sub(r"\s+", " ", _inline_children(child)).strip()
            if text:
                blocks.append(_wrap(text, width))
        elif child.tag == "dd":
            body = "\n\n".join(_blocks(child.children, width - 4))
            if body:
                blocks.append(":   " + _indent(body, 4)[4:])
    return blocks


def _inline(node: _Element | str) -> str:
    if isinstance(node, str):
        return node
    tag = node.tag
    if tag in _DROPPED:
        return ""
    if tag == "literal":
        return f"`{node.attributes['text']}`"
    if tag in _CODE:
        return _code(re.sub(r"\s+", " ", _text(node)))
    content = _inline_children(node)
    match tag:
        case "b" | "strong":
            return _emphasis(content, "**")
        case "i" | "em" | "cite" | "var":
            return _emphasis(content, "*")
        case "a":
            href = node.attributes.get("href", "").strip()
            text = re.sub(r"\s+", " ", content).strip()
            if not href:
                return content
            return f"[{text or href}]({href})"
        case "img" | "wbr":
            return ""
        case _:
            return content


def _inline_children(element: _Element) -> str:
    return "".join(_inline(child) for child in element.children)


def _text(element: _Element) -> str:
    """The text of an element as written, with placeholder tags kept."""
    parts: list[str] = []
    for child in element.children:
        if isinstance(child, str):
            parts.append(child)
        elif child.tag == "literal":
            parts.append(child.attributes["text"])
        elif child.tag not in _DROPPED:
            parts.append(_text(child))
    return "".join(parts)


def _code(text: str) -> str:
    if not text.strip():
        return text
    fence = "`"
    while fence in text:
        fence += "`"
    padding = " " if text.startswith("`") or text.endswith("`") else ""
    # Wrapping keeps a code span on one line, as Pandoc does.
    return f"{fence}{padding}{text}{padding}{fence}".replace(" ", _CODE_SPACE)


def _emphasis(content: str, marker: str) -> str:
    core = content.strip()
    if not core:
        return content
    lead = content[: len(content) - len(content.lstrip())]
    trail = content[len(content.rstrip()) :]
    return f"{lead}{marker}{core}{marker}{trail}"


def _wrap(text: str, width: int) -> str:
    lines = textwrap.wrap(
        text,
        width=max(width, 20),
        break_long_words=False,
        break_on_hyphens=False,
    )
    joined: list[str] = []
    for line in lines:
        if joined and _BLOCK_START.match(line):
            joined[-1] += " " + line
        else:
            joined.append(line)
    return "\n".join(joined).replace(_CODE_SPACE, " ")


def _indent(text: str, size: int) -> str:
    pad = " " * size
    return "\n".join(pad + line if line else line for line in text.split("\n"))
