#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from collections.abc import Iterator
from dataclasses import dataclass
from itertools import chain
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    # pyright doesn't like optional imports.
    import urllib3

try:
    import urllib3

    HAS_URLLIB3 = True
except ImportError:
    HAS_URLLIB3 = False  # type: ignore

from smithy_core.exceptions import ClientTimeoutError, MissingDependencyError
from smithy_core.interfaces import is_bytes_reader

from smithy_http import HTTPResponse
from smithy_http.interfaces import HTTPRequest
from smithy_http.interfaces import HTTPResponse as HTTPResponseInterface

from . import tuples_to_fields
from .exceptions import SmithyHTTPError
from .interfaces import HTTPClient, HTTPClientConfiguration, HTTPRequestConfiguration

__all__ = ["Urllib3HTTPClient", "Urllib3HTTPClientConfig"]

_DEFAULT_CHUNK_SIZE = 1024


@dataclass(kw_only=True)
class Urllib3HTTPClientConfig(HTTPClientConfiguration):
    """Client-level configuration for :py:class:`Urllib3HTTPClient`.

    :param connect_timeout: How long, in seconds, to wait for a connection, or None
        to wait indefinitely.
    :param read_timeout: How long, in seconds, to wait for data on an open
        connection, or None to wait indefinitely. A request's
        ``HTTPRequestConfiguration.read_timeout`` takes precedence.
    :param max_pool_connections: How many connections to keep open for reuse per
        host. Concurrent requests beyond this open connections that aren't kept.
    """

    connect_timeout: float | None = 60.0
    read_timeout: float | None = 60.0
    max_pool_connections: int = 10

    def __post_init__(self) -> None:
        _assert_urllib3()


class Urllib3HTTPClient(HTTPClient):
    """Implementation of :py:class:`.interfaces.HTTPClient` using urllib3."""

    TIMEOUT_EXCEPTIONS: tuple[type[Exception], ...] = (
        (urllib3.exceptions.TimeoutError,) if HAS_URLLIB3 else ()
    )

    def __init__(
        self,
        *,
        client_config: Urllib3HTTPClientConfig | None = None,
        _pool: "urllib3.PoolManager | None" = None,
    ) -> None:
        """
        :param client_config: Configuration that applies to all requests made with this
        client.
        """
        _assert_urllib3()
        self._config = client_config or Urllib3HTTPClientConfig()
        self._closed = False
        # Advertise 'identity' to request uncompressed responses. Uploads are streamed in
        # 128 KiB blocks, as in botocore: urllib3's 16 KiB default was about 2.5x slower,
        # and larger blocks were no faster.
        self._pool = _pool or urllib3.PoolManager(
            maxsize=self._config.max_pool_connections,
            headers={"Accept-Encoding": "identity"},
            blocksize=128 * 1024,
        )

    def __enter__(self) -> Self:
        if self._closed:
            raise SmithyHTTPError("Cannot enter an HTTP client that has been closed.")
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.close()

    def __deepcopy__(self, memo: Any) -> Self:
        return self

    def send(
        self,
        request: HTTPRequest,
        *,
        request_config: HTTPRequestConfiguration | None = None,
    ) -> HTTPResponseInterface:
        """Send HTTP request using urllib3.

        The response body is streamed: it holds a pooled connection until it's read
        to the end, which returns the connection to the pool, or closed, which
        discards it.

        :param request: The request including destination URI, fields, payload.
        :param request_config: Configuration specific to this request.
        """
        if self._closed:
            raise SmithyHTTPError(
                "Cannot send a request after the HTTP client has been closed."
            )
        request_config = request_config or HTTPRequestConfiguration()
        read_timeout = request_config.read_timeout
        timeout = urllib3.Timeout(
            connect=self._config.connect_timeout,
            read=self._config.read_timeout if read_timeout is None else read_timeout,
        )
        # urllib3 can't send request trailers, and a trailer is never a header.
        headers = urllib3.HTTPHeaderDict()
        for name, value in chain.from_iterable(
            fld.as_tuples() for fld in request.fields.get_by_type("header")
        ):
            headers.add(name, value)

        raw = self._pool.request(
            method=request.method,
            url=request.destination.build(),
            body=_request_body(request),
            headers=headers,
            redirect=False,
            retries=False,
            preload_content=False,
            decode_content=False,
            timeout=timeout,
        )
        return HTTPResponse(
            status=raw.status,
            fields=tuples_to_fields(raw.headers.items()),
            body=_Urllib3ResponseBody(raw),
            reason=raw.reason,
        )

    def close(self) -> None:
        """Close the underlying connection pool."""
        if self._closed:
            return
        self._closed = True
        self._pool.clear()


def _request_body(request: HTTPRequest) -> Any:
    """The body to give urllib3, which streams readers rather than reading them first.

    urllib3 reads a reader in blocks as it sends it, framed by the request's
    Content-Length or chunked transfer encoding. Without either it would switch to
    chunked transfer encoding, which services such as S3 reject, so such a body is
    read into memory and sent with its length.
    """
    body = request.body
    fields = request.fields
    if is_bytes_reader(body) and (
        "content-length" in fields or "transfer-encoding" in fields
    ):
        return body
    return request.consume_body()


class _Urllib3ResponseBody:
    """A streamed urllib3 response body.

    The body holds its connection until it's read to the end, which returns the
    connection to the pool for reuse, or closed, which closes the connection, since
    the unread rest of the body can't be skipped without reading it. A body that's
    neither read to the end nor closed holds its connection until it's garbage
    collected, so use it in a ``with`` block when it may not be read to the end.

    Errors raised while reading are raised as Smithy errors: timeouts as
    :py:class:`ClientTimeoutError`, so that they're retried while the client reads
    an error or non-streaming response, and other connection failures as
    :py:class:`SmithyHTTPError`.
    """

    def __init__(self, response: "urllib3.BaseHTTPResponse") -> None:
        """Initialize the body.

        :param response: A response sent with ``preload_content=False``.
        """
        self._response = response
        self._closed = False

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.close()

    def __iter__(self) -> Iterator[bytes]:
        return self.iter_chunks()

    @property
    def closed(self) -> bool:
        """Whether the body was closed."""
        return self._closed

    def read(self, size: int = -1) -> bytes:
        """Read up to ``size`` bytes, or the rest of the body if it's negative.

        An empty result means the body was read to the end.

        :raises ClientTimeoutError: If the server stops sending data for longer
            than the read timeout.
        :raises SmithyHTTPError: If the connection fails, including when it closes
            before the whole ``Content-Length`` was received.
        """
        if self._closed:
            raise ValueError("I/O operation on closed file.")
        try:
            return self._response.read(None if size < 0 else size)
        except Urllib3HTTPClient.TIMEOUT_EXCEPTIONS as e:
            # Name the cause, as the client does for timeouts while sending.
            raise ClientTimeoutError(
                message=f"A timeout error occurred ({type(e).__name__}: {e})."
            ) from e
        except urllib3.exceptions.HTTPError as e:
            raise SmithyHTTPError(f"Failed to read the response body: {e}") from e

    def iter_chunks(self, chunk_size: int = _DEFAULT_CHUNK_SIZE) -> Iterator[bytes]:
        """Iterate over the body in chunks of up to ``chunk_size`` bytes."""
        while data := self.read(chunk_size):
            yield data

    def readable(self) -> bool:
        """Whether the body is readable."""
        return True

    def writeable(self) -> bool:
        """Whether the body is writeable, which it never is."""
        return False

    def seekable(self) -> bool:
        """Whether the body is seekable, which it never is."""
        return False

    def close(self) -> None:
        """Close the body, releasing its connection.

        A body that was read to the end has already returned its connection to the
        pool. Otherwise the connection is closed, and its slot in the pool freed.
        """
        if self._closed:
            return
        self._closed = True
        # Closes the socket unless the connection was already returned to the pool
        # at the end of the body, then frees the pool slot it held.
        self._response.close()
        self._response.release_conn()


def _assert_urllib3() -> None:
    if not HAS_URLLIB3:
        raise MissingDependencyError(
            "Attempted to use the urllib3 component, but urllib3 is not installed."
        )
