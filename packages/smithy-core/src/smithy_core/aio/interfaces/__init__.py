#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from collections.abc import AsyncIterable
from typing import Protocol, runtime_checkable, TYPE_CHECKING, Any

from ...interfaces import URI, Endpoint
from ...interfaces import StreamingBlob as SyncStreamingBlob


if TYPE_CHECKING:
    from ...schemas import APIOperation
    from ...shapes import ShapeID
    from ...serializers import SerializeableShape
    from ...deserializers import DeserializeableShape


@runtime_checkable
class AsyncByteStream(Protocol):
    """A file-like object with an async read method."""

    async def read(self, size: int = -1) -> bytes: ...


@runtime_checkable
class AsyncWriter(Protocol):
    """An object with an async write method."""

    async def write(self, data: bytes) -> None: ...


# A union of all acceptable streaming blob types. Deserialized payloads will
# always return a ByteStream, or AsyncByteStream if async is enabled.
type StreamingBlob = SyncStreamingBlob | AsyncByteStream | AsyncIterable[bytes]


class Request(Protocol):
    """Protocol-agnostic representation of a request."""

    destination: URI
    """The URI where the request should be sent to."""

    body: StreamingBlob = b""
    """The request payload."""

    async def consume_body_async(self) -> bytes:
        """Iterate over request body and return as bytes."""
        ...

    def consume_body(self) -> bytes:
        """Iterate over request body and return as bytes."""
        ...


class Response(Protocol):
    """Protocol-agnostic representation of a response."""

    @property
    def body(self) -> StreamingBlob:
        """The response payload as iterable of chunks of bytes."""
        ...

    async def consume_body_async(self) -> bytes:
        """Iterate over response body and return as bytes."""
        ...

    def consume_body(self) -> bytes:
        """Iterate over request body and return as bytes."""
        ...


class ClientTransport[I: Request, O: Response](Protocol):
    """Protocol-agnostic representation of a client tranport (e.g. an HTTP client)."""

    async def send(self, request: I) -> O:
        """Send a request over the transport and receive the response."""
        ...


class ClientProtocol[I: Request, O: Response](Protocol):
    """A protocol used by a client to communicate with a server."""

    @property
    def id(self) -> "ShapeID":
        """The ID of the protocol."""
        ...

    def serialize_request[
        OperationInput: "SerializeableShape",
        OperationOutput: "DeserializeableShape",
    ](
        self,
        *,
        operation: "APIOperation[OperationInput, OperationOutput]",
        input: OperationInput,
        endpoint: URI,
        context: dict[str, Any],
    ) -> I:
        """Serialize an operation input into a transport request.

        :param operation: The operation whose request is being serialized.
        :param input: The input shape to be serialized.
        :param endpoint: The base endpoint to serialize.
        :param context: A context bag for the request.
        """
        ...

    def set_service_endpoint(
        self,
        *,
        request: I,
        endpoint: Endpoint,
    ) -> I:
        """Update the endpoint of a transport request.

        :param request: The request whose endpoint should be updated.
        :param endpoint: The endpoint to set on the request.
        """
        ...

    async def deserialize_response[
        OperationInput: "SerializeableShape",
        OperationOutput: "DeserializeableShape",
    ](
        self,
        *,
        operation: "APIOperation[OperationInput, OperationOutput]",
        request: I,
        response: O,
        error_registry: Any,  # TODO: add error registry
        context: dict[str, Any],  # TODO: replace with a typed context bag
    ) -> OperationOutput:
        """Deserializes the output from the tranport response or throws an exception.

        :param operation: The operation whose response is being deserialized.
        :param request: The transport request that was sent for this response.
        :param response: The response to deserialize.
        :param error_registry: A TypeRegistry used to deserialize errors.
        :param context: A context bag for the request.
        """
        ...
