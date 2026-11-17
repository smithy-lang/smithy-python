#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import sys
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Literal, Protocol, TypeVar, runtime_checkable

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

if sys.version_info >= (3, 12):
    from typing import TypeAliasType
else:
    from typing_extensions import TypeAliasType


if TYPE_CHECKING:
    from typing_extensions import TypeForm

    from ...deserializers import DeserializeableShape, ShapeDeserializer
    from ...endpoints import EndpointResolverParams
    from ...interfaces import Endpoint
    from ...schemas import APIOperation
    from ...serializers import SerializeableShape
    from .auth import AsyncAuthScheme

_IE = TypeVar("_IE", bound="SerializeableShape")
_OE = TypeVar("_OE", bound="DeserializeableShape")
_I = TypeVar("_I", bound=Request)
_I_contra = TypeVar("_I_contra", bound=Request, contravariant=True)
_O_co = TypeVar("_O_co", bound=Response, covariant=True)
_O_contra = TypeVar("_O_contra", bound=Response, contravariant=True)
_OperationInput = TypeVar("_OperationInput", bound="SerializeableShape")
_OperationOutput = TypeVar("_OperationOutput", bound="DeserializeableShape")


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


StreamingBlob = TypeAliasType("StreamingBlob", AnyStreamingBlob)


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


class AsyncClientTransport(Protocol[_I_contra, _O_co]):
    """Protocol-agnostic representation of a client transport (e.g. an HTTP client).

    Transports that support duplex (bidirectional) event streaming can implement
    :py:class:`AsyncDuplexClientTransport`.
    """

    TIMEOUT_EXCEPTIONS: tuple[type[Exception], ...]

    async def send(self, request: _I_contra) -> _O_co:
        """Send a request over the transport and receive the response."""
        ...


class AsyncDuplexClientTransport(
    AsyncClientTransport[_I_contra, _O_co], Protocol[_I_contra, _O_co]
):
    """A client transport that supports duplex (bidirectional) event streaming.

    Duplex transports can read response data while the request body is still being
    written. HTTP transports typically require HTTP/2 for this capability.
    """

    SUPPORTS_DUPLEX_STREAMING: Literal[True]


@runtime_checkable
class AsyncClientProtocol(ClientProtocol[_I, _O_contra], Protocol[_I, _O_contra]):
    """A client protocol that also supports event streams for async clients."""

    async def create_event_publisher(
        self,
        *,
        operation: "APIOperation[_OperationInput, _OperationOutput]",
        request: _I,
        event_type: "TypeForm[_IE]",
        context: TypedProperties,
        auth_scheme: "AsyncAuthScheme[Any, Any, Any, Any] | None" = None,
    ) -> AsyncEventPublisher[_IE]:
        """Creates an event publisher for a protocol event stream.

        :param operation: The event stream operation.
        :param request: The transport request that was sent for this stream.
        :param event_type: The type of event to publish.
        :param context: A context bag for the request.
        :param auth_scheme: The optional auth scheme used to sign events.
        """
        raise UnsupportedStreamError()

    def create_event_receiver(
        self,
        *,
        operation: "APIOperation[_OperationInput, _OperationOutput]",
        request: _I,
        response: _O_contra,
        event_type: "TypeForm[_OE]",
        event_deserializer: Callable[["ShapeDeserializer"], _OE],
        context: TypedProperties,
    ) -> AsyncEventReceiver[_OE]:
        """Creates an event receiver for a protocol event stream.

        :param operation: The event stream operation.
        :param request: The transport request that was sent for this stream.
        :param response: The transport response that was received for this stream.
        :param event_type: The type of event to publish.
        :param event_deserializer: The deserializer to be used to deserialize events.
        :param context: A context bag for the request.
        """
        raise UnsupportedStreamError()
