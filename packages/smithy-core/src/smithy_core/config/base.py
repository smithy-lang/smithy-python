# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass, field, fields
from typing import Any, ClassVar, Self

from .exceptions import ConfigError, ConfigValidationError
from .types import UNSET, ConfigSource, FieldSpec, Resolved


@dataclass(kw_only=True, init=False)
class ConfigBase:
    """Shared base for the sync and async client config classes.

    Holds the resolvable fields and the resolution machinery; the public
    ``resolve()`` factory lives on the concrete subclasses :py:class:`Config`
    (synchronous) and :py:class:`AsyncConfig` (asynchronous). Not meant to be
    used directly.

    The engine is resolution-source agnostic: it threads an opaque context
    object (built by :py:meth:`_build_context`, ``None`` here) to the field
    resolvers, and defers credential wiring to :py:meth:`_resolve_credentials`
    (a no-op here). Layers that read a config source, such as the AWS shared
    config files, subclass this and supply those two hooks.
    """

    _ctx: Any = field(default=None, repr=False, compare=False)
    _sources: dict[str, ConfigSource] = field(  # type: ignore[assignment]
        default_factory=dict,
        repr=False,
        compare=False,
    )

    _FIELDS: ClassVar[dict[str, FieldSpec]] = {}

    # CAUTION: subclasses carrying secrets override this to exclude them from __repr__.
    _REPR_EXCLUDE_FIELDS: ClassVar[frozenset[str]] = frozenset()

    def __repr__(self) -> str:
        """Render the config, excluding fields subclasses mark sensitive.

        Defined on the base so every subclass inherits the filtering rather
        than generating its own ``__repr__``. Subclasses must be declared with
        ``@dataclass(repr=False)`` to inherit this.
        """
        rendered = ", ".join(
            f"{f.name}={getattr(self, f.name)!r}"
            for f in fields(self)
            if f.repr and f.name not in self._REPR_EXCLUDE_FIELDS
        )
        return f"{type(self).__name__}({rendered})"

    def __init__(self, *args: object, **kwargs: object) -> None:
        """Block direct construction without advertising config fields as parameters."""
        raise ConfigError(
            f"{type(self).__name__} cannot be constructed directly. "
            f"Use `{type(self).__name__}.resolve(...)` instead."
        )

    def _build_context(self, **context_kwargs: Any) -> Any:
        """Build the resolution context threaded to field resolvers.

        Returns ``None`` here; a resolution source (e.g. AWS shared config
        files) subclasses this to construct and return its context.
        """
        return None

    async def _validate_context_async(self, ctx: Any) -> None:
        """Async hook to fail fast on the resolution context before field resolution."""

    def _validate_context(self, ctx: Any) -> None:
        """Hook to fail fast on the resolution context before field resolution."""

    def _resolve_credentials(self, overrides: dict[str, Any], *, async_: bool) -> None:
        """Hook to validate/auto-wire credentials before the field loop. No-op here."""

    @classmethod
    async def _resolve_async(
        cls,
        *,
        overrides: Mapping[str, object],
        **context_kwargs: Any,
    ) -> Self:
        """Internal async resolution entry point for the async config subclass."""
        instance = cls._create_instance()
        ctx = instance._build_context(**context_kwargs)
        instance._ctx = ctx
        await instance._validate_context_async(ctx)
        await instance._resolve_fields_async(dict(overrides))
        return instance

    @classmethod
    def _resolve(
        cls,
        *,
        overrides: Mapping[str, object],
        **context_kwargs: Any,
    ) -> Self:
        """Internal sync resolution entry point for the sync config subclass."""
        instance = cls._create_instance()
        ctx = instance._build_context(**context_kwargs)
        instance._ctx = ctx
        instance._validate_context(ctx)
        instance._resolve_fields(dict(overrides))
        return instance

    async def _resolve_fields_async(self, overrides: dict[str, Any]) -> None:
        """Run the async resolution pipeline for all fields."""
        unknown = set(overrides) - set(self._FIELDS)
        if unknown:
            raise ConfigValidationError(
                f"Unknown config field(s): {sorted(unknown)}. "
                f"Valid fields are: {sorted(self._FIELDS)}"
            )

        self._resolve_credentials(overrides, async_=True)

        for field_name, spec in self._FIELDS.items():
            if field_name in overrides:
                value = overrides[field_name]
                if spec.converter is not None:
                    value = spec.converter(value)
                setattr(self, field_name, value)
                self._sources[field_name] = ConfigSource.OVERRIDE
            else:
                resolver = spec.async_resolver
                if resolver is not None:
                    result: Resolved[Any] = await resolver(self._ctx)
                    if result.value is not UNSET:
                        setattr(self, field_name, result.value)
                        self._sources[field_name] = result.source
                    else:
                        self._apply_default(field_name, spec, async_=True)
                elif spec.resolver is not None:
                    sync_result: Resolved[Any] = spec.resolver(self._ctx)
                    if sync_result.value is not UNSET:
                        setattr(self, field_name, sync_result.value)
                        self._sources[field_name] = sync_result.source
                    else:
                        self._apply_default(field_name, spec, async_=True)
                else:
                    self._apply_default(field_name, spec, async_=True)

            if spec.validator is not None:
                spec.validator(getattr(self, field_name))

    def _resolve_fields(self, overrides: dict[str, Any]) -> None:
        """Run the synchronous resolution pipeline for all fields."""
        unknown = set(overrides) - set(self._FIELDS)
        if unknown:
            raise ConfigValidationError(
                f"Unknown config field(s): {sorted(unknown)}. "
                f"Valid fields are: {sorted(self._FIELDS)}"
            )

        self._resolve_credentials(overrides, async_=False)

        for field_name, spec in self._FIELDS.items():
            if field_name in overrides:
                value = overrides[field_name]
                if spec.converter is not None:
                    value = spec.converter(value)
                setattr(self, field_name, value)
                self._sources[field_name] = ConfigSource.OVERRIDE
            elif spec.resolver is not None:
                result: Resolved[Any] = spec.resolver(self._ctx)
                if result.value is not UNSET:
                    setattr(self, field_name, result.value)
                    self._sources[field_name] = result.source
                else:
                    self._apply_default(field_name, spec)
            else:
                self._apply_default(field_name, spec)

            if spec.validator is not None:
                spec.validator(getattr(self, field_name))

    def _apply_default(
        self, field_name: str, spec: FieldSpec, async_: bool = False
    ) -> None:
        """Apply the default value for a field."""
        if async_ and spec.async_default_factory is not None:
            value = spec.async_default_factory()
        elif spec.default_factory is not None:
            value = spec.default_factory()
        else:
            value = spec.default
        setattr(self, field_name, value)
        self._sources[field_name] = ConfigSource.DEFAULT

    def source_of(self, field_name: str) -> ConfigSource | None:
        """Get the source that provided a field's value.

        :param field_name: The config field name.
        :returns: The ConfigSource, or None if not tracked.
        """
        return self._sources.get(field_name)

    def resolution_context(self) -> Any:
        """Get the resolution context used to create this config.

        :returns: The context object, or None if not available.
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

    def __setattr__(self, name: str, value: Any) -> None:
        """Guard and track config fields set after resolution.

        Rejects unknown field names, validates the new value, and records the
        field as an override so ``source_of()`` stays accurate when plugins
        customize a config per request.
        """
        if not name.startswith("_") and name not in self.__class__._FIELDS:
            raise AttributeError(
                f"'{type(self).__name__}' has no config field '{name}'"
            )

        spec = self.__class__._FIELDS.get(name)
        if spec is not None and spec.converter is not None and value is not UNSET:
            value = spec.converter(value)

        self._guard_setattr(name, value, spec)

        if spec is not None and hasattr(self, "_sources") and name in self._sources:
            if spec.validator is not None:
                spec.validator(value)
            self._sources[name] = ConfigSource.OVERRIDE
        super().__setattr__(name, value)

    def _guard_setattr(self, name: str, value: Any, spec: FieldSpec | None) -> None:
        """Hook to reject a post-resolution assignment. No-op here."""

    # Resolved component fields shared (identity-preserved), not duplicated, on a deep
    # copy. Clients deep-copy config per operation call to scope plugin mutations;
    # rebuilding these per request would be wasteful and, for live resources, wrong.
    _DEEPCOPY_SHARED_FIELDS: ClassVar[tuple[str, ...]] = ("transport", "retry_strategy")

    def __deepcopy__(self, memo: dict[int, Any]) -> Self:
        """Deep-copy the config while sharing resources that must not be duplicated."""
        for name in self._DEEPCOPY_SHARED_FIELDS:
            shared = getattr(self, name, None)
            if shared is not None:
                memo[id(shared)] = shared
        new = self._create_instance()
        memo[id(self)] = new
        for f in fields(self):
            object.__setattr__(new, f.name, deepcopy(getattr(self, f.name), memo))
        return new


@dataclass(kw_only=True, init=False, repr=False)
class Config(ConfigBase):
    """Synchronous client config. Resolve with :py:meth:`resolve`."""

    @classmethod
    def resolve(cls, **overrides: Any) -> Self:
        """Resolve a config from defaults and explicit overrides.

        :param overrides: Explicit field values that skip resolution.
        :returns: A fully-resolved config instance.
        """
        return cls._resolve(overrides=overrides)


@dataclass(kw_only=True, init=False, repr=False)
class AsyncConfig(ConfigBase):
    """Asynchronous client config. Resolve with :py:meth:`resolve`."""

    @classmethod
    async def resolve(cls, **overrides: Any) -> Self:
        """Resolve a config from defaults and explicit overrides.

        :param overrides: Explicit field values that skip resolution.
        :returns: A fully-resolved config instance.
        """
        return await cls._resolve_async(overrides=overrides)
