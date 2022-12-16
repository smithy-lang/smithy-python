from dataclasses import dataclass
from typing import Any, Protocol, TypeVar

# Defining headers as a list instead of a mapping to avoid ambiguity and
# the nuances of multiple fields in a mapping style interface
HeadersList = list[tuple[str, str]]
QueryParamsList = list[tuple[str, str]]


class URI(Protocol):
    """Universal Resource Identifier, target location for a :py:class:`Request`."""

    scheme: str
    """For example ``http`` or ``https``."""

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


class Request(Protocol):
    url: URI
    method: str  # GET, PUT, etc
    headers: HeadersList
    body: Any


class Response(Protocol):
    status_code: int  # HTTP status code
    headers: HeadersList
    body: Any


class Endpoint(Protocol):
    url: URI
    headers: HeadersList


# EndpointParams are defined in the generated client, so we use a TypeVar here.
# More specific EndpointParams implementations are subtypes of less specific ones. But
# consumers of less specific EndpointParams implementations are subtypes of consumers
# of more specific ones.
EndpointParams = TypeVar("EndpointParams", contravariant=True)


class EndpointResolver(Protocol[EndpointParams]):
    """Resolves an operation's endpoint based given parameters."""

    async def resolve_endpoint(self, params: EndpointParams) -> Endpoint:
        raise NotImplementedError()


@dataclass(kw_only=True)
class HttpRequestConfiguration:
    """Request-level HTTP configuration.

    :param read_timeout: How long, in seconds, the client will attempt to read the
    first byte over an established, open connection before timing out.
    """

    read_timeout: float | None = None


class HttpClient(Protocol):
    """A synchronous HTTP client interface."""

    def send(
        self, request: Request, request_config: HttpRequestConfiguration
    ) -> Response:
        pass


class AsyncHttpClient(Protocol):
    """An asynchronous HTTP client interface."""

    async def send(
        self, request: Request, request_config: HttpRequestConfiguration
    ) -> Response:
        pass
