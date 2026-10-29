#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import logging
from collections.abc import Callable, Mapping, Sequence
from importlib import metadata
from typing import Any, cast

from smithy_core.aio._program import run_program_async
from smithy_core.aio.interfaces.identity import AsyncIdentityResolver
from smithy_core.interfaces.identity import Identity
from smithy_http.aio.interfaces import AsyncHTTPClient

from ....config.merged_config import MergedConfig
from ....identity.chain.exceptions import UnclaimedSource
from ....identity.chain.resolver import (
    _assemble,  # pyright: ignore[reportPrivateUsage]
    _IdentityChainBase,  # pyright: ignore[reportPrivateUsage]
)
from .provider import ChainIdentityProvider, ChainSetup

__all__ = ("AsyncIdentityChain",)

_CHAIN_PROVIDER_ENTRY_POINT_GROUP = "smithy_aws_core.aio.identity.chain_providers"
logger = logging.getLogger(__name__)


class AsyncIdentityChain[I: Identity](
    _IdentityChainBase[I], AsyncIdentityResolver[I, Mapping[str, Any]]
):
    """Resolves identities from an assembled sequence of resolvers."""

    def __init__(
        self,
        resolvers: Sequence[AsyncIdentityResolver[I, Any]],
        *,
        identity_type: type[I] | None = None,
        unclaimed_sources: Sequence[UnclaimedSource] = (),
    ) -> None:
        """Initialize the chain with resolvers in precedence order.

        :param resolvers: Identity resolvers to iterate in precedence order.
        :param identity_type: The identity type this chain resolves, or None when
            constructing a chain directly without declaring one.
        :param unclaimed_sources: Detected-but-unclaimed sources discovered during
            chain assembly. This parameter is used by :meth:`create`; omit it when
            constructing a chain directly.
        """
        super().__init__(
            resolvers, identity_type=identity_type, unclaimed_sources=unclaimed_sources
        )

    @staticmethod
    async def create[ChainIdentity: Identity](
        identity_type: type[ChainIdentity],
        *,
        config_file: MergedConfig | None = None,
        profile_name: str | None = None,
        region_override: str | None = None,
        http_client: AsyncHTTPClient | None = None,
    ) -> "AsyncIdentityChain[ChainIdentity]":
        """Create an identity chain from discovered providers.

        :param identity_type: The identity type to resolve.
        :param config_file: Parsed config/credentials file. Loaded from disk
            when not set.
        :param profile_name: Explicit profile name to use. When set, top-level
            environment credential resolution is suppressed. If omitted, the shared
            config provider uses ``AWS_PROFILE`` when set, otherwise ``default``.
        :param region_override: Region to use for providers whose resolvers
            fetch credentials through a service call.
        :param http_client: HTTP client to use for providers whose resolvers make
            network calls.
        """
        discovered_providers = _discover_chain_identity_providers()
        setup = ChainSetup(
            config_file=config_file,
            profile_name=profile_name,
            region_override=region_override,
            http_client=http_client,
        )
        unclaimed_sources = await run_program_async(
            _assemble(identity_type, discovered_providers, setup, logger)
        )
        return AsyncIdentityChain(
            setup.resolvers,
            identity_type=identity_type,
            unclaimed_sources=unclaimed_sources,
        )

    async def get_identity(self, *, properties: Mapping[str, Any]) -> I:
        """Return the first identity resolved by the chain."""
        return await run_program_async(self._get_identity(properties))

    async def invalidate(self) -> None:
        """Invalidate every resolver in the chain."""
        await run_program_async(self._invalidate())


def _discover_chain_identity_providers() -> tuple[ChainIdentityProvider, ...]:
    discovered: list[ChainIdentityProvider] = []
    for entry_point in metadata.entry_points(group=_CHAIN_PROVIDER_ENTRY_POINT_GROUP):
        provider_factory = cast(
            Callable[[], ChainIdentityProvider],
            entry_point.load(),
        )
        discovered.append(provider_factory())
    return tuple(discovered)
