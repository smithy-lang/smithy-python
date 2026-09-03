#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from typing import TYPE_CHECKING, Any

from smithy_core.documents import TypeRegistry
from smithy_core.exceptions import CallError, ExpectationNotMetError, ModeledError
from smithy_core.interfaces import TypedProperties
from smithy_core.schemas import APIOperation
from smithy_core.shapes import ShapeID

from ...traits import AwsQueryErrorTrait
from ..xml import assert_xml, parse_xml_error_code

try:
    from smithy_xml import XMLCodec
except ImportError:
    pass

if TYPE_CHECKING:
    from smithy_xml import XMLCodec


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
    context: TypedProperties,
    retry_after: float | None = None,
) -> CallError:
    """Create a modeled or generic CallError from an awsQuery error response."""
    code = parse_xml_error_code(body, wrapper_elements)
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

            assert_xml()
            deserializer = XMLCodec().create_deserializer(
                body, wrapper_elements=wrapper_elements
            )
            modeled_error = error_shape.deserialize(deserializer)
            if retry_after is not None:
                modeled_error.retry_after = retry_after
            return modeled_error

    message = f"Unknown error for operation {operation.schema.id} - status: {status}"
    if code is not None:
        message += f", code: {code}"

    is_timeout = status == 408
    is_throttle = status == 429
    fault = "client" if status < 500 else "server"

    return CallError(
        message=message,
        fault=fault,
        is_throttling_error=is_throttle,
        is_timeout_error=is_timeout,
        is_retry_safe=is_throttle or is_timeout or None,
        retry_after=retry_after,
    )
