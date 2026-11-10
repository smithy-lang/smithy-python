#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from collections import deque
from copy import copy
from io import BytesIO
from typing import Any, Self

from smithy_http import HTTPResponse, tuples_to_fields
from smithy_http.interfaces import (
    Fields,
    HTTPClient,
    HTTPClientConfiguration,
    HTTPRequest,
    HTTPRequestConfiguration,
)

__all__ = ["MockHTTPClient", "MockHTTPClientBase", "MockHTTPClientError"]


class MockHTTPClientBase:
    """Queued responses and captured requests, shared by the sync and async mocks.

    Simulates HTTP request/response behavior. Responses are queued in FIFO order and
    requests are captured for inspection.
    """

    TIMEOUT_EXCEPTIONS: tuple[type[Exception], ...] = (TimeoutError,)

    def __init__(
        self,
        *,
        client_config: HTTPClientConfiguration | None = None,
    ) -> None:
        """
        :param client_config: Configuration that applies to all requests made with this
        client.
        """
        self._client_config = client_config
        self._responses: deque[tuple[int, Fields, bytes]] = deque()
        self._captured_requests: list[HTTPRequest] = []

    def __deepcopy__(self, memo: Any) -> Self:
        return self

    @property
    def call_count(self) -> int:
        """The number of requests made to this client."""
        return len(self._captured_requests)

    @property
    def captured_requests(self) -> list[HTTPRequest]:
        """The list of all requests captured by this client."""
        return self._captured_requests.copy()

    def add_response(
        self,
        status: int = 200,
        headers: list[tuple[str, str]] | None = None,
        body: bytes = b"",
    ) -> None:
        """Queue a response for the next request.

        :param status: HTTP status code.
        :param headers: HTTP response headers as list of (name, value) tuples.
        :param body: Response body as bytes.
        """
        self._responses.append((status, tuples_to_fields(headers or []), body))

    def _pop_response(self, request: HTTPRequest) -> tuple[int, Fields, bytes]:
        """Capture the request and return the next queued status, fields and body.

        :raises MockHTTPClientError: If no responses are queued.
        """
        self._captured_requests.append(copy(request))
        if not self._responses:
            raise MockHTTPClientError(
                f"No responses queued in {type(self).__name__}. Use add_response() to "
                "queue responses."
            )
        return self._responses.popleft()


class MockHTTPClient(MockHTTPClientBase, HTTPClient):
    """Implementation of :py:class:`.interfaces.HTTPClient` solely for testing purposes.

    For async clients, use :py:class:`smithy_http.aio.testing.AsyncMockHTTPClient`.
    """

    def send(
        self,
        request: HTTPRequest,
        *,
        request_config: HTTPRequestConfiguration | None = None,
    ) -> HTTPResponse:
        """Send HTTP request and return configured response.

        :param request: The request including destination URI, fields, payload.
        :param request_config: Configuration specific to this request.
        :returns: Pre-configured HTTP response from the queue.
        :raises MockHTTPClientError: If no responses are queued.
        """
        status, fields, body = self._pop_response(request)
        return HTTPResponse(status=status, fields=fields, body=BytesIO(body))


class MockHTTPClientError(Exception):
    """Exception raised by the mock HTTP clients for test setup issues."""
