# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from typing import Protocol, runtime_checkable


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
class ByteStream(Protocol):
    """A file-like object with a read method that returns bytes."""

    def read(self, size: int = -1) -> bytes: ...


# A union of all acceptable streaming blob types. Deserialized payloads will
# always return a ByteStream, or AsyncByteStream if async is enabled.
type StreamingBlob = ByteStream | bytes | bytearray
