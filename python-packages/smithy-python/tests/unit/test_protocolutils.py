# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

import json
from collections.abc import AsyncIterator

import pytest

from smithy_python._private import tuples_to_fields
from smithy_python._private.http import HTTPResponse
from smithy_python.async_utils import async_list
from smithy_python.protocolutils import (
    RestJsonErrorInfo,
    parse_rest_json_error_code,
    parse_rest_json_error_info,
)
from smithy_python.types import Document


@pytest.mark.parametrize(
    "headers, body, expected",
    [
        ([], {}, RestJsonErrorInfo("unknown", "Unknown", {})),
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
            RestJsonErrorInfo("unknown", "bar", {"message": "bar"}),
        ),
        (
            [],
            {"error_message": "bar"},
            RestJsonErrorInfo("unknown", "bar", {"error_message": "bar"}),
        ),
        (
            [],
            {"errormessage": "bar"},
            RestJsonErrorInfo("unknown", "bar", {"errormessage": "bar"}),
        ),
        (
            [],
            {"mEsSaGe": "bar"},
            RestJsonErrorInfo("unknown", "bar", {"mEsSaGe": "bar"}),
        ),
        (
            [("x-amzn-errortype", "foo")],
            {"message": "bar"},
            RestJsonErrorInfo("foo", "bar", {"message": "bar"}),
        ),
    ],
)
async def test_parse_rest_json_error_info(
    headers: list[tuple[str, str]], body: Document, expected: RestJsonErrorInfo
) -> None:
    response = HTTPResponse(
        status=400,
        fields=tuples_to_fields(headers),
        body=async_list([json.dumps(body).encode()]),
    )
    error_info = await parse_rest_json_error_code(response)
    actual = await parse_rest_json_error_info(response, error_info)
    assert actual == expected


class _ExceptionThrowingBody:
    def __aiter__(self) -> AsyncIterator[bytes]:
        raise Exception("Body unexpectedly accessed")


@pytest.mark.parametrize(
    "headers, expected",
    [
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
async def test_parse_rest_json_error_info_without_accessing_body(
    headers: list[tuple[str, str]], expected: RestJsonErrorInfo
) -> None:
    response = HTTPResponse(
        status=400, fields=tuples_to_fields(headers), body=_ExceptionThrowingBody()
    )
    actual = await parse_rest_json_error_code(response)
    assert actual == expected


@pytest.mark.parametrize(
    "headers, body, expected",
    [
        ([], {"code": "foo"}, RestJsonErrorInfo("foo", "Unknown", {"code": "foo"})),
        (
            [],
            {"code": "bar", "other": "other"},
            RestJsonErrorInfo("bar", "Unknown", {"code": "bar", "other": "other"}),
        ),
        (
            [("x-amzn-something", "com.example#oops")],
            {"code": "baz", "other": {"test": "thingy"}},
            RestJsonErrorInfo(
                "baz", "Unknown", {"code": "baz", "other": {"test": "thingy"}}
            ),
        ),
        ([], {}, RestJsonErrorInfo("unknown", "Unknown", {})),
    ],
)
async def test_parse_rest_json_error_code_from_body_when_not_in_fields(
    headers: list[tuple[str, str]], body: Document, expected: RestJsonErrorInfo
) -> None:
    response = HTTPResponse(
        status=400,
        fields=tuples_to_fields(headers),
        body=async_list([json.dumps(body).encode()]),
    )
    actual = await parse_rest_json_error_code(response)
    assert actual == expected
