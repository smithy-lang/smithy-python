#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""Shared utilities for testing async smithy-python clients with an HTTP transport."""

from smithy_core.aio.utils import list_async

from .. import HTTPResponse
from ..interfaces import HTTPRequest, HTTPRequestConfiguration
from ..testing.mockhttp import MockHTTPClientBase
from .interfaces import AsyncHTTPClient

__all__ = ["AsyncMockHTTPClient"]


class AsyncMockHTTPClient(MockHTTPClientBase, AsyncHTTPClient):
    """Implementation of :py:class:`.interfaces.AsyncHTTPClient` solely for testing.

    Simulates HTTP request/response behavior. Responses are queued in FIFO order and
    requests are captured for inspection.
    """

    # Declared so duplex (bidirectional) stream operations can be unit tested
    # against this client. Queued responses are returned without consuming the
    # request body, which is compatible with duplex streaming.
    SUPPORTS_DUPLEX_STREAMING = True

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
        status, fields, body = self._pop_response(request)
        if isinstance(body, bytes | bytearray):
            body = list_async([bytes(body)])
        return HTTPResponse(status=status, fields=fields, body=body)
