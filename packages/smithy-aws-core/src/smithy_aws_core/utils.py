#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import logging

from smithy_core.documents import Document
from smithy_core.shapes import ShapeID, ShapeType
from smithy_http.aio.interfaces import HTTPResponse

_LOGGER = logging.getLogger(__name__)

_RETRY_AFTER_HEADER = "x-amz-retry-after"


def parse_retry_after(response: HTTPResponse) -> float | None:
    """Parse the ``x-amz-retry-after`` header into a backoff duration in seconds.

    The header value is an integer number of milliseconds. Invalid or missing
    values are ignored (return ``None``) so they fall back to exponential backoff.
    """
    if _RETRY_AFTER_HEADER not in response.fields:
        return None
    raw = response.fields[_RETRY_AFTER_HEADER].as_string()
    try:
        seconds = int(raw) / 1000.0
        if seconds < 0:
            raise ValueError("Negative retry-after value")
        return seconds
    except (ValueError, TypeError, OverflowError) as error:
        _LOGGER.debug(
            "Ignoring invalid %s header value: %r. Error: %s",
            _RETRY_AFTER_HEADER,
            raw,
            error,
        )
        return None


def parse_document_discriminator(
    document: Document, default_namespace: str | None
) -> ShapeID | None:
    if document.shape_type is ShapeType.MAP:
        map_document = document.as_map()
        code = map_document.get("__type")
        if code is None:
            code = map_document.get("code")
        if code is not None and code.shape_type is ShapeType.STRING:
            return parse_error_code(code.as_string(), default_namespace)

    return None


def parse_error_code(code: str, default_namespace: str | None) -> ShapeID | None:
    if not code:
        return None

    code = code.split(":")[0]
    if "#" in code:
        return ShapeID(code)

    if not code or not default_namespace:
        return None

    return ShapeID.from_parts(name=code, namespace=default_namespace)
