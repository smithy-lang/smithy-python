#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
# pyright: reportPrivateUsage=false
import asyncio
import contextlib
from collections.abc import Callable
from copy import copy
from dataclasses import dataclass
from types import TracebackType
from typing import Any, Self

from smithy_core.aio.client import AsyncClient
from smithy_core.aio.types import AsyncBytesProvider
from smithy_core.aio.utils import read_streaming_blob_async
from smithy_http import HTTPResponse
from smithy_http.aio.interfaces import AsyncHTTPClient
from smithy_http.aio.testing import AsyncMockHTTPClient
from smithy_http.interfaces import HTTPRequest, HTTPRequestConfiguration

from .._private.http_mock import NoResponse, take_over
from ..http_mock import HTTPMockController, HTTPMockError

__all__ = ["AsyncHTTPMockController", "mock_async"]


async def mock_async[C](client: AsyncClient[C]) -> "AsyncHTTPMockController":
    """Take over a client so its requests are matched and answered, never sent.

    :raises TypeError: If the client isn't an async client this mock can take over.
    """
    if not isinstance(client, AsyncClient):  # pyright: ignore[reportUnnecessaryIsInstance]
        raise TypeError(
            f"mock_async() takes an async client, got {type(client).__name__}. Use "
            "smithy_test.mock() for sync clients."
        )
    controller = AsyncHTTPMockController()
    controller._capture = _AsyncMockTransport(controller)
    take_over(client, controller._capture, _none_without_response)
    return controller


class AsyncHTTPMockController(HTTPMockController):
    """An :py:class:`HTTPMockController` for async clients.

    Event stream requests are answered as soon as they're sent, and their bodies are
    read while the client streams events. Used as an async context manager, it waits
    for those bodies on exit before checking them against their expectations.
    """

    def __init__(self) -> None:
        super().__init__()
        self._streams: list[_StreamRead] = []

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        for stream in self._streams:
            if exc_type is None and stream.body.closed:
                await stream.task
            elif not stream.task.done():
                stream.task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await stream.task
                self._late_failures.append(
                    f"Request {stream.number}'s event stream wasn't closed, so its "
                    "body wasn't checked."
                )
        self.__exit__(exc_type, exc_value, traceback)

    def _read_stream(
        self, number: int, request: HTTPRequest, body: AsyncBytesProvider
    ) -> None:
        async def read() -> None:
            request.body = await read_streaming_blob_async(body)
            self._check_body(number, request, request.body)

        self._streams.append(_StreamRead(number, body, asyncio.create_task(read())))

    def _unmet(self) -> list[str]:
        unread = [
            f"Request {s.number}'s event stream is still being read; exit with "
            "`async with` to wait for it."
            for s in self._streams
            if not s.task.done()
        ]
        return [*unread, *super()._unmet()]


@dataclass(frozen=True)
class _StreamRead:
    number: int
    body: AsyncBytesProvider
    task: "asyncio.Task[None]"


class _AsyncMockTransport(AsyncMockHTTPClient):
    """Queues the controller's response for each request, then answers with it."""

    def __init__(self, controller: AsyncHTTPMockController) -> None:
        super().__init__()
        self._controller = controller
        self.displaced: list[AsyncHTTPClient] = []

    async def send(
        self,
        request: HTTPRequest,
        *,
        request_config: HTTPRequestConfiguration | None = None,
    ) -> HTTPResponse:
        captured = copy(request)
        body = request.body
        # An event stream body is written until the client closes the stream, which
        # it can wait to do until it has the response.
        stream = isinstance(body, AsyncBytesProvider)
        if stream:
            captured.body = b""
            self._controller._read_stream(self.call_count + 1, captured, body)
        else:
            captured.body = await read_streaming_blob_async(body)
        number = self.call_count + 1
        try:
            status, headers, response_body = self._controller._exchange(
                captured, None if stream else captured.body, number
            )
        except NoResponse:
            self._captured_requests.append(captured)
            if not stream:
                raise
            raise HTTPMockError(
                f"Request {number} opened an event stream, which can't end without "
                "a response. Call respond_with() on its expectation."
            ) from None
        except Exception:
            # Unanswered requests are captured too, since send() only captures
            # requests it answers.
            self._captured_requests.append(captured)
            raise
        self.add_response(status, headers, response_body)
        response = await super().send(captured, request_config=request_config)
        # send() captures a copy; keep this one, whose body the stream read fills in.
        self._captured_requests[-1] = captured
        return response

    async def close(self) -> None:
        for transport in self.displaced:
            # AsyncHTTPClient doesn't declare close; the client closes it the same way.
            if (close := getattr(transport, "close", None)) is not None:
                await close()


def _none_without_response(invoke: Callable[..., Any]) -> Callable[..., Any]:
    async def _invoke(*args: Any, **kwargs: Any) -> Any:
        try:
            return await invoke(*args, **kwargs)
        except NoResponse:
            return None

    return _invoke
