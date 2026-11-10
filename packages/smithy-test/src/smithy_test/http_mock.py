#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
# pyright: reportPrivateUsage=false
from collections.abc import Callable, Mapping
from copy import copy
from types import TracebackType
from typing import Any, Self

from smithy_core.client import Client
from smithy_core.exceptions import SmithyError
from smithy_core.interfaces import AnyStreamingBlob
from smithy_core.utils import read_streaming_blob
from smithy_http import HTTPResponse
from smithy_http.interfaces import HTTPClient, HTTPRequest, HTTPRequestConfiguration
from smithy_http.testing.mockhttp import MockHTTPClient, MockHTTPClientBase

from ._private.http_mock import NoResponse, mismatches, take_over

__all__ = [
    "HTTPMockController",
    "HTTPMockError",
    "HTTPMockExpectation",
    "HTTPMockMismatchError",
    "mock",
]

type _Matcher[T] = str | Callable[[T], bool | None]
"""An exact string, a ``"/regex/"`` string, or a callable returning True or None."""

type _EntriesMatcher = (
    Mapping[str, _Matcher[str]] | Callable[[dict[str, str]], bool | None]
)

type _ResponseBody = str | AnyStreamingBlob


def mock[C](client: Client[C]) -> "HTTPMockController":
    """Take over a client so its requests are matched and answered, never sent.

    :raises TypeError: If the client isn't a sync client this mock can take over.
    """
    if not isinstance(client, Client):  # pyright: ignore[reportUnnecessaryIsInstance]
        raise TypeError(
            f"mock() takes a sync client, got {type(client).__name__}. Use "
            "smithy_test.aio.mock_async() for async clients."
        )
    controller = HTTPMockController()
    controller._capture = _MockTransport(controller)
    take_over(client, controller._capture, _none_without_response)
    return controller


class HTTPMockController:
    """Matches, answers and records the requests of a client taken over by a mock.

    Used as a context manager, it raises on exit if an expectation wasn't met.
    """

    def __init__(self) -> None:
        self._expectations: list[HTTPMockExpectation] = []
        self._capture: MockHTTPClientBase | None = None
        self._position = 0

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        # An error raised in the block is the more useful one to report.
        if exc_type is not None:
            return
        unmet = [
            f"Expectation {i}: matched {e._used} of {e._times} requests"
            for i, e in enumerate(self._expectations, start=1)
            if e._used < e._times
        ]
        if unmet:
            raise HTTPMockMismatchError(
                "\n  ".join(["Not every expected request was sent:", *unmet])
            )

    @property
    def requests(self) -> list[HTTPRequest]:
        """The requests the client sent, with their bodies read into bytes."""
        return self._capture.captured_requests if self._capture else []

    def expect_request(
        self,
        *,
        method: _Matcher[str] | None = None,
        scheme: _Matcher[str] | None = None,
        hostname: _Matcher[str] | None = None,
        port: _Matcher[int | None] | None = None,
        path: _Matcher[str] | None = None,
        query: _EntriesMatcher | None = None,
        headers: _EntriesMatcher | None = None,
        body: _Matcher[bytes] | None = None,
    ) -> "HTTPMockExpectation":
        """Expect the next request; the last expectation matches all later ones."""
        components = {
            "method": method,
            "scheme": scheme,
            "hostname": hostname,
            "port": port,
            "path": path,
            "query": query,
            "headers": headers,
            "body": body,
        }
        expectation = HTTPMockExpectation(
            {name: m for name, m in components.items() if m is not None}
        )
        self._expectations.append(expectation)
        return expectation

    def _exchange(
        self, request: HTTPRequest, body: bytes, number: int
    ) -> tuple[int, list[tuple[str, str]], AnyStreamingBlob]:
        """Match a request, then return the status, headers and body to answer it.

        :raises HTTPMockError: If no requests are expected.
        :raises HTTPMockMismatchError: If the request doesn't match its expectation.
        :raises NoResponse: If the matching expectation has no response.
        """
        expectations = self._expectations
        if not expectations:
            raise HTTPMockError(
                f"Request {number} was sent, but no requests were expected. Call "
                "expect_request() before invoking the client."
            )
        while (
            self._position < len(expectations) - 1
            and expectations[self._position]._used
            >= expectations[self._position]._times
        ):
            self._position += 1
        expectation = expectations[self._position]
        failures, cause = mismatches(expectation._matchers, request, body)
        if failures:
            heading = f"Request {number} didn't match expectation {self._position + 1}:"
            raise HTTPMockMismatchError("\n  ".join([heading, *failures])) from cause
        return expectation._respond()


class HTTPMockExpectation:
    """An expected request and the responses to it."""

    def __init__(self, matchers: dict[str, Any]) -> None:
        self._matchers = matchers
        self._times = 1
        self._used = 0
        self._responses: list[tuple[int, list[tuple[str, str]], _ResponseBody]] = []

    def times(self, n: int) -> Self:
        """Expect this request ``n`` times in a row."""
        self._times = n
        return self

    def respond_with(
        self,
        status_code: int = 200,
        headers: Mapping[str, str] | None = None,
        body: _ResponseBody = b"",
    ) -> Self:
        """Queue a response; the last response answers all later requests."""
        self._responses.append((status_code, list((headers or {}).items()), body))
        return self

    def _respond(self) -> tuple[int, list[tuple[str, str]], AnyStreamingBlob]:
        self._used += 1
        if not self._responses:
            raise NoResponse()
        index = min(self._used, len(self._responses)) - 1
        status, headers, body = self._responses[index]
        if isinstance(body, str):
            body = body.encode("utf-8")
        return status, headers, body


class HTTPMockError(SmithyError):
    """Raised when a mocked client sends a request without any expectations."""


# A SmithyError so the pipeline raises it as is instead of wrapping it.
class HTTPMockMismatchError(SmithyError, AssertionError):
    """Raised when a mocked client's requests don't meet its expectations."""


class _MockTransport(MockHTTPClient):
    """Queues the controller's response for each request, then answers with it."""

    def __init__(self, controller: HTTPMockController) -> None:
        super().__init__()
        self._controller = controller
        self.displaced: list[HTTPClient] = []

    def send(
        self,
        request: HTTPRequest,
        *,
        request_config: HTTPRequestConfiguration | None = None,
    ) -> HTTPResponse:
        captured = copy(request)
        captured.body = read_streaming_blob(request.body)
        try:
            status, headers, body = self._controller._exchange(
                captured, captured.body, self.call_count + 1
            )
        except Exception:
            # Unanswered requests are captured too, since send() only captures
            # requests it answers.
            self._captured_requests.append(captured)
            raise
        self.add_response(status, headers, body)
        return super().send(captured, request_config=request_config)

    def close(self) -> None:
        for transport in self.displaced:
            # HTTPClient doesn't declare close; the client closes it the same way.
            if (close := getattr(transport, "close", None)) is not None:
                close()


def _none_without_response(invoke: Callable[..., Any]) -> Callable[..., Any]:
    def _invoke(*args: Any, **kwargs: Any) -> Any:
        try:
            return invoke(*args, **kwargs)
        except NoResponse:
            return None

    return _invoke
