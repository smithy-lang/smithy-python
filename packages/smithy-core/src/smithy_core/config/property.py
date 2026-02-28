# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Callable
from typing import Any

from smithy_core.config.resolver import ConfigResolver


class ConfigProperty:
    """Descriptor for config properties with resolution, caching, and validation.

    This descriptor handles:
    - Lazy resolution from sources (only on first access)
    - Custom resolution for variables requiring complex resolution
    - Caching of resolved values
    - Source tracking for provenance
    - Validation of values

    Example:
        class Config:
            region = ConfigProperty('region', validator=validate_region)

            def __init__(self):
                self._resolver = ConfigResolver(sources=[...])
    """

    def __init__(
        self,
        key: str,
        validator: Callable[[Any, str | None], Any] | None = None,
        resolver_func: Callable[[ConfigResolver], tuple[Any, str | None]] | None = None,
        default_value: Any = None,
    ):
        """Initialize config property descriptor.

        :param key: The configuration key (e.g., 'region')
        :param validator: Optional validation function that takes (value, source)
                      and returns validated value or raises an exception
        :param resolver_func: Optional custom resolver function for complex resolution.
                  Takes a ConfigResolver and returns (value, source) tuple.
        """
        self.key = key
        self.validator = validator
        self.resolver_func = resolver_func
        # Cache attribute name in instance __dict__ (e.g., "_cache_region")
        self.cache_attr = f"_cache_{key}"
        self.default_value = default_value

    def __get__(self, obj: Any, objtype: type | None = None) -> Any:
        """Get the config value with lazy resolution and caching.

        On first access, the property checks if the value is already cached. If not, it resolves
        the value from sources using resolver. When a validator is provided, the resolved value
        is validated before use. Finally, the property caches the (value, source) tuple. On
        subsequent accesses, it returns the cached value.

        :param obj: The Config instance
        :param objtype: The Config class

        :returns: The resolved and validated config value
        """
        # If accessed on class instead of instance, return descriptor itself
        if obj is None:
            return self

        cached = getattr(obj, self.cache_attr, None)
        if cached is not None:
            return cached[
                0
            ]  # Return value from tuple (value, source) if already cached

        # If not cached, use a resolver to go through the sources to get (value, source)
        # For complex config resolutions, use a custom resolver function to resolve values
        if self.resolver_func:
            value, source = self.resolver_func(obj._resolver)
        else:
            value, source = obj._resolver.get(self.key)

        if value is None:
            value = self.default_value
            source = "default"

        if self.validator:
            value = self.validator(value, source)

        setattr(obj, self.cache_attr, (value, source))
        return value

    def __set__(self, obj: Any, value: Any) -> None:
        """Set the config value (called during __init__ or after).

        When a config value is set, the property validates the new value if a validator is provided, then
        updates the cached (value, source) tuple. The source is marked as 'instance' if the value
        is set during __init__, or 'in-code' if set later.

        :param obj: The Config instance
        :param value: The new value to set
        """
        # Determine source based on when the value was set
        # If cache already exists, it means it was not set during initialization
        # In that case source will be set to in-code
        source = "in-code" if hasattr(obj, self.cache_attr) else "instance"
        if self.validator:
            value = self.validator(value, source)

        setattr(obj, self.cache_attr, (value, source))
