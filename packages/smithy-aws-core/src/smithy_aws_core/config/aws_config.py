# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass, field
from typing import Any, ClassVar, Self

from smithy_core.retries import RetryStrategyOptions

from .context import SharedConfigContext
from .exceptions import ConfigError, ConfigValidationError
from .filesystem import FileSystem
from .resolvers import (
    resolve_max_attempts,
    resolve_region,
    resolve_retry_mode,
)
from .types import UNSET, ConfigSource, FieldSpec, Resolved
from .validators import (
    validate_max_attempts,
    validate_profile,
    validate_region,
    validate_retry_mode,
)


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

    def __setattr__(self, name: str, value: Any) -> None:
        """Track provenance when fields are set with plugins after construction"""
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
