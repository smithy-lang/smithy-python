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

AWS_JSON_10: Final = ProtocolContribution(
    protocol_id=_model.ShapeId("aws.protocols", "awsJson1_0"),
    protocol=_aws("AwsJson10ClientProtocol", "protocols", "json"),
    async_protocol=_aws("AsyncAwsJson10ClientProtocol", "aio.protocols", "json"),
    transport=RPCV2_CBOR.transport,
    async_transport=RPCV2_CBOR.async_transport,
)
"""The ``aws.protocols#awsJson1_0`` contribution."""

AWS_JSON_11: Final = ProtocolContribution(
    protocol_id=_model.ShapeId("aws.protocols", "awsJson1_1"),
    protocol=_aws("AwsJson11ClientProtocol", "protocols", "json"),
    async_protocol=_aws("AsyncAwsJson11ClientProtocol", "aio.protocols", "json"),
    transport=RPCV2_CBOR.transport,
    async_transport=RPCV2_CBOR.async_transport,
)
"""The ``aws.protocols#awsJson1_1`` contribution."""

REST_XML: Final = ProtocolContribution(
    protocol_id=_model.ShapeId("aws.protocols", "restXml"),
    protocol=_aws("RestXmlClientProtocol", "protocols", "xml"),
    async_protocol=_aws("AsyncRestXmlClientProtocol", "aio.protocols", "xml"),
    transport=RPCV2_CBOR.transport,
    async_transport=RPCV2_CBOR.async_transport,
)
"""The ``aws.protocols#restXml`` contribution."""

# The query protocols have no event streams, so async clients use the sync
# protocols, as in the Java generator.
_AWS_QUERY_PROTOCOL: Final = _aws("AwsQueryClientProtocol", "protocols", "xml")
_EC2_QUERY_PROTOCOL: Final = _aws("Ec2QueryClientProtocol", "protocols", "xml")

AWS_QUERY: Final = ProtocolContribution(
    protocol_id=_model.ShapeId("aws.protocols", "awsQuery"),
    protocol=_AWS_QUERY_PROTOCOL,
    async_protocol=_AWS_QUERY_PROTOCOL,
    transport=RPCV2_CBOR.transport,
    async_transport=RPCV2_CBOR.async_transport,
)
"""The ``aws.protocols#awsQuery`` contribution."""

EC2_QUERY: Final = ProtocolContribution(
    protocol_id=_model.ShapeId("aws.protocols", "ec2Query"),
    protocol=_EC2_QUERY_PROTOCOL,
    async_protocol=_EC2_QUERY_PROTOCOL,
    transport=RPCV2_CBOR.transport,
    async_transport=RPCV2_CBOR.async_transport,
)
"""The ``aws.protocols#ec2Query`` contribution."""

AWS_PROTOCOLS: Final[Mapping[_model.ShapeId, ProtocolContribution]] = MappingProxyType(
    {
        **DEFAULT_PROTOCOLS,
        **{
            contribution.protocol_id: contribution
            for contribution in (
                REST_JSON,
                AWS_JSON_10,
                AWS_JSON_11,
                REST_XML,
                AWS_QUERY,
                EC2_QUERY,
            )
        },
    }
)
"""The core protocols and the AWS protocols."""
