from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, cast

from smithy_core.auth import DefaultAuthResolver
from smithy_core.endpoints import StaticEndpointResolver
from smithy_core.interceptors import Interceptor
from smithy_core.interfaces import (
    ClientProtocol,
    ClientTransport,
    EndpointResolver,
    ProtocolConstructor,
    ProtocolSettings,
    URI,
)
from smithy_core.interfaces.auth import AuthScheme, AuthSchemeResolver
from smithy_core.interfaces.retries import RetryStrategy
from smithy_core.retries import RetryStrategyOptions
from smithy_core.shapes import ShapeID
from smithy_http.protocols import RpcV2CborClientProtocol
from smithy_http.urllib3 import Urllib3HTTPClient

from rpcv2cbor_client._private.schemas import RPC_V2_PROTOCOL

_PROTOCOL_SETTINGS = ProtocolSettings(
    namespace="smithy.protocoltests.rpcv2Cbor",
    service_target="RpcV2Protocol",
    version="2020-07-14",
    service_schema=RPC_V2_PROTOCOL,
)


@dataclass(init=False)
class Config:
    "Configuration for RpcV2Protocol."

    auth_scheme_resolver: AuthSchemeResolver
    "Determines the auth scheme for each operation."

    auth_schemes: dict[ShapeID, AuthScheme[Any, Any, Any, Any]]
    "Auth schemes by auth scheme ID."

    endpoint_resolver: EndpointResolver
    "Resolves the endpoint of each operation."

    endpoint_uri: str | URI | None
    "The static URI requests are sent to."

    interceptors: list[Interceptor[Any, Any, Any, Any]]
    "Hooks called during the execution of a request."

    protocol: ClientProtocol[Any, Any]
    "Serializes requests and deserializes responses."

    retry_strategy: RetryStrategy | RetryStrategyOptions | None
    "The retry strategy, or options to create one."

    transport: ClientTransport[Any, Any]
    "Sends requests, such as an HTTP client."

    def __init__(
        self,
        *,
        auth_scheme_resolver: AuthSchemeResolver | None = None,
        auth_schemes: dict[ShapeID, AuthScheme[Any, Any, Any, Any]] | None = None,
        endpoint_resolver: EndpointResolver | None = None,
        endpoint_uri: str | URI | None = None,
        interceptors: list[Interceptor[Any, Any, Any, Any]] | None = None,
        protocol: ClientProtocol[Any, Any]
        | ProtocolConstructor[ClientProtocol[Any, Any]]
        | None = None,
        retry_strategy: RetryStrategy | RetryStrategyOptions | None = None,
        transport: ClientTransport[Any, Any] | None = None,
    ) -> None:
        self.auth_scheme_resolver = auth_scheme_resolver or DefaultAuthResolver()
        self.auth_schemes = auth_schemes or {}
        self.endpoint_resolver = endpoint_resolver or StaticEndpointResolver()
        self.endpoint_uri = endpoint_uri
        self.interceptors = interceptors or []
        if isinstance(protocol, type):
            protocol = protocol(_PROTOCOL_SETTINGS)
        self.protocol = cast(
            ClientProtocol[Any, Any], protocol
        ) or RpcV2CborClientProtocol(_PROTOCOL_SETTINGS)
        self.retry_strategy = retry_strategy
        self.transport = transport or Urllib3HTTPClient()


type Plugin = Callable[[Config], None]
"A callable that customizes the client configuration."
