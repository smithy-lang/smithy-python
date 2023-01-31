import json

import pytest

from smithy_python._private.http import Response
from smithy_python.interfaces.http import HeadersList
from smithy_python.protocolutils import RestJsonErrorInfo, parse_rest_json_error_info
from smithy_python.types import Document


class _AsyncReader:
    def __init__(self, body: str):
        self._body: bytes = body.encode("utf-8")

    async def read(self, size: int = -1) -> bytes:
        result: bytes = self._body
        if size <= 0:
            self._body = b""
        else:
            result = self._body[:size]
            self._body = self._body[size:]
        return result


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
    headers: HeadersList, body: Document, expected: RestJsonErrorInfo
) -> None:
    response = Response(status_code=400, headers=headers, body=_AsyncReader(json.dumps(body)))
    actual = await parse_rest_json_error_info(response)
    assert actual == expected
