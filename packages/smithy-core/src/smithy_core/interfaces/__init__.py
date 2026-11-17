# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import sys
from collections.abc import (
    AsyncIterable,
    Awaitable,
    Callable,
    ItemsView,
    Iterator,
    KeysView,
    Sequence,
    ValuesView,
)
from dataclasses import dataclass
from inspect import iscoroutinefunction
from typing import (
    TYPE_CHECKING,
    Any,
    Protocol,
    TypeGuard,
    overload,
    runtime_checkable,
)

if sys.version_info >= (3, 12):
    from typing import TypeAliasType, TypeVar
else:
    from typing_extensions import TypeAliasType, TypeVar


__all__ = [
    "URI",
    "AnyStreamingBlob",
    "AwaitableBytesReader",
    "BytesReader",
    "BytesWriter",
    "ClientProtocol",
    "ClientTransport",
    "Endpoint",
    "EndpointResolver",
    "PropertyKey",
    "ProtocolConstructor",
    "ProtocolSettings",
    "Request",
    "Response",
    "SeekableBytesReader",
    "StreamingBlob",
    "TypedProperties",
    "is_bytes_reader",
    "is_streaming_blob",
]

if TYPE_CHECKING:
    from typing_extensions import TypeForm

    from .._schema_compact import StaticSchema
    from ..deserializers import DeserializeableShape
    from ..documents import TypeRegistry
    from ..endpoints import EndpointAuthScheme, EndpointResolverParams
    from ..program import Program
    from ..response import ResponseMetadata
    from ..schemas import APIOperation, Schema
    from ..serializers import SerializeableShape
    from ..shapes import ShapeID

_DT = TypeVar("_DT")
_I = TypeVar("_I", infer_variance=True)
_O = TypeVar("_O", infer_variance=True)
_OperationInput = TypeVar("_OperationInput", bound="SerializeableShape")
_OperationOutput = TypeVar("_OperationOutput", bound="DeserializeableShape")
_T = TypeVar("_T", infer_variance=True)


class URI(Protocol):
    """Universal Resource Identifier, target location for a :py:class:`Request`."""

    scheme: str
    """For example ``http`` or ``mqtts``."""

    username: str | None
    """Username part of the userinfo URI component."""

    password: str | None
    """Password part of the userinfo URI component."""

    host: str
    """The hostname, for example ``amazonaws.com``."""

    port: int | None
    """An explicit port number."""

    path: str | None
    """Path component of the URI."""

    query: str | None
    """Query component of the URI as string."""

    fragment: str | None
    """Part of the URI specification, but may not be transmitted by a client."""

    def build(self) -> str:
        """Construct URI string representation.

        Returns a string of the form
        ``{scheme}://{username}:{password}@{host}:{port}{path}?{query}#{fragment}``
        """
        ...

    @property
    def netloc(self) -> str:
        """Construct netloc string in format ``{username}:{password}@{host}:{port}``"""
        ...


@runtime_checkable
class BytesWriter(Protocol):
    """A protocol for objects that support writing bytes to them."""

    def write(self, b: bytes, /) -> int:
        """Write ``b`` and return the number of bytes written."""
        ...


@runtime_checkable
class BytesReader(Protocol):
    """A protocol for objects that support reading bytes from them."""

    def read(self, size: int = -1, /) -> bytes:
        """Read up to ``size`` bytes, or all remaining bytes if ``size`` is negative."""
        ...


def is_bytes_reader(obj: Any) -> TypeGuard[BytesReader]:
    """Determines whether the given object conforms to the BytesReader protocol.

    This is necessary to distinguish this from an async reader, since runtime_checkable
    doesn't make that distinction.

    :param obj: The object to inspect.
    """
    return isinstance(obj, BytesReader) and not iscoroutinefunction(obj.read)


@runtime_checkable
class SeekableBytesReader(BytesReader, Protocol):
    """A synchronous bytes reader with seek and tell methods."""

    def tell(self) -> int:
        """Return the current stream position."""
        ...

    def seek(self, offset: int, whence: int = 0, /) -> int:
        """Move the stream position and return the new absolute position."""
        ...


# A union of all acceptable streaming blob types. Deserialized payloads will
# always return a ByteStream, or AsyncByteStream if async is enabled.
StreamingBlob = TypeAliasType("StreamingBlob", BytesReader | bytes | bytearray)


def is_streaming_blob(obj: Any) -> TypeGuard[StreamingBlob]:
    """Determines whether the given object is a StreamingBlob.

    :param obj: The object to inspect.
    """
    return isinstance(obj, bytes | bytearray) or is_bytes_reader(obj)


@runtime_checkable
class AwaitableBytesReader(Protocol):
    """A file-like object whose read returns an awaitable, such as an async stream."""

    def read(self, size: int = -1) -> Awaitable[bytes]:
        """Read up to ``size`` bytes, or all remaining bytes if ``size`` is negative."""
        ...


# CAUTION: matches smithy_core.aio.interfaces.StreamingBlob structurally; message
# types carry either mode's body, so they can't name the aio alias.
AnyStreamingBlob = TypeAliasType(
    "AnyStreamingBlob", StreamingBlob | AwaitableBytesReader | AsyncIterable[bytes]
)


class Request(Protocol):
    """Protocol-agnostic representation of a request."""

    destination: URI
    """The URI where the request should be sent to."""

    body: AnyStreamingBlob = b""
    """The request payload."""

    def consume_body(self) -> bytes:
        """Read the request body into bytes."""
        ...


class Response(Protocol):
    """Protocol-agnostic representation of a response."""

    @property
    def body(self) -> AnyStreamingBlob:
        """The response payload."""
        ...

    def consume_body(self) -> bytes:
        """Read the response body into bytes."""
        ...


class Endpoint(Protocol):
    """A resolved endpoint."""

    uri: URI
    """The endpoint URI."""

    properties: "TypedProperties"
    """Properties required to interact with the endpoint.

    For example, in some AWS use cases this might contain HTTP headers to add to each
    request.
    """

    auth_schemes: Sequence["EndpointAuthScheme"]
    """The auth schemes the endpoint supports, in order of preference.

    Empty when the endpoint has no special auth settings.
    """


@runtime_checkable
class PropertyKey(Protocol[_T]):
    """A typed properties key.

    Used with :py:class:`Context` to set and get typed values.

    For a concrete implementation, see :py:class:`smithy_core.types.PropertyKey`.

    .. code-block:: python

        UNION_PROPERTY: PropertyKey[str | int] = PropertyKey(
            key="union",
            value_type=str | int,
        )
    """

    key: str
    """The string key used to access the value."""

    value_type: "TypeForm[_T]"
    """The type of the associated value in the properties bag."""

    def __str__(self) -> str:
        return self.key


# This is currently strongly tied to being compatible with a dict[str, Any], but we
# could remove that to allow for potentially more efficient maps. That might introduce
# unacceptable usability penalties or footguns though.
@runtime_checkable
class TypedProperties(Protocol):
    """A properties map with typed setters and getters.

    Keys can be either a string or a :py:class:`PropertyKey`. Using a PropertyKey instead
    of a string enables type checkers to narrow to the associated value type rather
    than having to use Any.

    Letting the value be either a string or PropertyKey allows consumers who care about
    typing to get it, and those who don't care about typing to not have to think about
    it.

    ..code-block:: python

        foo = PropertyKey(key="foo", value_type=str)
        properties = TypedProperties()
        properties[foo] = "bar"

        assert assert_type(properties[foo], str) == "bar"
        assert assert_type(properties["foo"], Any) == "bar"

    For a concrete implementation, see :py:class:`smithy_core.types.TypedProperties`.

    Note that unions and other special types cannot easily be used here due to being
    incompatible with ``type[T]``. PEP747 proposes a fix to this case, but it has not
    yet been accepted. In the meantime, there is a workaround. The PropertyKey must
    be assigned to an explicitly typed variable, and the ``value_type`` parameter of
    the constructor must have a ``# type: ignore`` comment, like so:

    .. code-block:: python

        UNION_PROPERTY: PropertyKey[str | int] = PropertyKey(
            key="union",
            value_type=str | int,  # type: ignore
        )

        properties = TypedProperties()
        properties[UNION_PROPERTY] = "foo"

        assert assert_type(properties[UNION_PROPERTY], str | int) == "foo"

    Type checkers will be able to use such a property as expected.
    """

    @overload
    def __getitem__(self, key: PropertyKey[_T]) -> _T: ...

    @overload
    def __getitem__(self, key: str) -> Any: ...

    @overload
    def __setitem__(self, key: PropertyKey[_T], value: _T) -> None: ...

    @overload
    def __setitem__(self, key: str, value: Any) -> None: ...

    def __delitem__(self, key: str | PropertyKey[Any]) -> None: ...

    def __iter__(self) -> Iterator[str]: ...

    def __contains__(self, key: object) -> bool: ...

    @overload
    def get(self, key: PropertyKey[_T], default: None = None) -> _T | None: ...

    @overload
    def get(self, key: PropertyKey[_T], default: _T) -> _T: ...

    @overload
    def get(self, key: PropertyKey[_T], default: _DT) -> _T | _DT: ...

    @overload
    def get(self, key: str, default: None = None) -> Any | None: ...

    @overload
    def get(self, key: str, default: _T) -> Any | _T: ...

    @overload
    def pop(self, key: PropertyKey[_T], default: None = None) -> _T | None: ...

    @overload
    def pop(self, key: PropertyKey[_T], default: _T) -> _T: ...

    @overload
    def pop(self, key: PropertyKey[_T], default: _DT) -> _T | _DT: ...

    @overload
    def pop(self, key: str, default: None = None) -> Any | None: ...

    @overload
    def pop(self, key: str, default: _T) -> Any | _T: ...

    def items(self) -> ItemsView[str, Any]:
        """Return a view of the property keys and values."""
        ...

    def keys(self) -> KeysView[str]:
        """Return a view of the property keys."""
        ...

    def values(self) -> ValuesView[Any]:
        """Return a view of the property values."""
        ...


@dataclass(kw_only=True, frozen=True)
class ProtocolSettings:
    """Service-level metadata for constructing a protocol.

    Lets a consumer select a protocol by class alone (e.g.
    ``protocol=AwsQueryClientProtocol``) without importing a private schema module.
    """

    namespace: str
    """The service's Smithy namespace, e.g. ``com.amazonaws.sqs``."""

    service_target: str
    """The service shape name, used as the ``X-Amz-Target`` prefix by RPC protocols."""

    version: str | None = None
    """The service API version. Required by awsQuery; unused by other protocols."""

    xml_namespace: str | None = None
    """The URI of the service's ``@xmlNamespace``, applied by restXml to request
    payloads that don't declare their own namespace."""

    service_schema: "StaticSchema | Schema"
    """The service shape's schema.

    Carries the service's traits, including the protocol trait whose ``eventStreamHttp``
    the RPC protocols read to negotiate HTTP/2 for event streams. The protocol reads its
    own trait off this schema, so the value is inherently per-protocol rather than a
    single flattened field. Codegen passes the compact schema form; it is hydrated on
    first read.
    """


ProtocolConstructor = TypeAliasType(
    "ProtocolConstructor", Callable[[ProtocolSettings], _T], type_params=(_T,)
)
"""A callable that builds a protocol instance from ``ProtocolSettings``.

A protocol class satisfies this, since calling the class constructs an instance.
"""


class EndpointResolver(Protocol):
    """Resolves an operation's endpoint given parameters."""

    def resolve_endpoint(self, params: "EndpointResolverParams[Any]") -> Endpoint:
        """Resolve an endpoint for the given operation.

        :param params: The parameters available to resolve the endpoint.
        """
        ...


class ClientTransport(Protocol[_I, _O]):
    """Protocol-agnostic representation of a synchronous client transport (e.g. an
    HTTP client)."""

    TIMEOUT_EXCEPTIONS: tuple[type[Exception], ...]

    def send(self, request: _I) -> _O:
        """Send a request over the transport and receive the response."""
        ...


class ClientProtocol(Protocol[_I, _O]):
    """A protocol used by a synchronous client to communicate with a server."""

    @property
    def id(self) -> "ShapeID":
        """The ID of the protocol."""
        ...

    def serialize_request(
        self,
        *,
        operation: "APIOperation[_OperationInput, _OperationOutput]",
        input: _OperationInput,
        endpoint: URI,
        context: TypedProperties,
    ) -> _I:
        """Serialize an operation input into a transport request.

        :param operation: The operation whose request is being serialized.
        :param input: The input shape to be serialized.
        :param endpoint: The base endpoint to serialize.
        :param context: A context bag for the request.
        """
        ...

    def set_service_endpoint(self, *, request: _I, endpoint: Endpoint) -> _I:
        """Update the endpoint of a transport request.

        :param request: The request whose endpoint should be updated.
        :param endpoint: The endpoint to set on the request.
        """
        ...

    def deserialize_response_program(
        self,
        *,
        operation: "APIOperation[_OperationInput, _OperationOutput]",
        request: _I,
        response: _O,
        error_registry: "TypeRegistry",
        context: TypedProperties,
        read_body: Callable[[AnyStreamingBlob], Any],
    ) -> "Program[_OperationOutput]":
        """Deserialize the output from the transport response or raise its error.

        The returned program runs under both the sync and async clients. It reads
        response bodies only by yielding ``lambda: read_body(body)``, which each
        client drives in its own mode.

        :param operation: The operation whose response is being deserialized.
        :param request: The transport request that was sent for this response.
        :param response: The response to deserialize.
        :param error_registry: A TypeRegistry used to deserialize errors.
        :param context: A context bag for the request.
        :param read_body: Reads a whole response body into bytes.
        """
        ...

    def extract_response_metadata(
        self, *, response: _O, context: TypedProperties
    ) -> "ResponseMetadata":
        """Extract metadata about a transport response.

        This is called for both successful and failed invocations so that request
        identifiers remain available to callers for debugging. Implementations
        MUST NOT raise: metadata is diagnostic, so any value that cannot be
        determined is left unset instead.

        :param response: The response to extract metadata from.
        :param context: Per-call storage shared with this protocol's other methods.
            Protocols whose request IDs arrive in the body must leave them here while
            deserializing, since only deserialization sees the parsed body.
        """
        ...
