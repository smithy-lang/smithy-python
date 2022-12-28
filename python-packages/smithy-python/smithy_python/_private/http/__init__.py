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
from urllib.parse import urlparse, urlunparse

from smithy_python.interfaces import http as http_interface


class URI:
    def __init__(
        self,
        host: str,
        path: str | None = None,
        scheme: str | None = None,
        query: str | None = None,
        port: int | None = None,
        username: str | None = None,
        password: str | None = None,
        fragment: str | None = None,
    ):
        self.scheme: str = "https" if scheme is None else scheme
        self.host = host
        self.port = port
        self.path = path
        self.query = query
        self.username = username
        self.password = password
        self.fragment = fragment

    @property
    def netloc(self) -> str:
        """Construct netloc string in format ``{username}:{password}@{host}:{port}``

        ``username``, ``password``, and ``port`` are only included if set. ``password``
        is ignored, unless ``username`` is also set.
        """
        if self.username is not None:
            password = "" if self.password is None else f":{self.password}"
            userinfo = f"{self.username}{password}@"
        else:
            userinfo = ""
        port = "" if self.port is None else f":{self.port}"
        return f"{userinfo}{self.host}{port}"

    def build(self) -> str:
        """Construct URI string representation.

        Returns a string of the form
        ``{scheme}://{username}:{password}@{host}:{port}{path}?{query}#{fragment}``
        """
        components = (
            self.scheme,
            self.netloc,
            self.path or "",
            "",  # params
            self.query,
            self.fragment,
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

    :params url: A static URI to route requests to.
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
            url=URI(
                host=parsed.hostname,
                path=parsed.path,
                scheme=parsed.scheme,
                query=parsed.query,
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
