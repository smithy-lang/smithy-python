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
from itertools import chain
from urllib.parse import parse_qs, urlunparse

import aiohttp

from ... import interfaces
from ...async_utils import async_list
from . import Field, FieldPosition, Fields, HttpResponse


class AwsCrtHttpClientConfig(interfaces.http.HttpClientConfiguration):
    pass


class AioHttpClient(interfaces.http.HttpClient):
    """Implementation of :py:class:`...interfaces.http.HttpClient` using aiohttp."""

    def __init__(self, *, client_config: AwsCrtHttpClientConfig | None) -> None:
        """
        :param client_config: Configuration that applies to all requests made with this
        client.
        """
        self._config = (
            AwsCrtHttpClientConfig() if client_config is None else client_config
        )
        self._session = aiohttp.ClientSession()

    async def send(
        self,
        *,
        request: interfaces.http.HttpRequest,
        request_config: interfaces.http.HttpRequestConfiguration | None = None,
    ) -> HttpResponse:
        """
        Send HTTP request using aiohttp client.

        :param request: The request including destination URI, fields, payload.
        :param request_config: Configuration specific to this request.
        """
        request_config = (
            interfaces.http.HttpRequestConfiguration()  # todo: should be an implementation
            if request_config is None
            else request_config
        )

        headers_list = list(
            chain.from_iterable(
                fld.as_tuples()
                for fld in request.fields.get_by_type(FieldPosition.HEADER)
            )
        )

        async with self._session.request(
            method=request.method,
            url=self._serialize_url_without_query(request.destination),
            params=parse_qs(request.destination.query),
            headers=headers_list,
            data=await request.consume_body(),
        ) as resp:
            return await self._marshal_response(resp)

    def _serialize_url_without_query(self, url: interfaces.URI) -> str:
        """Serialize all parts of the URL up to and including the path."""
        components = (url.scheme, url.host, url.path or "", "", "", "")
        return urlunparse(components)

    async def _marshal_response(
        self, aiohttp_resp: aiohttp.ClientResponse
    ) -> HttpResponse:
        """Convert a ``aiohttp.ClientResponse`` to a ``smithy_python.http.HttpResponse``"""
        headers = Fields()
        for header_name, header_val in aiohttp_resp.headers.items():
            try:
                headers.get_field(header_name).add(header_val)
            except KeyError:
                headers.set_field(
                    Field(
                        name=header_name,
                        values=[header_val],
                        kind=FieldPosition.HEADER,
                    )
                )

        return HttpResponse(
            status=aiohttp_resp.status,
            fields=headers,
            body=async_list([await aiohttp_resp.read()]),
        )
