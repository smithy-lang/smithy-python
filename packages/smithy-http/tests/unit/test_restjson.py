#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from io import BytesIO

from smithy_http import HTTPResponse, tuples_to_fields
from smithy_http.restjson import RestJsonErrorInfo, parse_rest_json_error_info


def test_parse_rest_json_error_info_reads_sync_body() -> None:
    response = HTTPResponse(
        status=400,
        fields=tuples_to_fields([("x-amzn-errortype", "com.example#foo")]),
        body=BytesIO(b'{"message": "bar"}'),
    )
    actual = parse_rest_json_error_info(response)
    assert actual == RestJsonErrorInfo("foo", "bar", {"message": "bar"})


def test_parse_rest_json_error_info_skips_body() -> None:
    response = HTTPResponse(
        status=400,
        fields=tuples_to_fields([]),
        body=BytesIO(b'{"code": "foo"}'),
    )
    actual = parse_rest_json_error_info(response, check_body=False)
    assert actual == RestJsonErrorInfo("Unknown", "Unknown", None)
