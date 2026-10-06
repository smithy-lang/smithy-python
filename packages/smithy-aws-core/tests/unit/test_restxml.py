#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import pytest
from smithy_aws_core._private.restxml import RestXmlErrorInfo, parse_rest_xml_error


@pytest.mark.parametrize(
    "body, expected",
    [
        (
            b"<ErrorResponse><Error><Type>Sender</Type><Code>NoSuchThing</Code>"
            b"<Message>Not found</Message></Error><RequestId>id</RequestId>"
            b"</ErrorResponse>",
            ("NoSuchThing", "Not found", ("ErrorResponse", "Error")),
        ),
        # noErrorWrapping services (e.g. S3) send a bare <Error>.
        (
            b'<?xml version="1.0"?><Error><Code>NoSuchKey</Code></Error>',
            ("NoSuchKey", None, ("Error",)),
        ),
        (
            b'<ErrorResponse xmlns="urn:x"><Error><Code>Ns</Code></Error></ErrorResponse>',
            ("Ns", None, ("ErrorResponse", "Error")),
        ),
        (b"<Error><Message>no code</Message></Error>", (None, "no code", ("Error",))),
        (b"<ErrorResponse></ErrorResponse>", (None, None, ())),
        (b"<Other><Code>X</Code></Other>", (None, None, ())),
        (b"not xml", (None, None, ())),
        (b"", (None, None, ())),
    ],
)
def test_parse_rest_xml_error(
    body: bytes, expected: tuple[str | None, str | None, tuple[str, ...]]
) -> None:
    assert parse_rest_xml_error(body) == RestXmlErrorInfo(*expected)
