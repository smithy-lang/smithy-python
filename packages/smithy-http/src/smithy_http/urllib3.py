#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from copy import copy, deepcopy
from itertools import chain
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
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
from .interfaces import HTTPClientConfiguration, HTTPRequestConfiguration


def _assert_urllib3() -> None:
    if not HAS_URLLIB3:
        raise MissingDependencyError(
            "Attempted to use the urllib3 component, but urllib3 is not installed."
        )


class Urllib3HTTPClientConfig(HTTPClientConfiguration):
    def __post_init__(self) -> None:
        _assert_urllib3()


class Urllib3HTTPClient:
    """Synchronous HTTP transport backed by urllib3.

    Structurally satisfies :py:class:`smithy_core.interfaces.ClientTransport` for
    HTTP requests/responses (synchronous ``send`` plus ``TIMEOUT_EXCEPTIONS``). The
    synchronous counterpart to :py:class:`smithy_http.aio.aiohttp.AIOHTTPClient`.
    """

    TIMEOUT_EXCEPTIONS = (urllib3.exceptions.TimeoutError,) if HAS_URLLIB3 else ()

    def __init__(
        self,
        *,
        client_config: Urllib3HTTPClientConfig | None = None,
        _pool: "urllib3.PoolManager | None" = None,
    ) -> None:
        _assert_urllib3()
        self._config = client_config or Urllib3HTTPClientConfig()
        self._closed = False
        self._pool = _pool or urllib3.PoolManager(
            headers={"Accept-Encoding": "identity"}
        )

    def send(
        self,
        request: HTTPRequest,
        *,
        request_config: HTTPRequestConfiguration | None = None,
    ) -> HTTPResponseInterface:
        """Send an HTTP request with urllib3 and return the response.

        :param request: The request including destination URI, fields, payload.
        :param request_config: Configuration specific to this request.
        """
        if self._closed:
            raise SmithyHTTPError(
                "Cannot send a request after the HTTP client has been closed."
            )

        headers = list(chain.from_iterable(fld.as_tuples() for fld in request.fields))

        raw = self._pool.request(
            request.method,
            self._serialize_uri(request.destination),
            body=request.consume_body(),
            headers=dict(headers),
            redirect=False,
            preload_content=False,
            decode_content=False,
        )
        return self._marshal_response(raw)

    def close(self) -> None:
        """Close the underlying urllib3 pool."""
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

    def _serialize_uri(self, uri: Any) -> str:
        # urllib3 takes a single URL string; query is already percent-encoded.
        base = f"{uri.scheme or 'https'}://{uri.netloc}{uri.path or '/'}"
        return f"{base}?{uri.query}" if uri.query else base

    def _marshal_response(
        self, raw: "urllib3.BaseHTTPResponse"
    ) -> HTTPResponseInterface:
        headers = Fields()
        for header_name, header_val in raw.headers.items():
            try:
                headers[header_name].add(header_val)
            except KeyError:
                headers[header_name] = Field(
                    name=header_name, values=[header_val], kind="header"
                )
        return HTTPResponse(
            status=raw.status,
            fields=headers,
            body=raw.data,
            reason=raw.reason,
        )

    def __deepcopy__(self, memo: Any) -> "Urllib3HTTPClient":
        return Urllib3HTTPClient(
            client_config=deepcopy(self._config),
            _pool=copy(self._pool),
        )
