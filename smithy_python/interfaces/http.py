from typing import Optional, List, Tuple, Any

from typing_extensions import Protocol


# Defining headers as a list instead of a mapping to avoid ambiguity and
# the nuances of multiple fields in a mapping style interface
HeadersList = List[Tuple[str, str]]


class URL(Protocol):
    scheme: str  # http or https
    hostname: str  # hostname e.g. amazonaws.com
    port: Optional[int]  # explicit port number
    path: str  # request path
    query_params: List[Tuple[str, str]]


class Request(Protocol):
    url: URL
    method: str  # GET, PUT, etc
    headers: HeadersList
    body: Any


class Response(Protocol):
    status_code: int  # HTTP status code
    headers: HeadersList
    body: Any


class Session(Protocol):
    def send(self, request: Request) -> Response:
        pass


class AsyncSession(Protocol):
    async def send(self, request: Request) -> Response:
        pass
