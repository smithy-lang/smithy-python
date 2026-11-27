from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, ClassVar, Self, Unpack

from smithy_aws_core.auth.sigv4 import SigV4AuthScheme
from smithy_aws_core.config.aws_config import AwsConfig, AwsConfigOverrides
from smithy_aws_core.config.filesystem import FileSystem
from smithy_aws_core.config.resolvers import (
    EndpointUriResolver,
    resolve_request_checksum_calculation_program,
    resolve_response_checksum_validation_program,
    resolve_use_fips_endpoint_program,
)
from smithy_aws_core.config.types import (
    FieldSpec,
    RequestChecksumCalculation,
    ResponseChecksumValidation,
)
from smithy_aws_core.config.validators import (
    validate_request_checksum_calculation,
    validate_response_checksum_validation,
)
from smithy_aws_core.endpoints import AWS_RULES_EXTENSION
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
from smithy_core.interfaces.identity import IdentityResolver
from smithy_core.shapes import ShapeID
from smithy_core.traits import APIKeyLocation
from smithy_http.auth.apikey import APIKeyAuthScheme
from smithy_http.auth.bearer import BearerAuthScheme
from smithy_http.identity import (
    APIKeyIdentity,
    APIKeyIdentityProperties,
    TokenIdentity,
    TokenIdentityProperties,
)
from smithy_http.identity.apikey import APIKeyIdentityResolver
from smithy_http.protocols import RpcV2CborClientProtocol
from smithy_http.urllib3 import Urllib3HTTPClient

from features_client._private.endpoints import BDD
from features_client._private.schemas import FIELD_NOTES

_PROTOCOL_SETTINGS = ProtocolSettings(
    namespace="example.features",
    service_target="FieldNotes",
    version="2026-11-20",
    service_schema=FIELD_NOTES,
)


class _FieldNotesConfigOverrides(AwsConfigOverrides, total=False):
    "Explicit field values FieldNotesConfig.resolve accepts."

    endpoint_resolver: EndpointResolver | None
    protocol: (
        ClientProtocol[Any, Any] | ProtocolConstructor[ClientProtocol[Any, Any]] | None
    )
    auth_schemes: dict[ShapeID, AuthScheme[Any, Any, Any, Any]] | None
    auth_scheme_resolver: AuthSchemeResolver | None
    api_key: str | None
    api_key_identity_resolver: (
        IdentityResolver[APIKeyIdentity, APIKeyIdentityProperties] | None
    )
    token: str | None
    token_identity_resolver: (
        IdentityResolver[TokenIdentity, TokenIdentityProperties] | None
    )
    stage: str | None
    force_path_style: bool | None
    use_fips_endpoint: bool | None
    request_checksum_calculation: RequestChecksumCalculation | None
    response_checksum_validation: ResponseChecksumValidation | None


@dataclass(kw_only=True, repr=False, init=False)
class FieldNotesConfig(AwsConfig):
    "Configuration for FieldNotesClient."

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

    api_key: str | None = None
    "The API key to send along with requests."

    api_key_identity_resolver: (
        IdentityResolver[APIKeyIdentity, APIKeyIdentityProperties] | None
    ) = None
    "Resolves the API key."

    token: str | None = None
    "The bearer token to send along with requests."

    token_identity_resolver: (
        IdentityResolver[TokenIdentity, TokenIdentityProperties] | None
    ) = None
    "Resolves the bearer token."

    stage: str | None = None
    "The deployment stage."

    force_path_style: bool | None = None
    "Forces path-style addressing."

    use_fips_endpoint: bool | None = None
    "Whether to use a FIPS endpoint."

    request_checksum_calculation: RequestChecksumCalculation | None = None
    "When to calculate request checksums: `when_supported` (the default) or `when_required`, only when the operation requires one or the request sets an algorithm."

    response_checksum_validation: ResponseChecksumValidation | None = None
    "When to validate response checksums: `when_supported` (the default) or `when_required`, only when the request enables validation."

    _FIELDS: ClassVar[dict[str, FieldSpec]] = {
        **AwsConfig._FIELDS,
        "endpoint_uri": FieldSpec(
            default=None, resolver=EndpointUriResolver("field_notes").program
        ),
        "endpoint_resolver": FieldSpec(
            default_factory=lambda: BddEndpointResolver(
                BDD, extensions=[AWS_RULES_EXTENSION]
            )
        ),
        "protocol": FieldSpec(
            default_factory=lambda: RpcV2CborClientProtocol(_PROTOCOL_SETTINGS),
            converter=lambda p: p(_PROTOCOL_SETTINGS) if isinstance(p, type) else p,
        ),
        "auth_schemes": FieldSpec(
            default_factory=lambda: {
                ShapeID("aws.auth#sigv4"): SigV4AuthScheme(service="fieldnotes"),
                ShapeID("smithy.api#httpApiKeyAuth"): APIKeyAuthScheme(
                    name="Authorization",
                    location=APIKeyLocation.HEADER,
                    scheme="ApiKey",
                ),
                ShapeID("smithy.api#httpBearerAuth"): BearerAuthScheme(),
            }
        ),
        "auth_scheme_resolver": FieldSpec(default_factory=DefaultAuthResolver),
        "api_key": FieldSpec(default=None),
        "api_key_identity_resolver": FieldSpec(
            default_factory=lambda: APIKeyIdentityResolver()
        ),
        "token": FieldSpec(default=None),
        "token_identity_resolver": FieldSpec(default=None),
        "stage": FieldSpec(default=None),
        "force_path_style": FieldSpec(default=None),
        "use_fips_endpoint": FieldSpec(
            default=None, resolver=resolve_use_fips_endpoint_program
        ),
        "request_checksum_calculation": FieldSpec(
            default="when_supported",
            resolver=resolve_request_checksum_calculation_program,
            validator=validate_request_checksum_calculation,
        ),
        "response_checksum_validation": FieldSpec(
            default="when_supported",
            resolver=resolve_response_checksum_validation_program,
            validator=validate_response_checksum_validation,
        ),
        "transport": FieldSpec(default_factory=lambda: Urllib3HTTPClient()),
    }

    _SHARED_FIELDS: ClassVar[tuple[str, ...]] = (
        *AwsConfig._SHARED_FIELDS,
        "api_key_identity_resolver",
        "token_identity_resolver",
    )

    def set_auth_scheme(self, scheme: AuthScheme[Any, Any, Any, Any]) -> None:
        "Set an auth scheme under its scheme ID."
        auth_schemes = dict(self.auth_schemes or {})
        auth_schemes[scheme.scheme_id] = scheme
        self.auth_schemes = auth_schemes

    @classmethod
    def resolve(  # pyright: ignore[reportIncompatibleMethodOverride]
        cls,
        *,
        profile: str | None = None,
        fs: FileSystem | None = None,
        config_file_path: str | None = None,
        credentials_file_path: str | None = None,
        **overrides: Unpack[_FieldNotesConfigOverrides],
    ) -> Self:
        "Resolve the config from overrides, the environment, and config files."
        return cls._resolve(
            profile=profile,
            fs=fs,
            config_file_path=config_file_path,
            credentials_file_path=credentials_file_path,
            overrides=overrides,
        )


type Plugin = Callable[[FieldNotesConfig], None]
"A callable that customizes the client configuration."
