#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
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

from smithy_core.exceptions import MissingDependencyError

from . import Field, Fields
from .aio import HTTPResponse
from .aio.interfaces import HTTPRequest
from .aio.interfaces import HTTPResponse as HTTPResponseInterface
from .exceptions import SmithyHTTPError
from .interfaces import HTTPClient, HTTPClientConfiguration, HTTPRequestConfiguration

__all__ = ["Urllib3HTTPClient", "Urllib3HTTPClientConfig"]


def _assert_urllib3() -> None:
    if not HAS_URLLIB3:
        raise MissingDependencyError(
            "Attempted to use the urllib3 component, but urllib3 is not installed."
        )


class Urllib3HTTPClientConfig(HTTPClientConfiguration):
    def __post_init__(self) -> None:
        _assert_urllib3()


class Urllib3HTTPClient(HTTPClient):
    """Implementation of :py:class:`.interfaces.HTTPClient` using urllib3."""

    TIMEOUT_EXCEPTIONS = (urllib3.exceptions.TimeoutError,) if HAS_URLLIB3 else ()

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
        # Advertise 'identity' to request uncompressed responses.
        self._pool = _pool or urllib3.PoolManager(
            headers={"Accept-Encoding": "identity"}
        )

    def send(
        self,
        request: HTTPRequest,
        *,
        request_config: HTTPRequestConfiguration | None = None,
    ) -> HTTPResponseInterface:
        """Send HTTP request using urllib3.

        :param request: The request including destination URI, fields, payload.
        :param request_config: Configuration specific to this request.
        """
        if self._closed:
            raise SmithyHTTPError(
                "Cannot send a request after the HTTP client has been closed."
            )
        request_config = request_config or HTTPRequestConfiguration()
        timeout = (
            urllib3.Timeout(read=request_config.read_timeout)
            if request_config.read_timeout is not None
            else None
        )
        headers = urllib3.HTTPHeaderDict()
        for name, value in chain.from_iterable(
            fld.as_tuples() for fld in request.fields
        ):
            headers.add(name, value)

        raw = self._pool.request(
            method=request.method,
            url=request.destination.build(),
            body=request.consume_body(),
            headers=headers,
            redirect=False,
            retries=False,
            preload_content=True,
            decode_content=False,
            timeout=timeout,
        )
        fields = Fields()
        for name, value in raw.headers.items():
            if name in fields:
                fields[name].add(value)
            else:
                fields[name] = Field(name=name, values=[value], kind="header")
        return HTTPResponse(
            status=raw.status, fields=fields, body=raw.data, reason=raw.reason
        )

    def close(self) -> None:
        """Close the underlying connection pool."""
        if self._closed:
            return
        self._closed = True
        self._pool.clear()

    def __enter__(self) -> Self:
        if self._closed:
            raise SmithyHTTPError("Cannot enter an HTTP client that has been closed.")
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.close()

    def __deepcopy__(self, memo: Any) -> Self:
        return self
