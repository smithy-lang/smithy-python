#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from xml.etree.ElementTree import Element

from ._xml import find_child, parse_xml_root


def parse_aws_query_request_id(source: bytes | Element | None) -> str | None:
    """Parse the request ID from an awsQuery response body.

    There is no request ID header. Successes nest it under ``ResponseMetadata``,
    errors put it directly under the root.
    """
    root = parse_xml_root(source) if isinstance(source, bytes) else source
    if root is None:
        return None

    metadata = find_child(root, "ResponseMetadata")
    if metadata is not None:
        nested = find_child(metadata, "RequestId")
        if nested is not None and nested.text:
            return nested.text

    direct = find_child(root, "RequestId")
    return direct.text or None if direct is not None else None
