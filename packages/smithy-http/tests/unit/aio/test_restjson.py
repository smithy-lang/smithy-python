#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import json
from collections.abc import AsyncIterator

import pytest
from smithy_core.aio.utils import async_list
from smithy_core.documents import DocumentValue
from smithy_http import tuples_to_fields
from smithy_http.aio import HTTPResponse
from smithy_http.aio.restjson import parse_rest_json_error_info
from smithy_http.restjson import RestJsonErrorInfo


@pytest.mark.parametrize(
    "headers, body, expected",
    [
        ([], {}, RestJsonErrorInfo("Unknown", "Unknown", {})),
        ([("x-amzn-errortype", "foo")], {}, RestJsonErrorInfo("foo", "Unknown", {})),
        ([("X-Amzn-Errortype", "foo")], {}, RestJsonErrorInfo("foo", "Unknown", {})),
        (
            [("x-amzn-errortype", "com.example#foo")],
            {},
            RestJsonErrorInfo("foo", "Unknown", {}),
        ),
        (
            [("x-amzn-errortype", "foo:https://example.com/")],
            {},
            RestJsonErrorInfo("foo", "Unknown", {}),
        ),
        (
            [("x-amzn-errortype", "com.example#foo:https://example.com/")],
            {},
            RestJsonErrorInfo("foo", "Unknown", {}),
        ),
        (
            [],
            {"__type": "foo"},
            RestJsonErrorInfo("foo", "Unknown", {"__type": "foo"}),
        ),
        ([], {"code": "foo"}, RestJsonErrorInfo("foo", "Unknown", {"code": "foo"})),
        (
            [("X-Amzn-Errortype", "foo")],
            {"__type": "baz"},
            RestJsonErrorInfo("foo", "Unknown", {"__type": "baz"}),
        ),
        (
            [],
            {"message": "bar"},
            RestJsonErrorInfo("Unknown", "bar", {"message": "bar"}),
        ),
        (
            [],
            {"error_message": "bar"},
            RestJsonErrorInfo("Unknown", "bar", {"error_message": "bar"}),
        ),
        (
            [],
            {"errormessage": "bar"},
            RestJsonErrorInfo("Unknown", "bar", {"errormessage": "bar"}),
        ),
        (
            [],
            {"mEsSaGe": "bar"},
            RestJsonErrorInfo("Unknown", "bar", {"mEsSaGe": "bar"}),
        ),
        (
            [("x-amzn-errortype", "foo")],
            {"message": "bar"},
            RestJsonErrorInfo("foo", "bar", {"message": "bar"}),
        ),
    ],
)
async def test_parse_rest_json_error_info(
    headers: list[tuple[str, str]], body: DocumentValue, expected: RestJsonErrorInfo
) -> None:
    response = HTTPResponse(
        status=400,
        fields=tuples_to_fields(headers),
        body=async_list([json.dumps(body).encode()]),
    )
    actual = await parse_rest_json_error_info(response)
    assert actual == expected


class _ExceptionThrowingBody:
    def __aiter__(self) -> AsyncIterator[bytes]:
        raise Exception("Body unexpectedly accessed")


@pytest.mark.parametrize(
    "headers, expected",
    [
        ([], RestJsonErrorInfo("Unknown", "Unknown", None)),
        ([("x-amzn-errortype", "foo")], RestJsonErrorInfo("foo", "Unknown", None)),
        ([("X-Amzn-Errortype", "foo")], RestJsonErrorInfo("foo", "Unknown", None)),
        (
            [("x-amzn-errortype", "com.example#foo")],
            RestJsonErrorInfo("foo", "Unknown", None),
        ),
        (
            [("x-amzn-errortype", "foo:https://example.com/")],
            RestJsonErrorInfo("foo", "Unknown", None),
        ),
        (
            [("x-amzn-errortype", "com.example#foo:https://example.com/")],
            RestJsonErrorInfo("foo", "Unknown", None),
        ),
    ],
)
async def test_parse_rest_json_error_info_without_body(
    headers: list[tuple[str, str]], expected: RestJsonErrorInfo
) -> None:
    response = HTTPResponse(
        status=400, fields=tuples_to_fields(headers), body=_ExceptionThrowingBody()
    )
    actual = await parse_rest_json_error_info(response, check_body=False)
    assert actual == expected


async def test_parse_error_info_non_json_body() -> None:
    response = HTTPResponse(
        status=400,
        fields=tuples_to_fields([]),
        body=async_list(
            [
                (
                    b"<html>\r\n<head><title>400 Bad Request</title></head>\r\n"
                    b"<body>\r\n<center><h1>400 Bad Request</h1></center>\r\n</body>\r\n</html>\r\n"
                )
            ]
        ),
    )
    expected = RestJsonErrorInfo("Unknown", "Unknown", None)
    actual = await parse_rest_json_error_info(response, check_body=True)
    assert actual == expected
