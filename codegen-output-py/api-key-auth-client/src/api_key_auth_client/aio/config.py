from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeAlias, cast

from smithy_core.aio.interfaces import AsyncClientTransport, AsyncEndpointResolver
from smithy_core.aio.interfaces.auth import AsyncAuthScheme
from smithy_core.aio.interfaces.identity import AsyncIdentityResolver
from smithy_core.auth import DefaultAuthResolver
from smithy_core.endpoints import BddEndpointResolver
from smithy_core.interceptors import Interceptor
from smithy_core.interfaces import (
    ClientProtocol,
    EndpointResolver,
    ProtocolConstructor,
    ProtocolSettings,
    URI,
)
from smithy_core.interfaces.auth import AuthSchemeResolver
from smithy_core.interfaces.retries import RetryStrategy
from smithy_core.retries import RetryStrategyOptions
from smithy_core.shapes import ShapeID
from smithy_core.traits import APIKeyLocation
from smithy_http.aio.aiohttp import AIOHTTPClient
from smithy_http.aio.auth.apikey import AsyncAPIKeyAuthScheme
from smithy_http.aio.identity.apikey import AsyncAPIKeyIdentityResolver
from smithy_http.aio.protocols import AsyncRpcV2CborClientProtocol
from smithy_http.identity import APIKeyIdentity, APIKeyIdentityProperties

from api_key_auth_client._private.endpoints import BDD
from api_key_auth_client._private.schemas import API_KEY_SERVICE

_PROTOCOL_SETTINGS = ProtocolSettings(
    namespace="example.apikey",
    service_target="ApiKeyService",
    version="2026-11-17",
    service_schema=API_KEY_SERVICE,
)


@dataclass(init=False)
class AsyncConfig:
    "Configuration for AsyncApiKeyService."

    api_key: str | None
    "The API key to send along with requests."

    api_key_identity_resolver: (
        AsyncIdentityResolver[APIKeyIdentity, APIKeyIdentityProperties] | None
    )
    "Resolves the API key."

    auth_scheme_resolver: AuthSchemeResolver
    "Determines the auth scheme for each operation."

    auth_schemes: dict[ShapeID, AsyncAuthScheme[Any, Any, Any, Any]]
    "Auth schemes by auth scheme ID."

    endpoint_resolver: EndpointResolver | AsyncEndpointResolver
    "Resolves the endpoint of each operation."

    endpoint_uri: str | URI | None
    "The endpoint URI, read by the endpoint rules as ``SDK::Endpoint``."

    interceptors: list[Interceptor[Any, Any, Any, Any]]
    "Hooks called during the execution of a request."

    protocol: ClientProtocol[Any, Any]
    "Serializes requests and deserializes responses."

    retry_strategy: RetryStrategy | RetryStrategyOptions | None
    "The retry strategy, or options to create one."

    transport: AsyncClientTransport[Any, Any]
    "Sends requests, such as an HTTP client."

    def __init__(
        self,
        *,
        api_key: str | None = None,
        api_key_identity_resolver: AsyncIdentityResolver[
            APIKeyIdentity, APIKeyIdentityProperties
        ]
        | None = None,
        auth_scheme_resolver: AuthSchemeResolver | None = None,
        auth_schemes: dict[ShapeID, AsyncAuthScheme[Any, Any, Any, Any]] | None = None,
        endpoint_resolver: EndpointResolver | AsyncEndpointResolver | None = None,
        endpoint_uri: str | URI | None = None,
        interceptors: list[Interceptor[Any, Any, Any, Any]] | None = None,
        protocol: ClientProtocol[Any, Any]
        | ProtocolConstructor[ClientProtocol[Any, Any]]
        | None = None,
        retry_strategy: RetryStrategy | RetryStrategyOptions | None = None,
        transport: AsyncClientTransport[Any, Any] | None = None,
    ) -> None:
        self.api_key = api_key
        self.api_key_identity_resolver = (
            api_key_identity_resolver or AsyncAPIKeyIdentityResolver()
        )
        self.auth_scheme_resolver = auth_scheme_resolver or DefaultAuthResolver()
        self.auth_schemes = auth_schemes or {
            ShapeID("smithy.api#httpApiKeyAuth"): AsyncAPIKeyAuthScheme(
                name="Authorization", location=APIKeyLocation.HEADER, scheme="ApiKey"
            ),
        }
        self.endpoint_resolver = endpoint_resolver or BddEndpointResolver(BDD)
        self.endpoint_uri = endpoint_uri
        self.interceptors = interceptors or []
        if isinstance(protocol, type):
            protocol = protocol(_PROTOCOL_SETTINGS)
        self.protocol = cast(
            ClientProtocol[Any, Any], protocol
        ) or AsyncRpcV2CborClientProtocol(_PROTOCOL_SETTINGS)
        self.retry_strategy = retry_strategy
        self.transport = transport or AIOHTTPClient()

    def set_auth_scheme(self, scheme: AsyncAuthScheme[Any, Any, Any, Any]) -> None:
        "Set an auth scheme under its scheme ID."
        self.auth_schemes[scheme.scheme_id] = scheme


Plugin: TypeAlias = Callable[[AsyncConfig], None]
"A callable that customizes the client configuration."
