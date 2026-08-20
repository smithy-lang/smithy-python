# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass, field, fields
from typing import TYPE_CHECKING, Any, ClassVar, Self, TypedDict, Unpack

from smithy_core.retries import RetryStrategyOptions, RetryStrategyType

if TYPE_CHECKING:
    from smithy_core.aio.interfaces import ClientTransport
    from smithy_core.aio.interfaces.identity import IdentityResolver
    from smithy_core.aio.interfaces.retries import RetryStrategy
    from smithy_core.interfaces import URI
    from smithy_http.interfaces import HTTPRequestConfiguration

    from smithy_aws_core.identity.components import (
        AWSCredentialsIdentity,
        AWSIdentityProperties,
    )

from .context import SharedConfigContext
from .exceptions import ConfigError, ConfigValidationError
from .filesystem import FileSystem
from .resolvers import (
    resolve_endpoint_uri,
    resolve_max_attempts,
    resolve_region,
    resolve_retry_mode,
    resolve_sdk_ua_app_id,
)
from .types import UNSET, ConfigSource, FieldSpec, Resolved
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
    retry_strategy: "RetryStrategy | RetryStrategyOptions | None"


@dataclass(kw_only=True, init=False)
class AsyncAwsConfig:
    """Base configuration class for all AWS services.

    Fields are resolved asynchronously from multiple sources (env vars,
    config files, defaults) through the resolve() classmethod.

    Do not instantiate directly — use:
        config = await AsyncAwsConfig.resolve()
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

    _ctx: SharedConfigContext | None = field(default=None, repr=False, compare=False)
    _sources: dict[str, ConfigSource] = field(  # type: ignore[assignment]
        default_factory=dict,
        repr=False,
        compare=False,
    )

    _FIELDS: ClassVar[dict[str, FieldSpec]] = {
        "region": FieldSpec(
            default=None,
            resolver=resolve_region,
            validator=validate_region,
        ),
        "retry_mode": FieldSpec(
            default=RetryStrategyOptions.retry_mode,
            resolver=resolve_retry_mode,
            validator=validate_retry_mode,
        ),
        "max_attempts": FieldSpec(
            default=RetryStrategyOptions.max_attempts,
            resolver=resolve_max_attempts,
            validator=validate_max_attempts,
        ),
        "endpoint_uri": FieldSpec(
            default=None,
            resolver=resolve_endpoint_uri,
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

    def __repr__(self) -> str:
        """Render the config without exposing credential material.

        Defined on the base class so that every subclass inherits the
        filtering, rather than relying on each subclass to mark its own
        credential fields ``repr=False``. Subclasses must be declared with
        ``@dataclass(repr=False)`` so they inherit this instead of generating
        their own ``__repr__``.
        """
        rendered = ", ".join(
            f"{f.name}={getattr(self, f.name)!r}"
            for f in fields(self)
            if f.repr and f.name not in _CREDENTIAL_FIELDS
        )
        return f"{type(self).__name__}({rendered})"

    def __init__(self, *args: object, **kwargs: object) -> None:
        """Block direct construction without advertising config fields as parameters."""
        raise ConfigError(
            f"{type(self).__name__} cannot be constructed directly. "
            f"Use `await {type(self).__name__}.resolve(...)` instead."
        )

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
        """Resolve a config object from environment, config files, and defaults.

        This is the only supported way to create a config instance.

        :param profile: Override the active profile name.
        :param fs: Override the filesystem abstraction.
        :param config_file_path: Override path for config file.
        :param credentials_file_path: Override path for credentials file.
        :param overrides: Explicit field values that skip resolution.
        :returns: A fully-resolved config instance.
        :raises ProfileNotFoundError: If a profile is requested via ``profile`` or
            the ``AWS_PROFILE`` environment variable but is not defined in the
            config files.
        """
        return await cls._resolve(
            profile=profile,
            fs=fs,
            config_file_path=config_file_path,
            credentials_file_path=credentials_file_path,
            overrides=overrides,
        )

    @classmethod
    async def _resolve(
        cls,
        *,
        profile: str | None,
        fs: FileSystem | None,
        config_file_path: str | None,
        credentials_file_path: str | None,
        overrides: Mapping[str, object],
    ) -> Self:
        """Internal resolution entry point for generated typed config factories."""
        ctx = SharedConfigContext(
            profile_name=profile,
            fs=fs,
            config_file_path=config_file_path,
            credentials_file_path=credentials_file_path,
        )

        # Fail fast on a bad profile when one was provided (not the default)
        profile_source = ctx.profile_source
        if profile_source is not ConfigSource.DEFAULT:
            config_file = await ctx.parsed_profiles()
            validate_profile(ctx.profile_name, config_file.profiles, profile_source)

        # Create the instance without calling the blocked constructor
        instance = cls._create_instance()
        instance._ctx = ctx

        # Resolve each field
        await instance._resolve_fields(dict(overrides))

        return instance

    def source_of(self, field_name: str) -> ConfigSource | None:
        """Get the source that provided a field's value.

        :param field_name: The config field name.
        :returns: The ConfigSource, or None if not tracked.
        """
        return self._sources.get(field_name)

    def resolution_context(self) -> SharedConfigContext | None:
        """Get the resolution context used to create this config.

        :returns: The SharedConfigContext, or None if not available.
        """
        return self._ctx

    @classmethod
    def _create_instance(cls) -> Self:
        """Create an instance that bypasses construction blocking."""
        instance = object.__new__(cls)
        object.__setattr__(instance, "_sources", {})
        object.__setattr__(instance, "_ctx", None)
        for field_name in cls._FIELDS:
            object.__setattr__(instance, field_name, UNSET)
        return instance

    async def _resolve_fields(self, overrides: dict[str, Any]) -> None:
        """Run the resolution pipeline for all fields."""
        unknown = set(overrides) - set(self._FIELDS)
        if unknown:
            raise ConfigValidationError(
                f"Unknown config field(s): {sorted(unknown)}. "
                f"Valid fields are: {sorted(self._FIELDS)}"
            )

        # Validate credential overrides and auto-wire the identity resolver
        # before the field loop, so the loop sees the resolver as an override.
        self._resolve_credentials(overrides)

        for field_name, spec in self._FIELDS.items():
            # check for overrides first
            if field_name in overrides:
                value = overrides[field_name]
                setattr(self, field_name, value)
                self._sources[field_name] = ConfigSource.OVERRIDE
            # check in resolver
            elif spec.resolver is not None:
                result: Resolved[Any] = await spec.resolver(self._ctx)
                if result.value is not UNSET:
                    setattr(self, field_name, result.value)
                    self._sources[field_name] = result.source
                else:
                    # If resolver returned UNSET, fall back to default
                    self._apply_default(field_name, spec)

            else:
                # No resolver, use default directly
                self._apply_default(field_name, spec)

            # Run validator for all sources
            if spec.validator is not None:
                spec.validator(getattr(self, field_name))

    def _apply_default(self, field_name: str, spec: FieldSpec) -> None:
        """Apply the default value for a field."""
        if spec.default_factory is not None:
            value = spec.default_factory()
        else:
            value = spec.default
        setattr(self, field_name, value)
        self._sources[field_name] = ConfigSource.DEFAULT

    def _resolve_credentials(self, overrides: dict[str, Any]) -> None:
        """Validate in-code credentials and auto-wire StaticCredentialsResolver.

        Rules:
        - If both aws_access_key_id and aws_secret_access_key are overridden,
          auto-set aws_credentials_identity_resolver to a
          StaticCredentialsResolver (unless the caller already provided one).
          Only the overridden values are used, so a session token present in a
          profile is not picked up here.
        - If credentials are overridden but the key/secret pair is incomplete,
          raise ConfigValidationError.
        - If no credential is overridden,  credentials are resolved from the
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

        # Auto-wire StaticCredentialsResolver if user didn't provide one
        if overrides.get("aws_credentials_identity_resolver") is None:
            # Lazy import to avoid circular dependency
            from smithy_aws_core.identity.components import AWSCredentialsIdentity
            from smithy_aws_core.identity.static import StaticCredentialsResolver

            identity = AWSCredentialsIdentity(
                access_key_id=overrides["aws_access_key_id"],
                secret_access_key=overrides["aws_secret_access_key"],
                session_token=overrides.get("aws_session_token"),
            )
            overrides["aws_credentials_identity_resolver"] = StaticCredentialsResolver(
                identity=identity
            )

    def __setattr__(self, name: str, value: Any) -> None:
        """Guard and track config fields set after resolution.

        Rejects unknown field names, blocks credential mutation, validates the
        new value, and records the field as an override so ``source_of()``
        stays accurate when plugins customize a config per request.
        """
        # Reject unknown fields
        if not name.startswith("_") and name not in self.__class__._FIELDS:
            raise AttributeError(
                f"'{type(self).__name__}' has no config field '{name}'"
            )

        # Block override for credentials after resolution
        if (
            name in _CREDENTIAL_FIELDS
            and hasattr(self, "_sources")
            and name in self._sources
        ):
            raise AttributeError(
                f"'{name}' cannot be modified after resolution. Pass credentials "
                f"to `await {type(self).__name__}.resolve(...)`, or set "
                "'aws_credentials_identity_resolver' to supply credentials "
                "dynamically."
            )

        # Mark as override only if the field is in _FIELDS and was already resolved
        if (
            name in self.__class__._FIELDS
            and hasattr(self, "_sources")
            and name in self._sources
        ):
            spec = self.__class__._FIELDS[name]
            if spec.validator is not None:
                spec.validator(value)
            self._sources[name] = ConfigSource.OVERRIDE
        super().__setattr__(name, value)

    def __deepcopy__(self, memo: dict[int, Any]) -> Self:
        """Deep-copy the config while sharing resources that must not be duplicated."""
        for shared in (
            self.aws_credentials_identity_resolver,
            self.transport,
            self.retry_strategy,
        ):
            if shared is not None:
                memo[id(shared)] = shared
        new = self._create_instance()
        memo[id(self)] = new
        for f in fields(self):
            object.__setattr__(new, f.name, deepcopy(getattr(self, f.name), memo))
        return new
