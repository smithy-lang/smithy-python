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
from typing import Any, Protocol
from urllib.parse import parse_qsl, urlparse

from smithy_python.interfaces import http as http_interface


class URL:
    def __init__(
        self,
        host: str,
        path: str | None = None,
        scheme: str | None = None,
        query_params: http_interface.QueryParamsList | None = None,
        port: int | None = None,
    ):
        self.scheme: str = "https" if scheme is None else scheme
        self.username: str | None = None
        self.password: str | None = None
        self.host = host
        self.port = port
        self.path = path
        self.query_params: http_interface.QueryParamsList = (
            [] if query_params is None else query_params
        )
        self.fragment: str | None = None

    @property
    def query(self) -> str | None:
        """Construct string representation of the query component of a URI."""
        if not self.query_params:
            return None
        return urlencode(self.query_params)

    @query.setter
    def query(self, new_query: str) -> None:
        self.query_params = parse_qsl(new_query)

    def build(self) -> str:
        """Construct URI string representation.

        Returns a string of the form
        ``{scheme}://{username}:{password}@{host}:{port}{path}?{query}#{fragment}``
        """
        components = (
            self.scheme,
            self.host,
            self.path or "",
            "",  # params
            self.query,
            self.fragment,
            self.username,
            self.password,
        )
        return urlunparse(components)


class Request:
    def __init__(
        self,
        url: http_interface.URI,
        method: str = "GET",
        headers: http_interface.HeadersList | None = None,
        body: Any = None,
    ):
        self.url: http_interface.URI = url
        self.method: str = method
        self.body: Any = body

        self.headers: http_interface.HeadersList = []
        if headers is not None:
            self.headers = headers


class Response:
    def __init__(
        self,
        status_code: int,
        headers: http_interface.HeadersList,
        body: Any,
    ):
        self.status_code: int = status_code
        self.headers: http_interface.HeadersList = headers
        self.body: Any = body


@dataclass
class Endpoint(http_interface.Endpoint):
    url: http_interface.URI
    headers: http_interface.HeadersList = field(default_factory=list)


@dataclass
class StaticEndpointParams:
    """
    Static endpoint params.

    :params url: A static URL to route requests to.
    """

    url: str | http_interface.URI


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
                host=parsed.hostname,
                path=parsed.path,
                scheme=parsed.scheme,
                query_params=parse_qsl(parsed.query),
                port=parsed.port,
            )
        )


class _StaticEndpointConfig(Protocol):
    endpoint_resolver: http_interface.EndpointResolver[StaticEndpointParams] | None


def set_static_endpoint_resolver(config: _StaticEndpointConfig) -> None:
    """
    Sets the endpoint resolver to the static endpoint resolver if not already set.

    :param config: A config object that has an endpoint_resolver property.
    """
    if config.endpoint_resolver is None:
        config.endpoint_resolver = StaticEndpointResolver()
