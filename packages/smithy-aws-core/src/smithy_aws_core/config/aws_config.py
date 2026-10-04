# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, ClassVar, Self, TypedDict, Unpack

from smithy_core.config import ConfigBase, ConfigValidationError, FieldSpec
from smithy_core.retries import RetryStrategyOptions, RetryStrategyType

if TYPE_CHECKING:
    from smithy_core.aio.interfaces import ClientTransport
    from smithy_core.aio.interfaces.identity import IdentityResolver
    from smithy_core.aio.interfaces.retries import AsyncRetryStrategy
    from smithy_core.interfaces import URI
    from smithy_core.interfaces.retries import RetryStrategy
    from smithy_http.interfaces import HTTPRequestConfiguration

    from smithy_aws_core.identity.components import (
        AWSCredentialsIdentity,
        AWSIdentityProperties,
    )

from .context import SharedConfigContext
from .filesystem import FileSystem
from .resolvers import (
    resolve_endpoint_uri,
    resolve_endpoint_uri_async,
    resolve_max_attempts,
    resolve_max_attempts_async,
    resolve_region,
    resolve_region_async,
    resolve_retry_mode,
    resolve_retry_mode_async,
    resolve_sdk_ua_app_id,
    resolve_sdk_ua_app_id_async,
)
from .types import ConfigSource
from .validators import (
    validate_max_attempts,
    validate_profile,
    validate_region,
    validate_retry_mode,
)

_CREDENTIAL_FIELDS = ("aws_access_key_id", "aws_secret_access_key", "aws_session_token")


class AwsConfigOverrides(TypedDict, total=False):
    """Common keyword overrides accepted by AWS config resolution."""

    region: str | None
    retry_mode: RetryStrategyType | None
    max_attempts: int | None
    endpoint_uri: "str | URI | None"
    aws_access_key_id: str | None
    aws_secret_access_key: str | None
    aws_session_token: str | None
    aws_credentials_identity_resolver: (
        "IdentityResolver[AWSCredentialsIdentity, AWSIdentityProperties] | None"
    )
    sdk_ua_app_id: str | None
    user_agent_extra: str | None
    interceptors: list[Any]
    http_request_config: "HTTPRequestConfiguration | None"
    transport: "ClientTransport[Any, Any] | None"
    retry_strategy: "RetryStrategy | AsyncRetryStrategy | RetryStrategyOptions | None"


@dataclass(kw_only=True, init=False, repr=False)
class AwsConfigBase(ConfigBase):
    """Shared base for the sync and async AWS config classes.

    Adds the AWS resolvable fields and resolution content (shared config files,
    region, credentials) onto the generic :py:class:`~smithy_core.config.ConfigBase`
    engine. The public ``resolve()`` factory lives on the concrete subclasses
    :py:class:`AwsConfig` (synchronous) and :py:class:`AsyncAwsConfig`
    (asynchronous). Not meant to be used directly.
    """

    region: str | None = None
    """The AWS region to connect to.
    """

    retry_mode: RetryStrategyType | None = None
    """The retry mode to use. ``standard`` is the only accepted override.

    ``legacy`` and ``adaptive`` are rejected when set here; when they come from
    the environment or a config file they warn and fall back to ``standard``.
    """

    max_attempts: int | None = None
    """The maximum number of attempts to make per request, including the initial
    attempt. Must be an integer of at least 1."""

    endpoint_uri: "str | URI | None" = None
    """A static URI to route requests to."""

    aws_access_key_id: str | None = field(default=None, repr=False)
    """The identifier for a secret access key.

    Set this together with ``aws_secret_access_key`` to supply credentials in
    code. Cannot be modified after resolution; see
    ``aws_credentials_identity_resolver`` to supply credentials dynamically.
    """

    aws_secret_access_key: str | None = field(default=None, repr=False)
    """A secret access key that can be used to sign requests.

    Must be set together with ``aws_access_key_id``.
    """

    aws_session_token: str | None = field(default=None, repr=False)
    """The session token used with temporary AWS credentials.

    Set this together with ``aws_access_key_id`` and ``aws_secret_access_key``
    when supplying temporary credentials in code.
    """

    aws_credentials_identity_resolver: "IdentityResolver[AWSCredentialsIdentity, AWSIdentityProperties] | None" = None
    """Resolves AWS Credentials.

    Set automatically to a ``StaticCredentialsResolver`` when
    ``aws_access_key_id`` and ``aws_secret_access_key`` are supplied in code.
    """

    sdk_ua_app_id: str | None = None
    """A unique and opaque application ID that is appended to the User-Agent
    header."""

    user_agent_extra: str | None = None
    """Additional suffix to be added to the User-Agent header."""

    interceptors: list[Any] = field(default_factory=list)  # type: ignore
    """The list of interceptors, which are hooks that are called during the
    execution of a request."""

    http_request_config: "HTTPRequestConfiguration | None" = None
    """Configuration for individual HTTP requests."""

    transport: "ClientTransport[Any, Any] | None" = None
    """The transport to use to send requests"""

    retry_strategy: Any | None = None
    """The retry strategy or options for configuring retry behavior.
    """

    _REPR_EXCLUDE_FIELDS: ClassVar[frozenset[str]] = frozenset(_CREDENTIAL_FIELDS)
    _DEEPCOPY_SHARED_FIELDS: ClassVar[tuple[str, ...]] = (
        "aws_credentials_identity_resolver",
        "transport",
        "retry_strategy",
    )

    _FIELDS: ClassVar[dict[str, FieldSpec]] = {
        "region": FieldSpec(
            default=None,
            resolver=resolve_region,
            async_resolver=resolve_region_async,
            validator=validate_region,
        ),
        "retry_mode": FieldSpec(
            default=RetryStrategyOptions.retry_mode,
            resolver=resolve_retry_mode,
            async_resolver=resolve_retry_mode_async,
            validator=validate_retry_mode,
        ),
        "max_attempts": FieldSpec(
            default=RetryStrategyOptions.max_attempts,
            resolver=resolve_max_attempts,
            async_resolver=resolve_max_attempts_async,
            validator=validate_max_attempts,
        ),
        "endpoint_uri": FieldSpec(
            default=None,
            resolver=resolve_endpoint_uri,
            async_resolver=resolve_endpoint_uri_async,
        ),
        "aws_access_key_id": FieldSpec(
            default=None,
        ),
        "aws_secret_access_key": FieldSpec(
            default=None,
        ),
        "aws_session_token": FieldSpec(
            default=None,
        ),
        "aws_credentials_identity_resolver": FieldSpec(
            default=None,
        ),
        "sdk_ua_app_id": FieldSpec(
            default=None,
            resolver=resolve_sdk_ua_app_id,
            async_resolver=resolve_sdk_ua_app_id_async,
        ),
        "user_agent_extra": FieldSpec(
            default=None,
        ),
        "interceptors": FieldSpec(
            default_factory=list,
        ),
        "http_request_config": FieldSpec(
            default=None,
        ),
        "transport": FieldSpec(
            default=None,
        ),
        "retry_strategy": FieldSpec(
            default=None,
        ),
    }

    def _build_context(
        self,
        *,
        profile: str | None = None,
        fs: FileSystem | None = None,
        config_file_path: str | None = None,
        credentials_file_path: str | None = None,
        **context_kwargs: Any,
    ) -> SharedConfigContext:
        """Build the AWS shared-config resolution context."""
        return SharedConfigContext(
            profile_name=profile,
            fs=fs,
            config_file_path=config_file_path,
            credentials_file_path=credentials_file_path,
        )

    async def _validate_context_async(self, ctx: SharedConfigContext) -> None:
        """Fail fast on a bad profile when one was explicitly provided."""
        if ctx.profile_source is not ConfigSource.DEFAULT:
            config_file = await ctx.parsed_profiles()
            validate_profile(ctx.profile_name, config_file.profiles, ctx.profile_source)

    def _validate_context(self, ctx: SharedConfigContext) -> None:
        """Fail fast on a bad profile when one was explicitly provided."""
        if ctx.profile_source is not ConfigSource.DEFAULT:
            config_file = ctx.parsed_profiles_sync()
            validate_profile(ctx.profile_name, config_file.profiles, ctx.profile_source)

    def _resolve_credentials(self, overrides: dict[str, Any], *, async_: bool) -> None:
        """Validate in-code credentials and auto-wire a StaticCredentialsResolver.

        Rules:
        - If both aws_access_key_id and aws_secret_access_key are overridden,
          auto-set aws_credentials_identity_resolver to a
          StaticCredentialsResolver (unless the caller already provided one).
          Only the overridden values are used, so a session token present in a
          profile is not picked up here.
        - If credentials are overridden but the key/secret pair is incomplete,
          raise ConfigValidationError.
        - If no credential is overridden, credentials are resolved from the
          remaining sources.
        """
        required = {"aws_access_key_id", "aws_secret_access_key"}
        cred_overrides = {f for f in _CREDENTIAL_FIELDS if f in overrides}

        if not cred_overrides:
            return

        if not required <= cred_overrides:
            raise ConfigValidationError(
                f"Partial credential override: {sorted(cred_overrides)}. "
                "Both 'aws_access_key_id' and 'aws_secret_access_key' must be "
                "provided together when overriding credentials."
            )

        if overrides.get("aws_credentials_identity_resolver") is None:
            # Lazy import to avoid circular dependency
            from smithy_aws_core.identity.components import AWSCredentialsIdentity

            if async_:
                from smithy_aws_core.identity.static import (
                    AsyncStaticCredentialsResolver as static_resolver_cls,
                )
            else:
                from smithy_aws_core.identity.static import (
                    StaticCredentialsResolver as static_resolver_cls,
                )

            identity = AWSCredentialsIdentity(
                access_key_id=overrides["aws_access_key_id"],
                secret_access_key=overrides["aws_secret_access_key"],
                session_token=overrides.get("aws_session_token"),
            )
            overrides["aws_credentials_identity_resolver"] = static_resolver_cls(
                identity=identity
            )

    def _guard_setattr(self, name: str, value: Any, spec: FieldSpec | None) -> None:
        """Block credential mutation after resolution."""
        if (
            name in _CREDENTIAL_FIELDS
            and hasattr(self, "_sources")
            and name in self._sources
        ):
            raise AttributeError(
                f"'{name}' cannot be modified after resolution. Pass credentials "
                f"to `{type(self).__name__}.resolve(...)`, or set "
                "'aws_credentials_identity_resolver' to supply credentials "
                "dynamically."
            )


@dataclass(kw_only=True, init=False, repr=False)
class AwsConfig(AwsConfigBase):
    """Synchronous AWS config. Resolve with :py:meth:`resolve`."""

    @classmethod
    def resolve(
        cls,
        *,
        profile: str | None = None,
        fs: FileSystem | None = None,
        config_file_path: str | None = None,
        credentials_file_path: str | None = None,
        **overrides: Unpack[AwsConfigOverrides],
    ) -> Self:
        """Resolve a config from environment, config files, and defaults.

        Reads config/credentials files with blocking disk I/O.

        :param profile: Override the active profile name.
        :param fs: Override the filesystem abstraction.
        :param config_file_path: Override path for config file.
        :param credentials_file_path: Override path for credentials file.
        :param overrides: Explicit field values that skip resolution.
        :returns: A fully-resolved config instance.
        :raises ProfileNotFoundError: If a requested profile is not defined.
        """
        return cls._resolve(
            overrides=overrides,
            profile=profile,
            fs=fs,
            config_file_path=config_file_path,
            credentials_file_path=credentials_file_path,
        )


@dataclass(kw_only=True, init=False, repr=False)
class AsyncAwsConfig(AwsConfigBase):
    """Asynchronous AWS config. Resolve with :py:meth:`resolve`."""

    @classmethod
    async def resolve(
        cls,
        *,
        profile: str | None = None,
        fs: FileSystem | None = None,
        config_file_path: str | None = None,
        credentials_file_path: str | None = None,
        **overrides: Unpack[AwsConfigOverrides],
    ) -> Self:
        """Resolve a config from environment, config files, and defaults.

        :param profile: Override the active profile name.
        :param fs: Override the filesystem abstraction.
        :param config_file_path: Override path for config file.
        :param credentials_file_path: Override path for credentials file.
        :param overrides: Explicit field values that skip resolution.
        :returns: A fully-resolved config instance.
        :raises ProfileNotFoundError: If a requested profile is not defined.
        """
        return await cls._resolve_async(
            overrides=overrides,
            profile=profile,
            fs=fs,
            config_file_path=config_file_path,
            credentials_file_path=credentials_file_path,
        )
