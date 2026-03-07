#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from smithy_core.documents import Document
from smithy_core.shapes import ShapeID, ShapeType


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
