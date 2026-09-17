#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import pytest
from smithy_aws_core.utils import (
    parse_document_discriminator,
    parse_error_code,
    parse_response_metadata,
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
        ("com.other#FooError", "com.other#FooError"),
        (
            "com.other#FooError:http://internal.amazon.com/coral/com.amazon.coral.validate",
            "com.other#FooError",
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


@pytest.mark.parametrize(
    "headers, expected_request_id",
    [
        # Most services send x-amzn-requestid.
        ([("x-amzn-requestid", "rid-amzn")], "rid-amzn"),
        # Services in the Amazon S3 lineage send x-amz-request-id instead.
        ([("x-amz-request-id", "rid-amz")], "rid-amz"),
        # When both are present, x-amzn-requestid takes precedence.
        (
            [("x-amz-request-id", "rid-amz"), ("x-amzn-requestid", "rid-amzn")],
            "rid-amzn",
        ),
        # An empty value is treated as absent rather than as an empty ID.
        ([("x-amzn-requestid", "")], None),
        # Falls through to the next candidate when the preferred one is empty.
        ([("x-amzn-requestid", ""), ("x-amz-request-id", "rid-amz")], "rid-amz"),
        ([], None),
    ],
)
def test_parse_response_metadata_request_id(
    headers: list[tuple[str, str]], expected_request_id: str | None
) -> None:
    response = HTTPResponse(
        status=200,
        fields=Fields([Field(name=name, values=[value]) for name, value in headers]),
    )
    assert parse_response_metadata(response).request_id == expected_request_id


@pytest.mark.parametrize(
    "headers, expected",
    [
        ([("x-amz-id-2", "host-id-2")], "host-id-2"),
        ([("x-amz-id-2", "")], None),
    ],
)
def test_parse_response_metadata_extended_request_id(
    headers: list[tuple[str, str]], expected: str | None
) -> None:
    response = HTTPResponse(
        status=200,
        fields=Fields([Field(name=name, values=[value]) for name, value in headers]),
    )
    assert parse_response_metadata(response).extended_request_id == expected


def test_parse_response_metadata_reads_all_members() -> None:
    response = HTTPResponse(
        status=503,
        fields=Fields(
            [
                Field(name="x-amzn-requestid", values=["rid"]),
                Field(name="x-amz-id-2", values=["host-id-2"]),
            ]
        ),
    )
    metadata = parse_response_metadata(response)
    assert metadata.request_id == "rid"
    assert metadata.extended_request_id == "host-id-2"
    assert metadata.http_status_code == 503


def test_parse_response_metadata_ignores_unrelated_headers() -> None:
    response = HTTPResponse(
        status=200,
        fields=Fields(
            [
                Field(name="x-amz-retry-after", values=["100"]),
                Field(name="request-id", values=["not-the-aws-header"]),
            ]
        ),
    )
    metadata = parse_response_metadata(response)
    assert metadata.request_id is None
    assert metadata.extended_request_id is None


def test_parse_response_metadata_reads_the_first_of_repeated_values() -> None:
    response = HTTPResponse(
        status=200,
        fields=Fields(
            [
                Field(name="x-amzn-requestid", values=["rid-1", "rid-2"]),
                Field(name="x-amz-id-2", values=["host-1", "host-2"]),
            ]
        ),
    )
    metadata = parse_response_metadata(response)
    assert metadata.request_id == "rid-1"
    assert metadata.extended_request_id == "host-1"
