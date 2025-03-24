#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass

from smithy_core.endpoints import Endpoint
from smithy_core.interfaces import TypedProperties as _TypedProperties
from smithy_core.interfaces import URI
from smithy_core.types import PropertyKey, TypedProperties

from . import Fields, interfaces

HEADERS = PropertyKey(key="headers", value_type=interfaces.Fields)
"""An Endpoint property indicating the given fields MUST be added to the request."""


@dataclass(init=False, kw_only=True)
class HTTPEndpoint(Endpoint):
    """A resolved endpoint with optional HTTP headers."""

    def __init__(
        self,
        *,
        uri: URI,
        properties: _TypedProperties | None = None,
        headers: interfaces.Fields | None = None,
    ) -> None:
        self.uri = uri
        self.properties = properties if properties is not None else TypedProperties()
        headers = headers if headers is not None else Fields()
        self.properties[HEADERS] = headers
