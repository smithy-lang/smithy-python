#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import pytest
from smithy_aws_core.utils import (
    parse_document_discriminator,
    parse_error_code,
    parse_retry_after,
)
from smithy_core.documents import Document
from smithy_core.shapes import ShapeID
from smithy_http import Field, Fields
from smithy_http.aio import HTTPResponse


@pytest.mark.parametrize(
    "document, expected",
    [
        ({"__type": "FooError"}, "com.test#FooError"),
        ({"__type": "com.test#FooError"}, "com.test#FooError"),
        (
            {
                "__type": "FooError:http://internal.amazon.com/coral/com.amazon.coral.validate/"
            },
            "com.test#FooError",
        ),
        (
            {
                "__type": "com.test#FooError:http://internal.amazon.com/coral/com.amazon.coral.validate"
            },
            "com.test#FooError",
        ),
        ({"code": "FooError"}, "com.test#FooError"),
        ({"code": "com.test#FooError"}, "com.test#FooError"),
        (
            {
                "code": "FooError:http://internal.amazon.com/coral/com.amazon.coral.validate/"
            },
            "com.test#FooError",
        ),
        (
            {
                "code": "com.test#FooError:http://internal.amazon.com/coral/com.amazon.coral.validate"
            },
            "com.test#FooError",
        ),
        ({"__type": "FooError", "code": "BarError"}, "com.test#FooError"),
        ("FooError", None),
        ({"__type": None}, None),
        ({"__type": ""}, None),
        ({"__type": ":"}, None),
    ],
)
def test_aws_json_document_discriminator(
    document: dict[str, str], expected: ShapeID | None
) -> None:
    actual = parse_document_discriminator(Document(document), "com.test")
    assert actual == expected


@pytest.mark.parametrize(
    "code, expected",
    [
        ("FooError", "com.test#FooError"),
        (
            "FooError:http://internal.amazon.com/coral/com.amazon.coral.validate/",
            "com.test#FooError",
        ),
        (
            "com.test#FooError:http://internal.amazon.com/coral/com.amazon.coral.validate",
            "com.test#FooError",
        ),
        ("", None),
        (":", None),
    ],
)
def test_parse_error_code(code: str, expected: ShapeID | None) -> None:
    actual = parse_error_code(code, "com.test")
    assert actual == expected


def test_parse_error_code_without_default_namespace() -> None:
    actual = parse_error_code("FooError", None)
    assert actual is None


@pytest.mark.parametrize(
    "header_value, expected",
    [
        ("1500", 1.5),
        ("0", 0.0),
        ("20", 0.02),
        ("invalid", None),
        ("1.5", None),
        ("-100", None),
        ("", None),
    ],
)
def test_parse_retry_after(header_value: str, expected: float | None) -> None:
    response = HTTPResponse(
        status=500,
        fields=Fields([Field(name="x-amz-retry-after", values=[header_value])]),
    )
    assert parse_retry_after(response) == expected


def test_parse_retry_after_missing_header() -> None:
    response = HTTPResponse(status=500, fields=Fields())
    assert parse_retry_after(response) is None


def test_parse_retry_after_ignores_standard_retry_after_header() -> None:
    # The standard HTTP Retry-After header must be ignored.
    response = HTTPResponse(
        status=503,
        fields=Fields([Field(name="Retry-After", values=["120"])]),
    )
    assert parse_retry_after(response) is None
