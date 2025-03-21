# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from asyncio import iscoroutinefunction
from collections.abc import ItemsView, Iterator, KeysView, ValuesView
from typing import (
    Any,
    Protocol,
    TypeGuard,
    overload,
    runtime_checkable,
)


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

    def write(self, b: bytes, /) -> int: ...


@runtime_checkable
class BytesReader(Protocol):
    """A protocol for objects that support reading bytes from them."""

    def read(self, size: int = -1, /) -> bytes: ...


def is_bytes_reader(obj: Any) -> TypeGuard[BytesReader]:
    """Determines whether the given object conforms to the BytesReader protocol.

    This is necessary to distinguish this from an async reader, since runtime_checkable
    doesn't make that distinction.

    :param obj: The object to inspect.
    """
    return isinstance(obj, BytesReader) and not iscoroutinefunction(
        getattr(obj, "read")
    )


# A union of all acceptable streaming blob types. Deserialized payloads will
# always return a ByteStream, or AsyncByteStream if async is enabled.
type StreamingBlob = BytesReader | bytes | bytearray


def is_streaming_blob(obj: Any) -> TypeGuard[StreamingBlob]:
    """Determines whether the given object is a StreamingBlob.

    :param obj: The object to inspect.
    """
    return isinstance(obj, bytes | bytearray) or is_bytes_reader(obj)


class Endpoint(Protocol):
    """A resolved endpoint."""

    uri: URI
    """The endpoint URI."""

    properties: "TypedProperties"
    """Properties required to interact with the endpoint.

    For example, in some AWS use cases this might contain HTTP headers to add to each
    request.
    """


@runtime_checkable
class PropertyKey[T](Protocol):
    """A typed properties key.

    Used with :py:class:`Context` to set and get typed values.

    For a concrete implementation, see :py:class:`smithy_core.types.PropertyKey`.

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

    Type checkers will be able to use such a property as expected.
    """

    key: str
    """The string key used to access the value."""

    value_type: type[T]
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
    def __getitem__[T](self, key: PropertyKey[T]) -> T: ...
    @overload
    def __getitem__(self, key: str) -> Any: ...

    @overload
    def __setitem__[T](self, key: PropertyKey[T], value: T) -> None: ...
    @overload
    def __setitem__(self, key: str, value: Any) -> None: ...

    def __delitem__(self, key: str | PropertyKey[Any]) -> None: ...

    @overload
    def get[T](self, key: PropertyKey[T], default: None = None) -> T | None: ...
    @overload
    def get[T](self, key: PropertyKey[T], default: T) -> T: ...
    @overload
    def get[T, DT](self, key: PropertyKey[T], default: DT) -> T | DT: ...
    @overload
    def get(self, key: str, default: None = None) -> Any | None: ...
    @overload
    def get[T](self, key: str, default: T) -> Any | T: ...

    @overload
    def pop[T](self, key: PropertyKey[T], default: None = None) -> T | None: ...
    @overload
    def pop[T](self, key: PropertyKey[T], default: T) -> T: ...
    @overload
    def pop[T, DT](self, key: PropertyKey[T], default: DT) -> T | DT: ...
    @overload
    def pop(self, key: str, default: None = None) -> Any | None: ...
    @overload
    def pop[T](self, key: str, default: T) -> Any | T: ...

    def __iter__(self) -> Iterator[str]: ...
    def items(self) -> ItemsView[str, Any]: ...
    def keys(self) -> KeysView[str]: ...
    def values(self) -> ValuesView[Any]: ...
    def __contains__(self, key: object) -> bool: ...
