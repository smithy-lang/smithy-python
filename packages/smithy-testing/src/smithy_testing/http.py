#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from collections import deque
from copy import copy

from smithy_core.aio.utils import async_list
from smithy_http import tuples_to_fields
from smithy_http.aio import HTTPResponse
from smithy_http.aio.interfaces import HTTPClient, HTTPRequest
from smithy_http.interfaces import HTTPClientConfiguration, HTTPRequestConfiguration


class MockHTTPClient(HTTPClient):
    """Implementation of :py:class:`.interfaces.HTTPClient` solely for testing purposes.

    Simulates HTTP request/response behavior.
    Responses are queued in FIFO order and requests are captured for inspection.
    """

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
        self._response_queue: deque[HTTPResponse] = deque()
        self._captured_requests: list[HTTPRequest] = []

    def add_response(
        self,
        status: int = 200,
        headers: list[tuple[str, str]] | None = None,
        body: bytes = b"",
    ) -> None:
        """Queue a response for the next request.

        :param status: HTTP status code (200, 404, 500, etc.)
        :param headers: HTTP response headers as list of (name, value) tuples
        :param body: Response body as bytes
        """
        response = HTTPResponse(
            status=status,
            fields=tuples_to_fields(headers or []),
            body=async_list([body]),
            reason=None,
        )
        self._response_queue.append(response)

    async def send(
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
        self._captured_requests.append(copy(request))

        # Return next queued response or raise error
        if self._response_queue:
            return self._response_queue.popleft()
        else:
            raise MockHTTPClientError(
                "No responses queued in MockHTTPClient. Use add_response() to queue responses."
            )

    @property
    def call_count(self) -> int:
        """The number of requests made to this client."""
        return len(self._captured_requests)

    @property
    def captured_requests(self) -> list[HTTPRequest]:
        """The list of all requests captured by this client."""
        return self._captured_requests.copy()


class MockHTTPClientError(Exception):
    """Exception raised by MockHTTPClient for test setup issues."""
