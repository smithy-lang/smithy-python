#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from typing import Any
from xml.etree.ElementTree import Element, ParseError, fromstring

from smithy_core.documents import TypeRegistry
from smithy_core.exceptions import CallError, ExpectationNotMetError, ModeledError
from smithy_core.schemas import APIOperation
from smithy_core.shapes import ShapeID
from smithy_xml import XMLCodec

from ...traits import AwsQueryErrorTrait


def _local_name(tag: str) -> str:
    """Strip namespace URI from an element tag: {uri}local -> local."""
    if tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


def _find_child(element: Element, name: str) -> Element | None:
    """Return the first child element whose local name matches ``name``."""
    for child in element:
        if _local_name(child.tag) == name:
            return child
    return None


def _parse_aws_query_error_code(
    body: bytes, wrapper_elements: tuple[str, ...]
) -> str | None:
    """Parse the ``Code`` field from a wrapped awsQuery error response."""
    try:
        element = fromstring(body)  # noqa: S314
    except ParseError:
        return None

    if wrapper_elements:
        if _local_name(element.tag) != wrapper_elements[0]:
            return None
        for wrapper in wrapper_elements[1:]:
            next_element = _find_child(element, wrapper)
            if next_element is None:
                return None
            element = next_element

    code_element = _find_child(element, "Code")
    return code_element.text if code_element is not None else None


def _resolve_aws_query_error_shape_id(
    *,
    code: str,
    operation: APIOperation[Any, Any],
    error_registry: TypeRegistry,
    default_namespace: str,
) -> ShapeID | None:
    """Resolve an awsQuery error code to a modeled error shape ID."""
    for error_schema in operation.error_schemas:
        trait = error_schema.get_trait(AwsQueryErrorTrait)
        if trait is not None and trait.code == code:
            if error_schema.id in error_registry:
                return error_schema.id
            break

    fallback_id = ShapeID.from_parts(namespace=default_namespace, name=code)
    return fallback_id if fallback_id in error_registry else None


def create_aws_query_error(
    *,
    body: bytes,
    operation: APIOperation[Any, Any],
    error_registry: TypeRegistry,
    default_namespace: str,
    wrapper_elements: tuple[str, ...],
    status: int,
) -> CallError:
    """Create a modeled or generic CallError from an awsQuery error response."""
    code = _parse_aws_query_error_code(body, wrapper_elements)
    if code is not None:
        shape_id = _resolve_aws_query_error_shape_id(
            code=code,
            operation=operation,
            error_registry=error_registry,
            default_namespace=default_namespace,
        )
        if shape_id is not None:
            error_shape = error_registry.get(shape_id)
            if not issubclass(error_shape, ModeledError):
                raise ExpectationNotMetError(
                    "Modeled errors must be derived from 'ModeledError', "
                    f"but got {error_shape}"
                )

            deserializer = XMLCodec().create_deserializer(
                body, wrapper_elements=wrapper_elements
            )
            return error_shape.deserialize(deserializer)

    message = f"Unknown error for operation {operation.schema.id} - status: {status}"
    if code is not None:
        message += f", code: {code}"
    fault = "client" if 400 <= status < 500 else "server"
    return CallError(message=message, fault=fault)
