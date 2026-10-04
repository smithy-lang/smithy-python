#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""Synchronous HTTP client protocols.

These reuse the async protocol classes for everything except the response body
read: ``serialize_request``, ``set_service_endpoint``, error construction, and the
codec serde are already synchronous and mode-agnostic. Only ``deserialize_response``
is overridden to read the body synchronously via ``consume_body``.
"""

from smithy_core.deserializers import DeserializeableShape
from smithy_core.documents import TypeRegistry
from smithy_core.interfaces import TypedProperties
from smithy_core.schemas import APIOperation
from smithy_core.serializers import SerializeableShape

from .aio.interfaces import HTTPRequest, HTTPResponse
from .aio.protocols import RpcV2CborClientProtocol as _AsyncRpcV2CborClientProtocol


class RpcV2CborClientProtocol(_AsyncRpcV2CborClientProtocol):
    """Synchronous implementation of the smithy.protocols#rpcv2Cbor protocol."""

    def deserialize_response[  # type: ignore[override]
        OperationInput: SerializeableShape,
        OperationOutput: DeserializeableShape,
    ](
        self,
        *,
        operation: APIOperation[OperationInput, OperationOutput],
        request: HTTPRequest,
        response: HTTPResponse,
        error_registry: TypeRegistry,
        context: TypedProperties,
    ) -> OperationOutput:
        body = response.consume_body()
        return self._deserialize_from_body(
            body=body,
            operation=operation,
            response=response,
            error_registry=error_registry,
            context=context,
        )
