# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass
from enum import Enum
from functools import cached_property
from urllib.parse import urlunparse

from . import interfaces, rfc3986
from .exceptions import SmithyException


class HostType(Enum):
    """Enumeration of possible host types."""

    IPv6 = "IPv6"
    """Host is an IPv6 address."""

    IPv4 = "IPv4"
    """Host is an IPv4 address."""

    DOMAIN = "DOMAIN"
    """Host type is a domain name."""

    UNKNOWN = "UNKNOWN"
    """Host type is unknown."""


@dataclass(kw_only=True, frozen=True)
class URI(interfaces.URI):
    """Universal Resource Identifier, target location for a :py:class:`HTTPRequest`."""

    scheme: str = "https"
    """For example ``http`` or ``https``."""

    username: str | None = None
    """Username part of the userinfo URI component."""

    password: str | None = None
    """Password part of the userinfo URI component."""

    host: str
    """The hostname, for example ``amazonaws.com``."""

    port: int | None = None
    """An explicit port number."""

    path: str | None = None
    """Path component of the URI."""

    query: str | None = None
    """Query component of the URI as string."""

    fragment: str | None = None
    """Part of the URI specification, but may not be transmitted by a client."""

    def __post_init__(self) -> None:
        """Validate host component."""
        if not rfc3986.HOST_MATCHER.match(self.host) and not rfc3986.IPv6_MATCHER.match(
            f"[{self.host}]"
        ):
            raise SmithyException(f"Invalid host: {self.host}")

    @property
    def netloc(self) -> str:
        """Construct netloc string in format ``{username}:{password}@{host}:{port}``

        ``username``, ``password``, and ``port`` are only included if set. ``password``
        is ignored, unless ``username`` is also set. Add square brackets around the host
        if it is a valid IPv6 endpoint URI per :rfc:`3986#section-3.2.2`.
        """
        return self._netloc

    # cached_property does NOT behave like property, it actually allows for setting.
    # Therefore we need a layer of indirection.
    @cached_property
    def _netloc(self) -> str:
        if self.username is not None:
            password = "" if self.password is None else f":{self.password}"
            userinfo = f"{self.username}{password}@"
        else:
            userinfo = ""

        if self.port is not None:
            port = f":{self.port}"
        else:
            port = ""

        if self.host_type == HostType.IPv6:
            host = f"[{self.host}]"
        else:
            host = self.host

        return f"{userinfo}{host}{port}"

    @property
    def host_type(self) -> HostType:
        """Return the type of host."""
        return self._host_type

    @cached_property
    def _host_type(self) -> HostType:
        if rfc3986.IPv6_MATCHER.match(f"[{self.host}]"):
            return HostType.IPv6
        if rfc3986.IPv4_MATCHER.match(self.host):
            return HostType.IPv4
        if rfc3986.HOST_MATCHER.match(self.host):
            return HostType.DOMAIN
        return HostType.UNKNOWN

    def build(self) -> str:
        """Construct URI string representation.

        Validate host. Returns a string of the form
        ``{scheme}://{username}:{password}@{host}:{port}{path}?{query}#{fragment}``
        """
        components = (
            self.scheme,
            self.netloc,
            self.path or "",
            "",  # params
            self.query,
            self.fragment,
        )
        return urlunparse(components)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, URI):
            return False
        return (
            self.scheme == other.scheme
            and self.host == other.host
            and self.port == other.port
            and self.path == other.path
            and self.query == other.query
            and self.username == other.username
            and self.password == other.password
            and self.fragment == other.fragment
        )
