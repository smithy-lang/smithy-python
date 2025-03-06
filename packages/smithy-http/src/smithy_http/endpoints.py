#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass, field

from smithy_core import SmithyException
from smithy_core.interfaces import URI

from . import Fields, interfaces


@dataclass
class Endpoint(interfaces.Endpoint):
    uri: URI
    headers: interfaces.Fields = field(default_factory=Fields)


class EndpointResolutionError(SmithyException):
    """Exception type for all exceptions raised by endpoint resolution."""

@dataclass
class StaticEndpointParams:
    """Static endpoint params.

    :param uri: A static URI to route requests to.
    """

    uri: str | URI | None
