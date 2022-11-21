from dataclasses import dataclass
from typing import Any, Optional, Protocol, TypeVar

# Defining headers as a list instead of a mapping to avoid ambiguity and
# the nuances of multiple fields in a mapping style interface
HeadersList = list[tuple[str, str]]


class URL(Protocol):
    scheme: str  # http or https
    hostname: str  # hostname e.g. amazonaws.com
    port: Optional[int]  # explicit port number
    path: str  # request path
    query_params: list[tuple[str, str]]


class Request(Protocol):
    url: URL
    method: str  # GET, PUT, etc
    headers: HeadersList
    body: Any


class Response(Protocol):
    status_code: int  # HTTP status code
    headers: HeadersList
    body: Any


class Endpoint(Protocol):
    url: URL
    headers: HeadersList


EndpointParams = TypeVar("EndpointParams", contravariant=True)


class EndpointResolver(Protocol[EndpointParams]):
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
