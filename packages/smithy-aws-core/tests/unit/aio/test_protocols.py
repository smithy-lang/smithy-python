#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from unittest.mock import Mock

import pytest
from smithy_aws_core.aio.protocols import AWSErrorIdentifier
from smithy_core.schemas import APIOperation, Schema
from smithy_core.shapes import ShapeID, ShapeType
from smithy_http import Fields, tuples_to_fields
from smithy_http.aio import HTTPResponse


@pytest.mark.parametrize(
    "header, expected",
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
        (None, None),
    ],
)
def test_aws_error_identifier(header: str | None, expected: ShapeID | None) -> None:
    fields = Fields()
    if header is not None:
        fields = tuples_to_fields([("x-amzn-errortype", header)])
    http_response = HTTPResponse(status=500, fields=fields)

    operation = Mock(spec=APIOperation)
    operation.schema = Schema(
        id=ShapeID("com.test#TestOperation"), shape_type=ShapeType.OPERATION
    )

    error_identifier = AWSErrorIdentifier()
    actual = error_identifier.identify(operation=operation, response=http_response)

    assert actual == expected
