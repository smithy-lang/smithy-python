#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import logging
import os
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol, Self
from urllib.parse import unquote, urlsplit

from smithy_core import URI as _URI
from smithy_core.interfaces import Request, Response, URI
from smithy_core.schemas import APIOperation
from smithy_core.shapes import ShapeID
from smithy_core.utils import read_streaming_blob

from ..exceptions import SmithyHTTPError as _SmithyHTTPError

__all__ = [
    "Field",
    "FieldPosition",
    "Fields",
    "HTTPClient",
    "HTTPClientConfiguration",
    "HTTPErrorIdentifier",
    "HTTPProxyConfig",
    "HTTPRequest",
    "HTTPRequestConfiguration",
    "HTTPResponse",
    "ProxyURI",
    "QueryParamsList",
]

FieldPosition = Literal["header", "trailer"]
"""The type of a field.

Defines its placement in a request or response.

header: Header field. In HTTP this is a header as defined in RFC 9110 Section 6.3.
trailer: Trailer field. In HTTP this is a trailer as defined in RFC 9110 Section 6.5.

Implementations of other protocols may use this FieldPosition for similar types of metadata.
"""


class Field(Protocol):
    """A name-value pair representing a single field in a request or response.

    The kind will dictate metadata placement within an the message, for example as
    header or trailer field in a HTTP request as defined in RFC 9110 Section 5.

    All field names are case insensitive and case-variance must be treated as
    equivalent. Names may be normalized but should be preserved for accuracy during
    transmission.
    """

    name: str
    values: list[str]
    kind: FieldPosition = "header"

    def add(self, value: str) -> None:
        """Append a value to a field."""
        ...

    def set(self, values: list[str]) -> None:
        """Overwrite existing field values."""
        ...

    def remove(self, value: str) -> None:
        """Remove all matching entries from list."""
        ...

    def as_string(self, delimiter: str = ",") -> str:
        """Serialize the ``Field``'s values into a single line string."""
        ...

    def as_tuples(self) -> list[tuple[str, str]]:
        """Get list of ``name``, ``value`` tuples where each tuple represents one
        value."""
        ...


class Fields(Protocol):
    """Protocol agnostic mapping of key-value pair request metadata, such as HTTP
    fields."""

    # Entries are keyed off the name of a provided Field
    entries: dict[str, Field]
    encoding: str = "utf-8"

    def __setitem__(self, name: str, field: Field) -> None:
        """Set entry for a Field name."""
        ...

    def __getitem__(self, name: str) -> Field:
        """Retrieve Field entry."""
        ...

    def __delitem__(self, name: str) -> None:
        """Delete entry from collection."""
        ...

    def __iter__(self) -> Iterator[Field]:
        """Allow iteration over entries."""
        ...

    def __len__(self) -> int:
        """Get total number of Field entries."""
        ...

    def __contains__(self, key: str) -> bool:
        """Allows in/not in checks on Field entries."""
        ...

    def set_field(self, field: Field) -> None:
        """Alias for __setitem__ to utilize the field.name for the entry key."""
        ...

    def get_by_type(self, kind: FieldPosition) -> list[Field]:
        """Helper function for retrieving specific types of fields.

        Used to grab all headers or all trailers.
        """
        ...

    def extend(self, other: "Fields") -> None:
        """Merges ``entries`` of ``other`` into the current ``entries``.

        For every `Field` in the ``entries`` of ``other``: If the normalized name
        already exists in the current ``entries``, the values from ``other`` are
        appended. Otherwise, the ``Field`` is added to the list of ``entries``.
        """
        ...


class HTTPRequest(Request, Protocol):
    """HTTP primitive for an Exchange to construct a version agnostic HTTP message.

    :param destination: The URI where the request should be sent to.
    :param method: The HTTP method of the request, for example "GET".
    :param fields: ``Fields`` object containing HTTP headers and trailers.
    :param body: A streamable collection of bytes.
    """

    method: str
    fields: Fields

    def consume_body(self) -> bytes:
        """Read the request body into bytes."""
        return read_streaming_blob(self.body)


class HTTPResponse(Response, Protocol):
    """HTTP primitives returned from an Exchange, used to construct a client
    response."""

    @property
    def status(self) -> int:
        """The 3 digit response status code (1xx, 2xx, 3xx, 4xx, 5xx)."""
        ...

    @property
    def fields(self) -> Fields:
        """``Fields`` object containing HTTP headers and trailers."""
        ...

    @property
    def reason(self) -> str | None:
        """Optional string provided by the server explaining the status."""
        ...

    def consume_body(self) -> bytes:
        """Read the response body into bytes."""
        return read_streaming_blob(self.body)


class HTTPErrorIdentifier:
    """A class that uses HTTP response metadata to identify errors.

    The body of the response SHOULD NOT be touched by this. The payload codec will be
    used instead to check for an ID in the body.
    """

    def identify(
        self,
        *,
        operation: APIOperation[Any, Any],
        response: HTTPResponse,
    ) -> ShapeID | None:
        """Idenitfy the ShapeID of an error from an HTTP response."""


QueryParamsList = list[tuple[str, str]]

_LOGGER = logging.getLogger(__name__)


@dataclass(kw_only=True, frozen=True, eq=False)
class ProxyURI(_URI):
    """The port to connect to the proxy on.

    Port is filled in from the scheme (80 for 'http', 443 for 'https')
    field() makes port required: a bare annotation would inherit URI's None default
    pyright flags a required override, but kw_only=True makes it valid
    """

    port: int = field()  # pyright: ignore[reportGeneralTypeIssues]


@dataclass(kw_only=True, frozen=True, repr=False)
class HTTPProxyConfig:
    """Client-level HTTP proxy configuration.

    Proxy URLs parsed as 'scheme://[user[:password]@]host[:port]'.
    Proxying disabled when URLs are not set,

    :param http_proxy: Proxy URL for requests to 'http' destinations
    :param https_proxy: Proxy URL for requests to 'https' destinations
    :param no_proxy: Comma-separated hosts that bypass the proxy
        '*' bypass every host.
        Entry with a port like 'example.com:8443' matches only that port.
        IPv6 entries need brackets '[::1]'.
    """

    http_proxy: str | None = None
    https_proxy: str | None = None
    no_proxy: str | None = None

    _http_proxy_uri: ProxyURI | None = field(
        default=None, init=False, repr=False, compare=False
    )
    _https_proxy_uri: ProxyURI | None = field(
        default=None, init=False, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        """Parses URL and sets proxy once so proxy_for doesn't parse again on each call"""
        if self.http_proxy:
            object.__setattr__(
                self, "_http_proxy_uri", self._parse_url(self.http_proxy)
            )
        if self.https_proxy:
            object.__setattr__(
                self, "_https_proxy_uri", self._parse_url(self.https_proxy)
            )

    def __repr__(self) -> str:
        """Omit passwords in urls"""
        return (
            f"HTTPProxyConfig(http_proxy={self._http_proxy_uri!r}, "
            f"https_proxy={self._https_proxy_uri!r}, "
            f"no_proxy={self.no_proxy!r})"
        )

    @classmethod
    def from_environment(cls, environ: Mapping[str, str] | None = None) -> Self:
        """Build a configuration from the HTTP_PROXY, HTTPS_PROXY and
        NO_PROXY environment variables.

        :param environ: The variables to read. Defaults to os.environ.
        """
        envvars = os.environ if environ is None else environ

        def get(name: str) -> str | None:
            return envvars.get(name.lower()) or envvars.get(name.upper()) or None

        def get_proxy_url(name: str) -> str | None:
            if (value := get(name.upper())) is None:
                return None
            try:
                cls._parse_url(value)
            except _SmithyHTTPError as e:
                _LOGGER.warning("Ignoring the %s environment variable: %s", name, e)
                return None
            return value

        return cls(
            http_proxy=get_proxy_url("http_proxy"),
            https_proxy=get_proxy_url("https_proxy"),
            no_proxy=get("no_proxy"),
        )

    def proxy_for(self, destination: URI) -> ProxyURI | None:
        """Return the proxy to use for 'destination', or None to connect directly.

        :param destination: The URI a request is sent to.
        """
        match destination.scheme:
            case "http":
                proxy = self._http_proxy_uri
            case "https":
                proxy = self._https_proxy_uri
            case _:
                return None
        if proxy is None or self._bypass_addresses(destination):
            return None
        return proxy

    def _bypass_addresses(self, destination: URI) -> bool:
        """Bypasses addresses listed in NO_PROXY
        Leading dot is ignored: '.example.com' matches example.com
        Entry without "port" matches the host on any port
        Entry with port like "example.com:8443", matches only that port.
        """
        if not self.no_proxy:
            return False
        if self.no_proxy.strip() == "*":
            return True
        host = destination.host.lower()
        if ":" in host:
            host = f"[{host}]"
        port = destination.port or (443 if destination.scheme == "https" else 80)
        host_port = f"{host}:{port}"
        for raw_entry in self.no_proxy.split(","):
            if not (entry := raw_entry.strip().lstrip(".").lower()):
                continue
            for candidate in (host, host_port):
                if candidate == entry or candidate.endswith(f".{entry}"):
                    return True
        return False

    @staticmethod
    def _parse_url(value: str) -> ProxyURI:
        url = value.strip()
        if "://" not in url:
            url = f"http://{url}"
        parts = urlsplit(url)
        scheme = parts.scheme.lower()
        if scheme not in ("http", "https"):
            raise _SmithyHTTPError(
                f"Unsupported proxy URL scheme {scheme!r}: expected 'http' or 'https'."
            )
        try:
            port = parts.port
        except ValueError as e:
            raise _SmithyHTTPError("Proxy URL has an invalid port.") from e
        if not parts.hostname:
            raise _SmithyHTTPError("Proxy URL has no host.")
        return ProxyURI(
            scheme=scheme,
            host=parts.hostname,
            port=port if port is not None else (443 if scheme == "https" else 80),
            username=(
                unquote(parts.username or "")
                if parts.username or parts.password is not None
                else None
            ),
            password=unquote(parts.password) if parts.password is not None else None,
        )


@dataclass(kw_only=True)
class HTTPClientConfiguration:
    """Client-level HTTP configuration.

    :param force_http_2: Whether to require HTTP/2.
    """

    force_http_2: bool = False


@dataclass(kw_only=True)
class HTTPRequestConfiguration:
    """Request-level HTTP configuration.

    :param read_timeout: How long, in seconds, the client will attempt to read the first
        byte over an established, open connection before timing out.
    """

    read_timeout: float | None = None


class HTTPClient(Protocol):
    """A synchronous HTTP client interface.

    Header field names and values are not validated before reaching this layer.
    Implementations of ``HTTPClient`` are responsible for validating and handling those
    invalid and dangerous characters (such as CR, LF, or NUL) as defined in `RFC 9110,
    Section 5.5 <https://www.rfc-editor.org/rfc/rfc9110#section-5.5>`_.
    """

    TIMEOUT_EXCEPTIONS: tuple[type[Exception], ...]

    def __init__(self, *, client_config: HTTPClientConfiguration | None) -> None:
        """
        :param client_config: Configuration that applies to all requests made with this
        client.
        """
        ...

    def send(
        self,
        request: HTTPRequest,
        *,
        request_config: HTTPRequestConfiguration | None = None,
    ) -> HTTPResponse:
        """Send HTTP request over the wire and return the response.

        :param request: The request including destination URI, fields, payload.
        :param request_config: Configuration specific to this request.
        """
        ...
