# Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

from urllib.parse import parse_qs, urlunparse

import aiohttp

from ...interfaces.http import URI, HttpRequestConfiguration
from . import Request, Response


class AioHttpClient:
    """Implementation of :py:class:`...interfaces.http.HttpClient` using aiohttp."""

    def __init__(self) -> None:
        self._session = aiohttp.ClientSession()

    async def send(
        self, request: Request, request_config: HttpRequestConfiguration | None = None
    ) -> Response:
        """Send HTTP request using aiohttp client."""
        request_config = (
            HttpRequestConfiguration() if request_config is None else request_config
        )
        async with self._session.request(
            method=request.method,
            url=self._serialize_url_without_query(request.url),
            params=parse_qs(request.url.query),
            headers=request.headers,
            data=request.body,
        ) as resp:
            return await self._marshal_response(resp)

    def _serialize_url_without_query(self, url: URI) -> str:
        components = (url.scheme, url.host, url.path, "", "", "")
        return urlunparse(components)

    async def _marshal_response(self, aiohttp_resp: aiohttp.ClientResponse) -> Response:
        """Convert a ``aiohttp.ClientResponse`` to a ``smithy_python.http.Response``"""
        headers = [(k, v) for k, v in aiohttp_resp.headers.items()]
        return Response(
            status_code=aiohttp_resp.status,
            headers=headers,
            body=await aiohttp_resp.read(),
        )
