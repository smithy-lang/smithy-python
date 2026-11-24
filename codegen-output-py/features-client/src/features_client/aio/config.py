from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, ClassVar, Self, Unpack

from smithy_aws_core.aio.auth.sigv4 import AsyncSigV4AuthScheme
from smithy_aws_core.aio.config.aws_config import (
    AsyncAwsConfig,
    AsyncAwsConfigOverrides,
)
from smithy_aws_core.aio.config.filesystem import AsyncFileSystem
from smithy_aws_core.config.resolvers import (
    EndpointUriResolver,
    resolve_use_fips_endpoint_program,
)
from smithy_aws_core.config.types import FieldSpec
from smithy_aws_core.endpoints import AWS_RULES_EXTENSION
from smithy_core.aio.interfaces import AsyncEndpointResolver
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
)
from smithy_core.interfaces.auth import AuthSchemeResolver
from smithy_core.shapes import ShapeID
from smithy_core.traits import APIKeyLocation
from smithy_http.aio.aiohttp import AIOHTTPClient
from smithy_http.aio.auth.apikey import AsyncAPIKeyAuthScheme
from smithy_http.aio.auth.bearer import AsyncBearerAuthScheme
from smithy_http.aio.identity.apikey import AsyncAPIKeyIdentityResolver
from smithy_http.aio.protocols import AsyncRpcV2CborClientProtocol
from smithy_http.identity import (
    APIKeyIdentity,
    APIKeyIdentityProperties,
    TokenIdentity,
    TokenIdentityProperties,
)

from features_client._private.endpoints import BDD
from features_client._private.schemas import FIELD_NOTES

_PROTOCOL_SETTINGS = ProtocolSettings(
    namespace="example.features",
    service_target="FieldNotes",
    version="2026-11-20",
    service_schema=FIELD_NOTES,
)


class _AsyncFieldNotesConfigOverrides(AsyncAwsConfigOverrides, total=False):
    "Explicit field values AsyncFieldNotesConfig.resolve accepts."

    endpoint_resolver: EndpointResolver | AsyncEndpointResolver | None
    protocol: (
        ClientProtocol[Any, Any] | ProtocolConstructor[ClientProtocol[Any, Any]] | None
    )
    auth_schemes: dict[ShapeID, AsyncAuthScheme[Any, Any, Any, Any]] | None
    auth_scheme_resolver: AuthSchemeResolver | None
    api_key: str | None
    api_key_identity_resolver: (
        AsyncIdentityResolver[APIKeyIdentity, APIKeyIdentityProperties] | None
    )
    token: str | None
    token_identity_resolver: (
        AsyncIdentityResolver[TokenIdentity, TokenIdentityProperties] | None
    )
    stage: str | None
    force_path_style: bool | None
    use_fips_endpoint: bool | None


@dataclass(kw_only=True, repr=False, init=False)
class AsyncFieldNotesConfig(AsyncAwsConfig):
    "Configuration for AsyncFieldNotesClient."

    interceptors: list[Interceptor[Any, Any, Any, Any]] = field(
        default_factory=list[Interceptor[Any, Any, Any, Any]]
    )
    "Hooks called during the execution of a request."

    endpoint_resolver: EndpointResolver | AsyncEndpointResolver | None = None
    "Resolves the endpoint of each operation."

    protocol: ClientProtocol[Any, Any] | None = None
    "Serializes requests and deserializes responses."

    auth_schemes: dict[ShapeID, AsyncAuthScheme[Any, Any, Any, Any]] | None = None
    "Auth schemes by auth scheme ID."

    auth_scheme_resolver: AuthSchemeResolver | None = None
    "Determines the auth scheme for each operation."

    api_key: str | None = None
    "The API key to send along with requests."

    api_key_identity_resolver: (
        AsyncIdentityResolver[APIKeyIdentity, APIKeyIdentityProperties] | None
    ) = None
    "Resolves the API key."

    token: str | None = None
    "The bearer token to send along with requests."

    token_identity_resolver: (
        AsyncIdentityResolver[TokenIdentity, TokenIdentityProperties] | None
    ) = None
    "Resolves the bearer token."

    stage: str | None = None
    "The deployment stage."

    force_path_style: bool | None = None
    "Forces path-style addressing."

    use_fips_endpoint: bool | None = None
    "Whether to use a FIPS endpoint."

    _FIELDS: ClassVar[dict[str, FieldSpec]] = {
        **AsyncAwsConfig._FIELDS,
        "endpoint_uri": FieldSpec(
            default=None, resolver=EndpointUriResolver("field_notes").program
        ),
        "endpoint_resolver": FieldSpec(
            default_factory=lambda: BddEndpointResolver(
                BDD, extensions=[AWS_RULES_EXTENSION]
            )
        ),
        "protocol": FieldSpec(
            default_factory=lambda: AsyncRpcV2CborClientProtocol(_PROTOCOL_SETTINGS),
            converter=lambda p: p(_PROTOCOL_SETTINGS) if isinstance(p, type) else p,
        ),
        "auth_schemes": FieldSpec(
            default_factory=lambda: {
                ShapeID("aws.auth#sigv4"): AsyncSigV4AuthScheme(service="fieldnotes"),
                ShapeID("smithy.api#httpApiKeyAuth"): AsyncAPIKeyAuthScheme(
                    name="Authorization",
                    location=APIKeyLocation.HEADER,
                    scheme="ApiKey",
                ),
                ShapeID("smithy.api#httpBearerAuth"): AsyncBearerAuthScheme(),
            }
        ),
        "auth_scheme_resolver": FieldSpec(default_factory=DefaultAuthResolver),
        "api_key": FieldSpec(default=None),
        "api_key_identity_resolver": FieldSpec(
            default_factory=lambda: AsyncAPIKeyIdentityResolver()
        ),
        "token": FieldSpec(default=None),
        "token_identity_resolver": FieldSpec(default=None),
        "stage": FieldSpec(default=None),
        "force_path_style": FieldSpec(default=None),
        "use_fips_endpoint": FieldSpec(
            default=None, resolver=resolve_use_fips_endpoint_program
        ),
        "transport": FieldSpec(default_factory=lambda: AIOHTTPClient()),
    }

    _SHARED_FIELDS: ClassVar[tuple[str, ...]] = (
        *AsyncAwsConfig._SHARED_FIELDS,
        "api_key_identity_resolver",
        "token_identity_resolver",
    )

    def set_auth_scheme(self, scheme: AsyncAuthScheme[Any, Any, Any, Any]) -> None:
        "Set an auth scheme under its scheme ID."
        auth_schemes = dict(self.auth_schemes or {})
        auth_schemes[scheme.scheme_id] = scheme
        self.auth_schemes = auth_schemes

    @classmethod
    async def resolve(  # pyright: ignore[reportIncompatibleMethodOverride]
        cls,
        *,
        profile: str | None = None,
        fs: AsyncFileSystem | None = None,
        config_file_path: str | None = None,
        credentials_file_path: str | None = None,
        **overrides: Unpack[_AsyncFieldNotesConfigOverrides],
    ) -> Self:
        "Resolve the config from overrides, the environment, and config files."
        return await cls._resolve(
            profile=profile,
            fs=fs,
            config_file_path=config_file_path,
            credentials_file_path=credentials_file_path,
            overrides=overrides,
        )


type Plugin = Callable[[AsyncFieldNotesConfig], None]
"A callable that customizes the client configuration."
