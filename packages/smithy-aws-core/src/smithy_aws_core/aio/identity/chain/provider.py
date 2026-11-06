#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass
from typing import Any, Protocol

from smithy_core.aio.interfaces.identity import AsyncIdentityResolver
from smithy_core.interfaces.identity import Identity
from smithy_http.aio.interfaces import AsyncHTTPClient

from ....business_metrics import (
    AwsFeatureId,
    add_feature_id,
    normalize_feature_ids,
)
from ....config.merged_config import MergedConfig
from ....identity.chain.ordering import OrderingConstraint

__all__ = [
    "ChainIdentityProvider",
    "ChainSetup",
    "NamedResolver",
]


@dataclass(frozen=True, kw_only=True)
class NamedResolver:
    """Associates an identity resolver with its provider's metadata."""

    provider_name: str
    resolver: AsyncIdentityResolver[Any, Any]
    feature_ids: tuple[AwsFeatureId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "feature_ids", normalize_feature_ids(self.feature_ids))

    async def get_identity(self, *, properties: Mapping[str, Any]) -> Any:
        """Resolve an identity and record the provider's features for the call."""
        features = properties.get("feature_ids")
        if features is None or not self.feature_ids:
            return await self.resolver.get_identity(properties=properties)
        # Record the provider's feature IDs instead of the resolver's own. Leaving out
        # the call's feature record keeps the resolver from recording its own, which is
        # meant for when it's used directly.
        resolver_properties = {
            key: value for key, value in properties.items() if key != "feature_ids"
        }
        identity = await self.resolver.get_identity(properties=resolver_properties)
        for feature_id in self.feature_ids:
            add_feature_id(features, feature_id)
        return identity

    async def invalidate(self) -> None:
        """Invalidate any identity cached by the underlying resolver."""
        await self.resolver.invalidate()


class ChainSetup:
    """Tracks shared state and resolvers during chain setup."""

    def __init__(
        self,
        *,
        config_file: MergedConfig | None = None,
        profile_name: str | None = None,
        region_override: str | None = None,
        http_client: AsyncHTTPClient | None = None,
        properties: MutableMapping[str, Any] | None = None,
    ) -> None:
        self._config_file = config_file
        self._profile_name = profile_name
        self._region_override = region_override
        self._http_client = http_client
        self._properties: MutableMapping[str, Any] = (
            {} if properties is None else properties
        )
        self._resolvers: list[NamedResolver] = []
        self._current_provider: ChainIdentityProvider | None = None
        self._terminal = False

    @property
    def config_file(self) -> MergedConfig | None:
        """Return the parsed config/credentials file, if loaded."""
        return self._config_file

    @property
    def profile_name(self) -> str | None:
        """Return the profile name, if selected."""
        return self._profile_name

    @property
    def region_override(self) -> str | None:
        """Return the region override, if provided."""
        return self._region_override

    @property
    def http_client(self) -> AsyncHTTPClient | None:
        """Return the HTTP client to use for network calls, if provided."""
        return self._http_client

    @property
    def properties(self) -> MutableMapping[str, Any]:
        """Return the property bag shared by custom providers."""
        return self._properties

    @property
    def resolvers(self) -> tuple[NamedResolver, ...]:
        """Return named resolvers in the order they were added."""
        return tuple(self._resolvers)

    @property
    def terminal(self) -> bool:
        """Return whether a provider added a terminal resolver."""
        return self._terminal

    def set_current_provider(self, provider: ChainIdentityProvider) -> None:
        """Set the provider whose setup method is currently running."""
        if self._terminal:
            raise RuntimeError("Cannot change provider after a terminal resolver.")
        self._current_provider = provider

    def set_config_file(self, config_file: MergedConfig) -> None:
        """Set the parsed config file without overwriting an existing value."""
        if self._config_file is not None:
            raise RuntimeError("Cannot overwrite a config file already present.")
        self._config_file = config_file

    def set_profile_name(self, profile_name: str) -> None:
        """Set the resolved name of the active profile."""
        self._profile_name = profile_name

    def add_resolver(self, resolver: AsyncIdentityResolver[Any, Any]) -> None:
        """Add a named resolver and continue assembly."""
        if self._terminal:
            raise RuntimeError("Cannot add a resolver after a terminal resolver.")
        if self._current_provider is None:
            raise RuntimeError("Cannot add a resolver without a current provider.")
        # A provider's feature_ids may be a tuple of one or more feature IDs, a single
        # feature ID without a tuple, or None. None is for providers, such as custom
        # ones, that have no feature ID and set it to None explicitly.
        feature_ids = getattr(self._current_provider, "feature_ids", ())
        self._resolvers.append(
            NamedResolver(
                provider_name=self._current_provider.name,
                resolver=resolver,
                feature_ids=feature_ids,
            )
        )

    def add_terminal_resolver(self, resolver: AsyncIdentityResolver[Any, Any]) -> None:
        """Add a named resolver and stop assembly."""
        self.add_resolver(resolver)
        self._terminal = True


class ChainIdentityProvider(Protocol):
    """Inspects setup state and conditionally adds identity resolvers.

    Providers may also define ``feature_ids``, the features recorded for a call when
    one of their resolvers returns its identity.
    """

    @property
    def name(self) -> str:
        """Return the canonical provider name."""
        ...

    @property
    def ordering(self) -> OrderingConstraint:
        """Return the provider's chain ordering constraint."""
        ...

    async def setup(
        self,
        identity_type: type[Identity],
        setup: ChainSetup,
    ) -> None:
        """Add resolvers for the requested identity type."""
        ...
