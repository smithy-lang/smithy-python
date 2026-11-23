from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, ClassVar, Self, Unpack

from smithy_aws_core.aio.auth.sigv4 import AsyncSigV4AuthScheme
from smithy_aws_core.aio.config.aws_config import (
    AsyncAwsConfig,
    AsyncAwsConfigOverrides,
)
from smithy_aws_core.aio.config.filesystem import AsyncFileSystem
from smithy_aws_core.aio.protocols import AsyncAwsJson10ClientProtocol
from smithy_aws_core.config.resolvers import EndpointUriResolver
from smithy_aws_core.config.types import FieldSpec
from smithy_aws_core.endpoints import AWS_RULES_EXTENSION
from smithy_core.aio.interfaces import AsyncEndpointResolver
from smithy_core.aio.interfaces.auth import AsyncAuthScheme
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
from smithy_http.aio.aiohttp import AIOHTTPClient

from querycompatible_awsjson10_client._private.endpoints import BDD
from querycompatible_awsjson10_client._private.schemas import (
    QUERY_COMPATIBLE_JSON_RPC10,
)

_PROTOCOL_SETTINGS = ProtocolSettings(
    namespace="aws.protocoltests.json10",
    service_target="QueryCompatibleJsonRpc10",
    version="2020-07-14",
    service_schema=QUERY_COMPATIBLE_JSON_RPC10,
)


class _AsyncQueryCompatibleJSONRPC10ConfigOverrides(
    AsyncAwsConfigOverrides, total=False
):
    "Explicit field values AsyncQueryCompatibleJSONRPC10Config.resolve accepts."

    endpoint_resolver: EndpointResolver | AsyncEndpointResolver | None
    protocol: (
        ClientProtocol[Any, Any] | ProtocolConstructor[ClientProtocol[Any, Any]] | None
    )
    auth_schemes: dict[ShapeID, AsyncAuthScheme[Any, Any, Any, Any]] | None
    auth_scheme_resolver: AuthSchemeResolver | None


@dataclass(kw_only=True, repr=False, init=False)
class AsyncQueryCompatibleJSONRPC10Config(AsyncAwsConfig):
    "Configuration for AsyncQueryCompatibleJSONRPC10Client."

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

    _FIELDS: ClassVar[dict[str, FieldSpec]] = {
        **AsyncAwsConfig._FIELDS,
        "endpoint_uri": FieldSpec(
            default=None,
            resolver=EndpointUriResolver("query_compatible_json_rpc_10").program,
        ),
        "endpoint_resolver": FieldSpec(
            default_factory=lambda: BddEndpointResolver(
                BDD, extensions=[AWS_RULES_EXTENSION]
            )
        ),
        "protocol": FieldSpec(
            default_factory=lambda: AsyncAwsJson10ClientProtocol(_PROTOCOL_SETTINGS),
            converter=lambda p: p(_PROTOCOL_SETTINGS) if isinstance(p, type) else p,
        ),
        "auth_schemes": FieldSpec(
            default_factory=lambda: {
                ShapeID("aws.auth#sigv4"): AsyncSigV4AuthScheme(
                    service="querycompatiblejsonrpc10"
                )
            }
        ),
        "auth_scheme_resolver": FieldSpec(default_factory=DefaultAuthResolver),
        "transport": FieldSpec(default_factory=lambda: AIOHTTPClient()),
    }

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
        **overrides: Unpack[_AsyncQueryCompatibleJSONRPC10ConfigOverrides],
    ) -> Self:
        "Resolve the config from overrides, the environment, and config files."
        return await cls._resolve(
            profile=profile,
            fs=fs,
            config_file_path=config_file_path,
            credentials_file_path=credentials_file_path,
            overrides=overrides,
        )


type Plugin = Callable[[AsyncQueryCompatibleJSONRPC10Config], None]
"A callable that customizes the client configuration."
