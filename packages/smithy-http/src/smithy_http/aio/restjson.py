#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from smithy_core.aio.utils import read_streaming_blob_async

from ..interfaces import HTTPResponse
from ..restjson import (
    RestJsonErrorInfo,
    _parse_rest_json_error_info,  # pyright: ignore[reportPrivateUsage]
)

__all__ = ["parse_rest_json_error_info_async"]


async def parse_rest_json_error_info_async(
    http_response: HTTPResponse, check_body: bool = True
) -> RestJsonErrorInfo:
    """Parses generic RestJson error info from an HTTP response.

    :param http_response: The HTTP response to parse.
    :param check_body: Whether to check the body for the code / message.
    :returns: The parsed error information.
    """
    body = await read_streaming_blob_async(http_response.body) if check_body else None
    return _parse_rest_json_error_info(http_response.fields, body)
