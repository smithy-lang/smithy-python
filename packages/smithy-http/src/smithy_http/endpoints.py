#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass, field
from typing import Protocol, Self

from smithy_core.interfaces import URI

from . import Fields, interfaces
from .aio.interfaces import EndpointParameters


@dataclass
class Endpoint(interfaces.Endpoint):
    uri: URI
    headers: interfaces.Fields = field(default_factory=Fields)


class _UriConfig(Protocol):
    endpoint_uri: str | URI | None


@dataclass
class StaticEndpointParams(EndpointParameters[_UriConfig]):
    """Static endpoint params.

    :param uri: A static URI to route requests to.
    """

    uri: str | URI | None

    @classmethod
    def build(cls, config: _UriConfig) -> Self:
        return cls(uri=config.endpoint_uri)
