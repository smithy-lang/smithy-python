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


def _http(name: str, module: str) -> _symbols.TypeReference:
    return _symbols.TypeReference(
        name,
        f"smithy_http.{module}",
        dependencies=(
            _dependencies.Dependency(
                package=_dependencies.SMITHY_HTTP.package,
                specifier=_dependencies.SMITHY_HTTP.specifier,
                group="runtime",
                extras=("aiohttp", "cbor", "urllib3"),
            ),
        ),
    )


RPCV2_CBOR: Final = ProtocolContribution(
    protocol_id=_model.ShapeId("smithy.protocols", "rpcv2Cbor"),
    protocol=_http("RpcV2CborClientProtocol", "protocols"),
    async_protocol=_http("AsyncRpcV2CborClientProtocol", "aio.protocols"),
    transport=_http("Urllib3HTTPClient", "urllib3"),
    async_transport=_http("AIOHTTPClient", "aio.aiohttp"),
)
"""The built-in ``smithy.protocols#rpcv2Cbor`` contribution."""

DEFAULT_PROTOCOLS: Final[Mapping[_model.ShapeId, ProtocolContribution]] = (
    MappingProxyType({RPCV2_CBOR.protocol_id: RPCV2_CBOR})
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
