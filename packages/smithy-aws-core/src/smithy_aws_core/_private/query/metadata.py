#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from xml.etree.ElementTree import ParseError, fromstring

from ._xml import find_child


def parse_aws_query_request_id(body: bytes) -> str | None:
    """Parse the request ID from an awsQuery response body.

    There is no request ID header. Successes nest it under ``ResponseMetadata``,
    errors put it directly under the root.
    """
    try:
        root = fromstring(body)  # noqa: S314
    except ParseError:
        return None

    metadata = find_child(root, "ResponseMetadata")
    if metadata is not None:
        nested = find_child(metadata, "RequestId")
        if nested is not None and nested.text:
            return nested.text

    direct = find_child(root, "RequestId")
    return direct.text or None if direct is not None else None
