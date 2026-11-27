# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0


from typing import Any

import pytest
from smithy_python._docs import documentation_is_html, html_to_markdown
from smithy_python.model import ServiceShape, ShapeId, load_model


@pytest.mark.parametrize(
    ("html", "markdown"),
    [
        ("<p>One.</p> <p>Two.</p>", "One.\n\nTwo."),
        (
            "<p>Use <code>Table</code>, <b>always</b> and <i>now</i>.</p>",
            "Use `Table`, **always** and *now*.",
        ),
        (
            '<p>See <a href=" https://example.com ">the guide</a>.</p>',
            "See [the guide](https://example.com).",
        ),
        ("<ul><li>a</li><li>b</li></ul>", "- a\n- b"),
        (
            "<ul><li><p>a</p><ul><li>c</li></ul></li><li><p>b</p></li></ul>",
            "- a\n\n  - c\n\n- b",
        ),
        ("<ol><li>a</li><li>b</li></ol>", "1. a\n2. b"),
        ("<note><p>Careful.</p></note>", "Note:\n    Careful."),
        ("<important><p>Very.</p></important>", "Warning:\n    Very."),
        ("<dl><dt>Term</dt><dd><p>Meaning</p></dd></dl>", "Term\n\n:   Meaning"),
        ("<fullname>Amazon Thing</fullname><p>Text.</p>", "Text."),
        (
            "<p>In <code>arn:aws:s3:<Region>:x</code> or arn:<Region>.</p>",
            "In `arn:aws:s3:<Region>:x` or arn:`<Region>`.",
        ),
        ("<p>A &amp; B &lt; C</p>", "A & B < C"),
        ("<pre>x = 1\n  y</pre>", "```\nx = 1\n  y\n```"),
        ("<p>Unclosed <b>bold</p><p>next</p>", "Unclosed **bold**\n\nnext"),
        # Docs with no tags are kept, so their lines and lists stay as written.
        (
            "Values:\n\n1. One\n2. Two\n\nMore text\non two lines.",
            "Values:\n\n1. One\n2. Two\n\nMore text\non two lines.",
        ),
        # In HTML, a blank line in text starts a paragraph.
        ("<p>One\n\nTwo <b>b</b></p>", "One\n\nTwo **b**"),
        ("<b>Lead</b> text\n\nnext\nline", "**Lead** text\n\nnext line"),
        ("<code>a`b</code>", "``a`b``"),
    ],
)
def test_html_to_markdown(html: str, markdown: str) -> None:
    assert html_to_markdown(html) == markdown


def test_wrapping_keeps_code_spans_and_list_indents() -> None:
    words = " ".join(["word"] * 20)
    result = html_to_markdown(
        f"<ul><li>{words} <code>a b c d e f g h</code> {words}</li></ul>"
    )
    lines = result.split("\n")
    assert all(len(line) <= 72 for line in lines)
    assert lines[0].startswith("- ")
    assert all(line.startswith("  ") for line in lines[1:])
    assert "`a b c d e f g h`" in result


def test_wrapping_never_starts_a_line_with_a_list_marker() -> None:
    result = html_to_markdown("<p>" + "word " * 13 + "- dash then more words</p>")
    assert not any(line.startswith("- ") for line in result.split("\n"))


def test_only_aws_services_have_html_documentation() -> None:
    def service(*traits: str) -> ServiceShape:
        trait_values: dict[str, Any] = {trait: {} for trait in traits}
        shapes: dict[str, Any] = {
            "example#Service": {"type": "service", "traits": trait_values}
        }
        model = load_model({"smithy": "2.0", "shapes": shapes})
        return model.expect_shape(ShapeId("example", "Service"), ServiceShape)

    assert documentation_is_html(service("aws.api#service"))
    assert not documentation_is_html(service())
    assert not documentation_is_html(None)
