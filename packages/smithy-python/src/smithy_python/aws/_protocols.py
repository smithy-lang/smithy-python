# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""AWS protocols for generated clients."""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Final

from .. import model as _model
from ..dependencies import Dependency
from ..protocols import DEFAULT_PROTOCOLS, RPCV2_CBOR, ProtocolContribution
from ..symbols import TypeReference
from ._dependencies import SMITHY_AWS_CORE


def _aws(name: str, module: str, extra: str) -> TypeReference:
    return TypeReference(
        name,
        f"smithy_aws_core.{module}",
        dependencies=(
            Dependency(
                package=SMITHY_AWS_CORE.package,
                specifier=SMITHY_AWS_CORE.specifier,
                group="runtime",
                extras=(extra,),
            ),
        ),
    )


REST_JSON: Final = ProtocolContribution(
    protocol_id=_model.ShapeId("aws.protocols", "restJson1"),
    protocol=_aws("RestJsonClientProtocol", "protocols", "json"),
    async_protocol=_aws("AsyncRestJsonClientProtocol", "aio.protocols", "json"),
    transport=RPCV2_CBOR.transport,
    async_transport=RPCV2_CBOR.async_transport,
)
"""The ``aws.protocols#restJson1`` contribution."""

AWS_PROTOCOLS: Final[Mapping[_model.ShapeId, ProtocolContribution]] = MappingProxyType(
    {**DEFAULT_PROTOCOLS, REST_JSON.protocol_id: REST_JSON}
)
"""The core protocols and the AWS protocols."""
