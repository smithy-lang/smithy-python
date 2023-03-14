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
    checking the most common locations and is intended for use with exceptions that
    either didn't model the message or which are unknown.
    """

    json_body: Document | None = None
    """The HTTP response body parsed as JSON."""


async def parse_rest_json_error_code(http_response: HTTPResponse) -> RestJsonErrorInfo:
    """Parses RestJson error code from an HTTP response.

    :param http_response: The HTTP response to parse.
    :returns: The parsed error info.
    """
    code: str | None = None
    message: str | None = None
    json_body: Document | None = None

    for field in http_response.fields:
        if field.name.lower() == _REST_JSON_CODE_HEADER:
            code = field.values[0]

    # If the error code could not be found in the http response fields then it could
    # be set as a top level field of the body
    if not code:
        code, message, json_body = await _parse_json_body(http_response)

    # Normalize the error code. Some services may try to send a fully-qualified shape
    # ID or a URI, but we don't want to include those.
    if code:
        if "#" in code:
            code = code.split("#")[1]
        code = code.split(":")[0]
        code = code.lower()

    return RestJsonErrorInfo(code or "unknown", message or "Unknown", json_body)


async def parse_rest_json_error_info(
    http_response: HTTPResponse,
    error_info: RestJsonErrorInfo,
) -> RestJsonErrorInfo:
    """Parses generic RestJson error info from an HTTP response.

    :param http_response: The HTTP response to parse.
    :param error_info: existing error info
    :returns: The parsed error information.
    """
    return await _parse_json_body(http_response, *error_info)


async def _parse_json_body(
    http_response: HTTPResponse,
    code: str | None = None,
    message: str | None = None,
    json_body: dict[str, Document] | None = None
) -> RestJsonErrorInfo:
    if body := await http_response.consume_body():
        json_body = json.loads(body)

    if json_body:
        for key, value in json_body.items():
            key_lower = key.lower()
            if (not code or code == "unknown") and key_lower in _REST_JSON_CODE_KEYS:
                code = expect_type(str, value)
            if (not message or message == "Unknown") and key_lower in _REST_JSON_MESSAGE_KEYS:
                message = expect_type(str, value)

    return RestJsonErrorInfo(code or "unknown", message or "Unknown", json_body)
