from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, ClassVar, Self, Unpack

from smithy_aws_core.config.aws_config import AwsConfig, AwsConfigOverrides
from smithy_aws_core.config.filesystem import FileSystem
from smithy_aws_core.config.resolvers import EndpointUriResolver
from smithy_aws_core.config.types import FieldSpec
from smithy_core.auth import DefaultAuthResolver
from smithy_core.endpoints import BddEndpointResolver
from smithy_core.interceptors import Interceptor
from smithy_core.interfaces import (
    ClientProtocol,
    EndpointResolver,
    ProtocolConstructor,
    ProtocolSettings,
)
from smithy_core.interfaces.auth import AuthScheme, AuthSchemeResolver
from smithy_core.shapes import ShapeID
from smithy_http.protocols import RpcV2CborClientProtocol
from smithy_http.urllib3 import Urllib3HTTPClient

from aws_config_client._private.endpoints import BDD
from aws_config_client._private.schemas import WEATHER_STATION

_PROTOCOL_SETTINGS = ProtocolSettings(
    namespace="example.awsconfig",
    service_target="WeatherStation",
    version="2026-11-19",
    service_schema=WEATHER_STATION,
)


class _WeatherStationConfigOverrides(AwsConfigOverrides, total=False):
    "Explicit field values WeatherStationConfig.resolve accepts."

    endpoint_resolver: EndpointResolver | None
    protocol: (
        ClientProtocol[Any, Any] | ProtocolConstructor[ClientProtocol[Any, Any]] | None
    )
    auth_schemes: dict[ShapeID, AuthScheme[Any, Any, Any, Any]] | None
    auth_scheme_resolver: AuthSchemeResolver | None


@dataclass(kw_only=True, repr=False, init=False)
class WeatherStationConfig(AwsConfig):
    "Configuration for WeatherStationClient."

    interceptors: list[Interceptor[Any, Any, Any, Any]] = field(
        default_factory=list[Interceptor[Any, Any, Any, Any]]
    )
    "Hooks called during the execution of a request."

    endpoint_resolver: EndpointResolver | None = None
    "Resolves the endpoint of each operation."

    protocol: ClientProtocol[Any, Any] | None = None
    "Serializes requests and deserializes responses."

    auth_schemes: dict[ShapeID, AuthScheme[Any, Any, Any, Any]] | None = None
    "Auth schemes by auth scheme ID."

    auth_scheme_resolver: AuthSchemeResolver | None = None
    "Determines the auth scheme for each operation."

    _FIELDS: ClassVar[dict[str, FieldSpec]] = {
        **AwsConfig._FIELDS,
        "endpoint_uri": FieldSpec(
            default=None, resolver=EndpointUriResolver("weather_station").program
        ),
        "endpoint_resolver": FieldSpec(
            default_factory=lambda: BddEndpointResolver(BDD)
        ),
        "protocol": FieldSpec(
            default_factory=lambda: RpcV2CborClientProtocol(_PROTOCOL_SETTINGS),
            converter=lambda p: p(_PROTOCOL_SETTINGS) if isinstance(p, type) else p,
        ),
        "auth_schemes": FieldSpec(default_factory=dict),
        "auth_scheme_resolver": FieldSpec(default_factory=DefaultAuthResolver),
        "transport": FieldSpec(default_factory=lambda: Urllib3HTTPClient()),
    }

    @classmethod
    def resolve(  # pyright: ignore[reportIncompatibleMethodOverride]
        cls,
        *,
        profile: str | None = None,
        fs: FileSystem | None = None,
        config_file_path: str | None = None,
        credentials_file_path: str | None = None,
        **overrides: Unpack[_WeatherStationConfigOverrides],
    ) -> Self:
        "Resolve the config from overrides, the environment, and config files."
        return cls._resolve(
            profile=profile,
            fs=fs,
            config_file_path=config_file_path,
            credentials_file_path=credentials_file_path,
            overrides=overrides,
        )


type Plugin = Callable[[WeatherStationConfig], None]
"A callable that customizes the client configuration."
