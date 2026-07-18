# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from smithy_python.docs import DocumentationConverter


def test_converts_aws_html_to_markdown() -> None:
    value = DocumentationConverter().convert(
        '<p>Use <b>strong</b> text and <a href="https://example.com">a link</a>.</p>'
    )
    assert value == "Use **strong** text and [a link](https://example.com)."
