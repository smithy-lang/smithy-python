# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Protocol contributions to generated clients, keyed by modeled protocol ID."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from . import dependencies as _dependencies
from . import exceptions as _exceptions
from . import model as _model
from . import symbols as _symbols

__all__ = [
    "DEFAULT_PROTOCOLS",
    "RPCV2_CBOR",
    "RPCV2_JSON",
    "ProtocolContribution",
    "select_protocol",
]


@dataclass(frozen=True, slots=True)
class ProtocolContribution:
    """The runtime parts a generated client uses for one modeled protocol."""

    protocol_id: _model.ShapeId
    protocol: _symbols.TypeReference
    async_protocol: _symbols.TypeReference
    transport: _symbols.TypeReference
    async_transport: _symbols.TypeReference


def _http(name: str, module: str, extra: str) -> _symbols.TypeReference:
    return _symbols.TypeReference(
        name,
        f"smithy_http.{module}",
        dependencies=(
            _dependencies.Dependency(
                package=_dependencies.SMITHY_HTTP.package,
                specifier=_dependencies.SMITHY_HTTP.specifier,
                group="runtime",
                extras=(extra,),
            ),
        ),
    )


# Each reference records the smithy-http extra it needs, so a client's package
# requires its protocol's codec extra and both default transports' extras.
_URLLIB3: Final = _http("Urllib3HTTPClient", "urllib3", "urllib3")
_AIOHTTP: Final = _http("AIOHTTPClient", "aio.aiohttp", "aiohttp")

RPCV2_CBOR: Final = ProtocolContribution(
    protocol_id=_model.ShapeId("smithy.protocols", "rpcv2Cbor"),
    protocol=_http("RpcV2CborClientProtocol", "protocols", "cbor"),
    async_protocol=_http("AsyncRpcV2CborClientProtocol", "aio.protocols", "cbor"),
    transport=_URLLIB3,
    async_transport=_AIOHTTP,
)
"""The built-in ``smithy.protocols#rpcv2Cbor`` contribution."""

RPCV2_JSON: Final = ProtocolContribution(
    protocol_id=_model.ShapeId("smithy.protocols", "rpcv2Json"),
    protocol=_http("RpcV2JsonClientProtocol", "protocols", "json"),
    async_protocol=_http("AsyncRpcV2JsonClientProtocol", "aio.protocols", "json"),
    transport=_URLLIB3,
    async_transport=_AIOHTTP,
)
"""The built-in ``smithy.protocols#rpcv2Json`` contribution."""

DEFAULT_PROTOCOLS: Final[Mapping[_model.ShapeId, ProtocolContribution]] = (
    MappingProxyType(
        {
            contribution.protocol_id: contribution
            for contribution in (RPCV2_CBOR, RPCV2_JSON)
        }
    )
)
"""Protocols supported by client generation."""


def select_protocol(
    service: _model.ServiceShape,
    selected: _model.ShapeId | None,
    registry: Mapping[_model.ShapeId, ProtocolContribution] = DEFAULT_PROTOCOLS,
) -> ProtocolContribution:
    """Choose the protocol a client uses.

    A selected protocol must be a trait on the service and in the registry.
    Without one, the service must have exactly one protocol trait in the
    registry. Candidates are ordered by shape ID, never by discovery order.

    :raises CodegenError: If no protocol, or more than one, can be chosen.
    """
    supported = sorted(
        (trait_id for trait_id in service.traits if trait_id in registry), key=str
    )
    if selected is not None:
        if selected not in service.traits:
            raise _exceptions.CodegenError(
                f"Protocol {selected} is not a trait on service {service.id}"
            )
        if selected not in registry:
            raise _exceptions.CodegenError(
                f"Protocol {selected} is not supported. Supported protocols: "
                f"{_names(registry)}"
            )
        return registry[selected]
    if len(supported) == 1:
        return registry[supported[0]]
    if supported:
        raise _exceptions.CodegenError(
            f"Service {service.id} has more than one supported protocol: "
            f"{', '.join(map(str, supported))}. Select one with --protocol"
        )
    raise _exceptions.CodegenError(
        f"Service {service.id} has no supported protocol. Supported protocols: "
        f"{_names(registry)}"
    )


def _names(registry: Mapping[_model.ShapeId, ProtocolContribution]) -> str:
    return ", ".join(sorted(map(str, registry))) or "none"
