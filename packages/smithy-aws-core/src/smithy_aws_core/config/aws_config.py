# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import os
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, ClassVar, Self

from smithy_core.retries import RetryStrategyOptions

if TYPE_CHECKING:
    from smithy_core.aio.interfaces import ClientTransport
    from smithy_core.aio.interfaces.identity import IdentityResolver
    from smithy_core.interfaces import URI
    from smithy_http.interfaces import HTTPRequestConfiguration

    from smithy_aws_core.identity import AWSCredentialsIdentity, AWSIdentityProperties

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


@dataclass(kw_only=True)
class AsyncAwsConfig:
    """Base configuration class for all AWS services.

    Fields are resolved asynchronously from multiple sources (env vars,
    config files, defaults) through the resolve() classmethod.

    Do not instantiate directly — use:
        config = await AsyncAwsConfig.resolve()
    """

    region: str | None = None
    retry_mode: str | None = None
    max_attempts: int | None = None
    endpoint_uri: "str | URI | None" = None
    aws_access_key_id: str | None = field(default=None, repr=False)
    aws_secret_access_key: str | None = field(default=None, repr=False)
    aws_session_token: str | None = field(default=None, repr=False)
    aws_credentials_identity_resolver: "IdentityResolver[AWSCredentialsIdentity, AWSIdentityProperties] | None" = None
    sdk_ua_app_id: str | None = None
    user_agent_extra: str | None = None
    interceptors: list[Any] = field(default_factory=list)  # type: ignore
    http_request_config: "HTTPRequestConfiguration | None" = None
    transport: "ClientTransport[Any, Any] | None" = None
    retry_strategy: Any | None = None

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

    def __post_init__(self) -> None:
        """Block direct construction. Use resolve() instead."""
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
        **overrides: Any,
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
        ctx = SharedConfigContext(
            profile_name=profile,
            fs=fs,
            config_file_path=config_file_path,
            credentials_file_path=credentials_file_path,
        )

        # Fail fast on a bad profile
        profile_origin = ctx.profile_origin
        if profile_origin is not None:
            config_file = await ctx.parsed_profiles()
            validate_profile(ctx.profile_name, config_file.profiles, profile_origin)

        # Create the instance bypassing __post_init__ check
        instance = cls._create_instance()
        instance._ctx = ctx

        # Resolve each field
        await instance._resolve_fields(overrides)

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

        # Resolve credentials atomically before the field loop
        await self._resolve_credentials(overrides)

        for field_name, spec in self._FIELDS.items():
            # Skip credentials — already resolved atomically above
            if field_name in _CREDENTIAL_FIELDS:
                if field_name in self._sources:
                    continue

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

    async def _resolve_credentials(self, overrides: dict[str, Any]) -> None:
        """Resolve credential fields atomically from a single source.

        Rules:
        - If both aws_access_key_id and aws_secret_access_key are overridden,
          resolve normally
        - If only one credential is overridden, raise ConfigValidationError.
        - Otherwise, resolve atomically: if both key and secret are present in
          env, take all three from env. If both are in the profile, take all
          three from profile. Token may be None in either case.

        This prevents mixing credentials from different sources.
        """

        required = {"aws_access_key_id", "aws_secret_access_key"}

        cred_overrides = {f for f in _CREDENTIAL_FIELDS if f in overrides}
        if cred_overrides:
            if required <= cred_overrides:
                return
            else:
                raise ConfigValidationError(
                    f"Partial credential override: {sorted(cred_overrides)}. "
                    "Both 'aws_access_key_id' and 'aws_secret_access_key' must be "
                    "provided together when overriding credentials."
                )

        # Check env vars atomically
        env_creds = (
            (os.environ.get("AWS_ACCESS_KEY_ID") or "").strip() or None,
            (os.environ.get("AWS_SECRET_ACCESS_KEY") or "").strip() or None,
            (os.environ.get("AWS_SESSION_TOKEN") or "").strip() or None,
        )
        if env_creds[0] and env_creds[1]:
            self._set_credentials(_CREDENTIAL_FIELDS, env_creds, ConfigSource.ENV)
            return

        # Check profile atomically
        ctx = self._ctx
        if ctx is None:
            raise ConfigError("Resolution context not initialized")
        config_file = await ctx.parsed_profiles()
        profile_creds = (
            config_file.get(ctx.profile_name, "aws_access_key_id"),
            config_file.get(ctx.profile_name, "aws_secret_access_key"),
            config_file.get(ctx.profile_name, "aws_session_token"),
        )
        if profile_creds[0] and profile_creds[1]:
            self._set_credentials(
                _CREDENTIAL_FIELDS, profile_creds, ConfigSource.PROFILE
            )

    def _set_credentials(
        self,
        fields: tuple[str, ...],
        values: tuple[str | None, ...],
        source: ConfigSource,
    ) -> None:
        """Set credential fields atomically, bypassing __setattr__ tracking."""
        for field_name, value in zip(fields, values, strict=True):
            object.__setattr__(self, field_name, value or None)
            self._sources[field_name] = source

    def __setattr__(self, name: str, value: Any) -> None:
        """Track provenance when fields are set with plugins after construction"""
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
                f"'{name}' cannot be modified after resolution. "
                "Create a new config with the desired credentials instead."
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
