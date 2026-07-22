#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass
from typing import Any, Protocol

from smithy_core.aio.interfaces.identity import IdentityResolver
from smithy_core.interfaces.identity import Identity

from ...config.file_parser import Section
from ...config.merged_config import MergedConfig
from .ordering import OrderingConstraint


@dataclass(frozen=True, kw_only=True)
class NamedResolver:
    """Associates an identity resolver with its provider name."""

    provider_name: str
    resolver: IdentityResolver[Any, Any]

    async def get_identity(self, *, properties: Mapping[str, Any]) -> Any:
        """Resolve an identity using the underlying resolver."""
        return await self.resolver.get_identity(properties=properties)


class ChainSetup:
    """Tracks shared state and resolvers during chain setup."""

    def __init__(
        self,
        *,
        profile_file: MergedConfig | None = None,
        profile_name_override: str | None = None,
        properties: MutableMapping[str, Any] | None = None,
    ) -> None:
        self._profile_file = profile_file
        self._profile_name_override = profile_name_override
        self._profile: Section | None = None
        self._properties: MutableMapping[str, Any] = (
            {} if properties is None else properties
        )
        self._resolvers: list[NamedResolver] = []
        self._current_provider: ChainIdentityProvider | None = None
        self._terminal = False

    @property
    def profile_file(self) -> MergedConfig | None:
        """Return the parsed config and credentials files, if loaded."""
        return self._profile_file

    @property
    def profile(self) -> Section | None:
        """Return the active profile, if selected."""
        return self._profile

    @property
    def profile_name_override(self) -> str | None:
        """Return the client-specified profile name, if provided."""
        return self._profile_name_override

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

    def set_profile_file(self, profile_file: MergedConfig) -> None:
        """Set the parsed profile file without overwriting an existing value."""
        if self._profile_file is not None:
            raise RuntimeError("Cannot overwrite a profile file already present.")
        self._profile_file = profile_file

    def set_profile(self, profile: Section) -> None:
        """Set the active profile."""
        self._profile = profile

    def add_resolver(self, resolver: IdentityResolver[Any, Any]) -> None:
        """Add a named resolver and continue assembly."""
        if self._terminal:
            raise RuntimeError("Cannot add a resolver after a terminal resolver.")
        if self._current_provider is None:
            raise RuntimeError("Cannot add a resolver without a current provider.")
        self._resolvers.append(
            NamedResolver(
                provider_name=self._current_provider.name,
                resolver=resolver,
            )
        )

    def add_terminal_resolver(self, resolver: IdentityResolver[Any, Any]) -> None:
        """Add a named resolver and stop assembly."""
        self.add_resolver(resolver)
        self._terminal = True


class ChainIdentityProvider(Protocol):
    """Inspects setup state and conditionally adds identity resolvers."""

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
