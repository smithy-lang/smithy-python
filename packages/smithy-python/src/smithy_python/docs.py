# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Conversion of Smithy documentation traits to readable Python docstrings."""

from __future__ import annotations

import re
import textwrap
from html import unescape
from html.parser import HTMLParser
from typing import ClassVar


class DocumentationConverter:
    """Converts CommonMark or AWS-flavored HTML into normalized Markdown."""

    def convert(self, value: str) -> str:
        if "<" in value and re.search(r"</?[A-Za-z][^>]*>", value):
            parser = _MarkdownHTMLParser()
            parser.feed(value)
            parser.close()
            value = parser.result()
        value = unescape(value).replace("\r\n", "\n")
        value = re.sub(r"[ \t]+\n", "\n", value)
        value = re.sub(r"\n{3,}", "\n\n", value)
        return value.strip()

    def docstring(self, value: str, *, indent: int = 4) -> str:
        converted = self.convert(value).replace('"""', r"\"\"\"")
        prefix = " " * indent
        if "\n" not in converted:
            return f'{prefix}"""{converted}"""'
        return f'{prefix}"""\n{textwrap.indent(converted, prefix)}\n{prefix}"""'


class _MarkdownHTMLParser(HTMLParser):
    _BLOCKS: ClassVar[set[str]] = {
        "p",
        "div",
        "section",
        "article",
        "br",
        "li",
        "ul",
        "ol",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        self._links: list[str | None] = []
        self._code_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag in self._BLOCKS:
            self._parts.append("\n" if tag == "br" else "\n\n")
        if tag == "li":
            self._parts.append("- ")
        elif tag in {"strong", "b"}:
            self._parts.append("**")
        elif tag in {"em", "i"}:
            self._parts.append("*")
        elif tag == "code":
            self._code_depth += 1
            self._parts.append("`" if self._code_depth == 1 else "")
        elif tag == "pre":
            self._parts.append("\n```\n")
        elif tag == "a":
            self._parts.append("[")
            self._links.append(attributes.get("href"))

    def handle_endtag(self, tag: str) -> None:
        if tag in {"strong", "b"}:
            self._parts.append("**")
        elif tag in {"em", "i"}:
            self._parts.append("*")
        elif tag == "code":
            self._parts.append("`" if self._code_depth == 1 else "")
            self._code_depth = max(0, self._code_depth - 1)
        elif tag == "pre":
            self._parts.append("\n```\n")
        elif tag == "a":
            href = self._links.pop() if self._links else None
            self._parts.append(f"]({href})" if href else "]")
        elif tag in self._BLOCKS:
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        self._parts.append(data)

    def result(self) -> str:
        return "".join(self._parts)
