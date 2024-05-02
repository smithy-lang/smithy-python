#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import json

from smithy_core.documents import DocumentValue
from smithy_core.utils import expect_type

from ..restjson import _REST_JSON_CODE_HEADER  # pyright: ignore[reportPrivateUsage]
from ..restjson import _REST_JSON_CODE_KEYS  # pyright: ignore[reportPrivateUsage]
from ..restjson import _REST_JSON_MESSAGE_KEYS  # pyright: ignore[reportPrivateUsage]
from ..restjson import RestJsonErrorInfo
from .interfaces import HTTPResponse


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
    json_body: dict[str, DocumentValue] | None = None

    for field in http_response.fields:
        if field.name.lower() == _REST_JSON_CODE_HEADER:
            code = field.values[0]

    if check_body:
        if body := await http_response.consume_body_async():
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
