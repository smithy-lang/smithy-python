#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Literal, Protocol, runtime_checkable

from ...exceptions import UnsupportedStreamError
from ...interfaces import (
    AnyStreamingBlob,
    ClientProtocol,
    Request,
    Response,
    TypedProperties,
)
from ...interfaces import ProtocolConstructor as ProtocolConstructor
from ...interfaces import ProtocolSettings as ProtocolSettings
from .eventstream import AsyncEventPublisher, AsyncEventReceiver

if TYPE_CHECKING:
    from typing_extensions import TypeForm

    from ...deserializers import DeserializeableShape, ShapeDeserializer
    from ...endpoints import EndpointResolverParams
    from ...interfaces import Endpoint
    from ...schemas import APIOperation
    from ...serializers import SerializeableShape
    from .auth import AsyncAuthScheme


@runtime_checkable
class AsyncByteStream(Protocol):
    """A file-like object with an async read method."""

    async def read(self, size: int = -1) -> bytes:
        """Read up to ``size`` bytes, or all remaining bytes if ``size`` is negative."""
        ...


@runtime_checkable
class AsyncWriter(Protocol):
    """An object with an async write method."""

    async def write(self, data: bytes) -> None:
        """Write ``data`` to the underlying sink."""
        ...


type StreamingBlob = AnyStreamingBlob


class AsyncEndpointResolver(Protocol):
    """Resolves an operation's endpoint given parameters, for async clients.

    Async clients also accept a sync :py:class:`smithy_core.interfaces.EndpointResolver`.
    """

    async def resolve_endpoint(
        self, params: "EndpointResolverParams[Any]"
    ) -> "Endpoint":
        """Resolve an endpoint for the given operation.

        :param params: The parameters available to resolve the endpoint.
        """
        ...


class AsyncClientTransport[I: Request, O: Response](Protocol):
    """Protocol-agnostic representation of a client transport (e.g. an HTTP client).

    Transports that support duplex (bidirectional) event streaming can implement
    :py:class:`AsyncDuplexClientTransport`.
    """

    TIMEOUT_EXCEPTIONS: tuple[type[Exception], ...]

    async def send(self, request: I) -> O:
        """Send a request over the transport and receive the response."""
        ...


class AsyncDuplexClientTransport[I: Request, O: Response](
    AsyncClientTransport[I, O], Protocol
):
    """A client transport that supports duplex (bidirectional) event streaming.

    Duplex transports can read response data while the request body is still being
    written. HTTP transports typically require HTTP/2 for this capability.
    """

    SUPPORTS_DUPLEX_STREAMING: Literal[True]


@runtime_checkable
class AsyncClientProtocol[I: Request, O: Response](ClientProtocol[I, O], Protocol):
    """A client protocol that also supports event streams for async clients."""

    async def create_event_publisher[
        OperationInput: "SerializeableShape",
        OperationOutput: "DeserializeableShape",
        Event: "SerializeableShape",
    ](
        self,
        *,
        operation: "APIOperation[OperationInput, OperationOutput]",
        request: I,
        event_type: "TypeForm[Event]",
        context: TypedProperties,
        auth_scheme: "AsyncAuthScheme[Any, Any, Any, Any] | None" = None,
    ) -> AsyncEventPublisher[Event]:
        """Creates an event publisher for a protocol event stream.

        :param operation: The event stream operation.
        :param request: The transport request that was sent for this stream.
        :param event_type: The type of event to publish.
        :param context: A context bag for the request.
        :param auth_scheme: The optional auth scheme used to sign events.
        """
        raise UnsupportedStreamError()

    def create_event_receiver[
        OperationInput: "SerializeableShape",
        OperationOutput: "DeserializeableShape",
        Event: "DeserializeableShape",
    ](
        self,
        *,
        operation: "APIOperation[OperationInput, OperationOutput]",
        request: I,
        response: O,
        event_type: "TypeForm[Event]",
        event_deserializer: Callable[["ShapeDeserializer"], Event],
        context: TypedProperties,
    ) -> AsyncEventReceiver[Event]:
        """Creates an event receiver for a protocol event stream.

        :param operation: The event stream operation.
        :param request: The transport request that was sent for this stream.
        :param response: The transport response that was received for this stream.
        :param event_type: The type of event to publish.
        :param event_deserializer: The deserializer to be used to deserialize events.
        :param context: A context bag for the request.
        """
        raise UnsupportedStreamError()
