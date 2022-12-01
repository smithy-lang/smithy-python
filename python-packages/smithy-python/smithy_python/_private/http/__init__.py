# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

# TODO: move all of this out of _private


from dataclasses import dataclass, field
from typing import Any
from urllib.parse import parse_qsl, urlparse

from smithy_python.interfaces import http as http_interface

HeadersList = list[tuple[str, str]]
QueryParamsList = list[tuple[str, str]]


class URL:
    def __init__(
        self,
        hostname: str,
        path: str | None = None,
        scheme: str | None = None,
        query_params: QueryParamsList | None = None,
        port: int | None = None,
    ):
        self.hostname: str = hostname
        self.port: int | None = port

        self.path: str = ""
        if path is not None:
            self.path = path

        self.scheme: str = "https"
        if scheme is not None:
            self.scheme = scheme

        self.query_params: QueryParamsList = []
        if query_params is not None:
            self.query_params = query_params


class Request:
    def __init__(
        self,
        url: http_interface.URL,
        method: str = "GET",
        headers: HeadersList | None = None,
        body: Any = None,
    ):
        self.url: http_interface.URL = url
        self.method: str = method
        self.body: Any = body

        self.headers: HeadersList = []
        if headers is not None:
            self.headers = headers


class Response:
    def __init__(
        self,
        status_code: int,
        headers: HeadersList,
        body: Any,
    ):
        self.status_code: int = status_code
        self.headers: HeadersList = headers
        self.body: Any = body


@dataclass
class Endpoint(http_interface.Endpoint):
    url: URL
    headers: HeadersList = field(default_factory=list)


@dataclass
class StaticEndpointParams:
    """
    Static endpoint params.

    :params url: A static URL to route requests to.
    """

    url: str | URL


class StaticEndpointResolver(http_interface.EndpointResolver[StaticEndpointParams]):
    """A basic endpoint resolver that forwards a static url."""

    async def resolve_endpoint(self, params: StaticEndpointParams) -> Endpoint:
        # If it's not a string, it's already a parsed URL so just pass it along.
        if not isinstance(params.url, str):
            return Endpoint(url=params.url)

        # Does crt have implementations of these parsing methods? Using the standard
        # library is probably fine.
        parsed = urlparse(params.url)

        # This will end up getting wrapped in the client.
        if parsed.hostname is None:
            raise ValueError(
                f"Unable to parse hostname from provided url: {params.url}"
            )

        return Endpoint(
            url=URL(
                hostname=parsed.hostname,
                path=parsed.path,
                scheme=parsed.scheme,
                query_params=parse_qsl(parsed.query),
                port=parsed.port,
            )
        )
