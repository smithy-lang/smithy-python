# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from asyncio import iscoroutinefunction
from typing import Protocol, runtime_checkable, Any, TypeGuard


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
    """Determines wheter the given object is a StreamingBlob.

    :param obj: The object to inspect.
    """
    return isinstance(obj, bytes | bytearray) or is_bytes_reader(obj)
