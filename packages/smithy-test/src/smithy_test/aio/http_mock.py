#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
# pyright: reportPrivateUsage=false
from collections.abc import Callable
from copy import copy
from typing import Any

from smithy_core.aio.client import AsyncClient
from smithy_core.aio.utils import read_streaming_blob_async
from smithy_http import HTTPResponse
from smithy_http.aio.interfaces import AsyncHTTPClient
from smithy_http.aio.testing import AsyncMockHTTPClient
from smithy_http.interfaces import HTTPRequest, HTTPRequestConfiguration

from .._private.http_mock import NoResponse, take_over
from ..http_mock import HTTPMockController

__all__ = ["mock_async"]


async def mock_async[C](client: AsyncClient[C]) -> HTTPMockController:
    """Take over a client so its requests are matched and answered, never sent.

    :raises TypeError: If the client isn't an async client this mock can take over.
    """
    if not isinstance(client, AsyncClient):  # pyright: ignore[reportUnnecessaryIsInstance]
        raise TypeError(
            f"mock_async() takes an async client, got {type(client).__name__}. Use "
            "smithy_test.mock() for sync clients."
        )
    controller = HTTPMockController()
    controller._capture = _AsyncMockTransport(controller)
    take_over(client, controller._capture, _none_without_response)
    return controller


class _AsyncMockTransport(AsyncMockHTTPClient):
    """Queues the controller's response for each request, then answers with it."""

    def __init__(self, controller: HTTPMockController) -> None:
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
        captured.body = await read_streaming_blob_async(request.body)
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
        return await super().send(captured, request_config=request_config)

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
