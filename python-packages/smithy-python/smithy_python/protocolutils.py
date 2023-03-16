import json
from typing import NamedTuple

from .interfaces.http import HTTPResponse
from .types import Document
from .utils import expect_type

_REST_JSON_CODE_HEADER = "x-amzn-errortype"

_REST_JSON_CODE_KEYS = {"__type", "code"}

_REST_JSON_MESSAGE_KEYS = {"message", "errormessage", "error_message"}


class RestJsonErrorInfo(NamedTuple):
    """Generic error information from a RestJson protocol error."""

    code: str
    """The error code."""

    message: str
    """The generic error message.

    A modeled error may have the error bound somewhere else. This is based off of
    checking the most common locations and is intended for use with excpetions that
    either didn't model the message or which are unknown.
    """

    json_body: dict[str, Document] | None = None
    """The HTTP response body parsed as JSON."""


async def parse_rest_json_error_info(
    http_response: HTTPResponse, check_body: bool = True
) -> RestJsonErrorInfo:
    """Parses generic RestJson error info from an HTTP response.

    :param http_response: The HTTP response to parse.
    :param check_body: Whether to check the body for the code / message.
    :returns: The parsed error information.
    """
    code: str | None = None
    message: str | None = None
    json_body: dict[str, Document] | None = None

    for field in http_response.fields:
        if field.name.lower() == _REST_JSON_CODE_HEADER:
            code = field.values[0]

    if check_body:
        if body := await http_response.consume_body():
            json_body = json.loads(body)

        if json_body:
            for key, value in json_body.items():
                key_lower = key.lower()
                if not code and key_lower in _REST_JSON_CODE_KEYS:
                    code = expect_type(str, value)
                if not message and key_lower in _REST_JSON_MESSAGE_KEYS:
                    message = expect_type(str, value)

    # Normalize the error code. Some services may try to send a fully-qualified shape
    # ID or a URI, but we don't want to include those.
    if code:
        if "#" in code:
            code = code.split("#")[1]
        code = code.split(":")[0]

    return RestJsonErrorInfo(code or "Unknown", message or "Unknown", json_body)
