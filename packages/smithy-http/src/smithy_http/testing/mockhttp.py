#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from collections import deque
from copy import copy
from typing import Any

from smithy_core.aio.utils import async_list

from smithy_http import tuples_to_fields
from smithy_http.aio import HTTPResponse
from smithy_http.aio.interfaces import HTTPClient, HTTPRequest
from smithy_http.interfaces import HTTPClientConfiguration, HTTPRequestConfiguration


class MockHTTPClient(HTTPClient):
    """Implementation of :py:class:`.interfaces.HTTPClient` solely for testing purposes.

    Simulates HTTP request/response behavior. Responses are queued in FIFO order and
    requests are captured for inspection.
    """

    TIMEOUT_EXCEPTIONS = (TimeoutError,)

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
        self._response_queue: deque[dict[str, Any]] = deque()
        self._captured_requests: list[HTTPRequest] = []

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
        self._response_queue.append(
            {
                "status": status,
                "headers": headers or [],
                "body": body,
            }
        )

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
            response_data = self._response_queue.popleft()
            return HTTPResponse(
                status=response_data["status"],
                fields=tuples_to_fields(response_data["headers"]),
                body=async_list([response_data["body"]]),
                reason=None,
            )
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

    def __deepcopy__(self, memo: Any) -> "MockHTTPClient":
        return self


class MockHTTPClientError(Exception):
    """Exception raised by MockHTTPClient for test setup issues."""
