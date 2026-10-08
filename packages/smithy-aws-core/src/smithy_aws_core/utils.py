#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import logging

from smithy_core.documents import Document
from smithy_core.response import ResponseMetadata
from smithy_core.shapes import ShapeID, ShapeType
from smithy_http.aio.interfaces import HTTPResponse
from smithy_http.interfaces import Field

_LOGGER = logging.getLogger(__name__)

_RETRY_AFTER_HEADER = "x-amz-retry-after"

_REQUEST_ID_HEADERS = ("x-amzn-requestid", "x-amz-request-id")
"""Headers that may carry the request ID, in order of preference.

Most services send ``x-amzn-requestid``. Services in the Amazon S3 lineage send
``x-amz-request-id`` instead.
"""

_EXTENDED_REQUEST_ID_HEADER = "x-amz-id-2"


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


def _first_value(field: Field) -> str | None:
    """The field's first value, or None if it has none or the first is empty.

    Identifiers are single opaque tokens, so a repeated header is read as its
    first value rather than joined the way ``as_string`` would.
    """
    return field.values[0] or None if field.values else None


def parse_response_metadata(response: HTTPResponse) -> ResponseMetadata:
    """Extract AWS response metadata from an HTTP response.

    The request ID is read from the first present header in
    ``_REQUEST_ID_HEADERS``. The extended request ID comes from
    ``x-amz-id-2`` and is only sent by some services.

    Absent or empty headers are left unset rather than raising, since this
    information is diagnostic and must never fail a call.
    """
    request_id = None
    for header in _REQUEST_ID_HEADERS:
        if header in response.fields:
            request_id = _first_value(response.fields[header])
            if request_id is not None:
                break

    extended_request_id = None
    if _EXTENDED_REQUEST_ID_HEADER in response.fields:
        extended_request_id = _first_value(response.fields[_EXTENDED_REQUEST_ID_HEADER])

    return ResponseMetadata(
        request_id=request_id,
        extended_request_id=extended_request_id,
        http_status_code=response.status,
    )


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
