#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass
from typing import Any, Protocol

from smithy_core.aio.interfaces.identity import AsyncIdentityResolver
from smithy_core.interfaces.identity import Identity
from smithy_http.aio.interfaces import AsyncHTTPClient

from ....config.merged_config import MergedConfig
from ....identity.chain.ordering import OrderingConstraint
from ....identity.chain.provider import (
    _ChainSetupBase,  # pyright: ignore[reportPrivateUsage]
    _NamedResolverBase,  # pyright: ignore[reportPrivateUsage]
)

__all__ = [
    "ChainIdentityProvider",
    "ChainSetup",
    "NamedResolver",
]


@dataclass(frozen=True, kw_only=True)
class NamedResolver(_NamedResolverBase):
    """Associates an identity resolver with its provider's metadata."""

    resolver: AsyncIdentityResolver[Any, Any]

    async def get_identity(self, *, properties: Mapping[str, Any]) -> Any:
        """Resolve an identity using the underlying resolver."""
        return await self.resolver.get_identity(properties=properties)

    async def invalidate(self) -> None:
        """Invalidate any identity cached by the underlying resolver."""
        await self.resolver.invalidate()


class ChainSetup(_ChainSetupBase):
    """Tracks shared state and resolvers during chain setup."""

    _NAMED_RESOLVER = NamedResolver

    def __init__(
        self,
        *,
        config_file: MergedConfig | None = None,
        profile_name: str | None = None,
        region_override: str | None = None,
        http_client: AsyncHTTPClient | None = None,
        properties: MutableMapping[str, Any] | None = None,
    ) -> None:
        super().__init__(
            config_file=config_file,
            profile_name=profile_name,
            region_override=region_override,
            http_client=http_client,
            properties=properties,
        )

    @property
    def http_client(self) -> AsyncHTTPClient | None:
        """Return the HTTP client to use for network calls, if provided."""
        return self._http_client

    @property
    def resolvers(self) -> tuple[NamedResolver, ...]:
        """Return named resolvers in the order they were added."""
        return tuple(self._resolvers)

    def add_resolver(self, resolver: AsyncIdentityResolver[Any, Any]) -> None:
        """Add a named resolver and continue assembly."""
        self._add(resolver)

    def add_terminal_resolver(self, resolver: AsyncIdentityResolver[Any, Any]) -> None:
        """Add a named resolver and stop assembly."""
        self._add_terminal(resolver)


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
