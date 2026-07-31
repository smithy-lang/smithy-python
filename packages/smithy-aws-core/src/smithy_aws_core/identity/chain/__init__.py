#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import logging
from collections.abc import Callable, Mapping, Sequence
from importlib import metadata
from typing import Any, cast

from smithy_core.aio.interfaces.identity import IdentityResolver
from smithy_core.exceptions import SmithyIdentityError
from smithy_core.interfaces.identity import Identity
from smithy_http.aio.interfaces import HTTPClient

from ...config.merged_config import MergedConfig
from .exceptions import (
    IdentityChainConfigurationError,
    IdentityChainError,
    IdentityResolverFailure,
    UnclaimedSource,
)
from .ordering import (
    After,
    Before,
    OrderingConstraint,
    Standard,
    StandardProvider,
)
from .provider import (
    ChainIdentityProvider,
    ChainSetup,
    NamedResolver,
)

__all__ = (
    "After",
    "Before",
    "ChainIdentityProvider",
    "ChainSetup",
    "IdentityChain",
    "IdentityChainConfigurationError",
    "IdentityChainError",
    "IdentityResolverFailure",
    "OrderingConstraint",
    "Standard",
    "StandardProvider",
    "UnclaimedSource",
)

_CHAIN_PROVIDER_ENTRY_POINT_GROUP = "smithy_aws_core.identity.chain_providers"
logger = logging.getLogger(__name__)


def _discover_chain_identity_providers() -> tuple[ChainIdentityProvider, ...]:
    discovered: list[ChainIdentityProvider] = []
    for entry_point in metadata.entry_points(group=_CHAIN_PROVIDER_ENTRY_POINT_GROUP):
        provider_factory = cast(
            Callable[[], ChainIdentityProvider],
            entry_point.load(),
        )
        discovered.append(provider_factory())
    return tuple(discovered)


def _sort_by_ordering(
    providers: Sequence[ChainIdentityProvider],
) -> tuple[ChainIdentityProvider, ...]:
    if not providers:
        return ()
    slot_indexes = {slot: index for index, slot in enumerate(StandardProvider)}

    def sort_key(
        indexed_provider: tuple[int, ChainIdentityProvider],
    ) -> tuple[int, int, int]:
        discovery_index, provider = indexed_provider
        ordering = provider.ordering

        match ordering:
            case Before():
                constraint_precedence = 0
            case Standard():
                constraint_precedence = 1
            case After():
                constraint_precedence = 2
            case _:
                raise IdentityChainConfigurationError(
                    f"Provider {type(provider).__name__} returned an unsupported "
                    f"ordering constraint: {ordering!r}."
                )

        # Slot precedence, constraint precedence, then discovery order
        return (slot_indexes[ordering.slot], constraint_precedence, discovery_index)

    indexed_providers = enumerate(providers)
    ordered_providers = sorted(indexed_providers, key=sort_key)
    return tuple(provider for _, provider in ordered_providers)


def _validate_providers(providers: Sequence[ChainIdentityProvider]) -> None:
    discovered_names: dict[str, ChainIdentityProvider] = {}
    discovered_standard_slots: dict[StandardProvider, ChainIdentityProvider] = {}

    for provider in providers:
        if (previous := discovered_names.get(provider.name)) is not None:
            raise IdentityChainConfigurationError(
                f"Credential providers {type(previous).__name__} and "
                f"{type(provider).__name__} use the same name: {provider.name}."
            )
        discovered_names[provider.name] = provider

        ordering = provider.ordering
        if isinstance(ordering, Standard):
            if (previous := discovered_standard_slots.get(ordering.slot)) is not None:
                raise IdentityChainConfigurationError(
                    f"Credential providers {type(previous).__name__} and "
                    f"{type(provider).__name__} both claim standard slot: "
                    f"{ordering.slot.name}."
                )
            discovered_standard_slots[ordering.slot] = provider


def _find_unclaimed_sources(
    providers: Sequence[ChainIdentityProvider],
) -> tuple[UnclaimedSource, ...]:
    claimed_slots = {
        provider.ordering.slot
        for provider in providers
        if isinstance(provider.ordering, Standard)
    }
    unclaimed_sources: list[UnclaimedSource] = []

    for slot in StandardProvider:
        if slot in claimed_slots or not slot.is_detected():
            continue
        package = slot.module_suggestion
        if package:
            unclaimed_sources.append(
                UnclaimedSource(source_name=slot.canonical_name, package=package)
            )

    return tuple(unclaimed_sources)


class IdentityChain[I: Identity](IdentityResolver[I, Mapping[str, Any]]):
    """Resolves identities from an assembled sequence of resolvers."""

    _resolvers: tuple[IdentityResolver[I, Any], ...]
    _identity_type: type[I] | None
    _unclaimed_sources: tuple[UnclaimedSource, ...]

    def __init__(
        self,
        resolvers: Sequence[IdentityResolver[I, Any]],
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
        self._resolvers = tuple(resolvers)
        self._identity_type = identity_type
        self._unclaimed_sources = tuple(unclaimed_sources)

    @property
    def identity_type(self) -> type[I] | None:
        """The identity type this chain resolves, or None if not declared."""
        return self._identity_type

    @staticmethod
    async def create[ChainIdentity: Identity](
        identity_type: type[ChainIdentity],
        *,
        config_file: MergedConfig | None = None,
        profile_name: str | None = None,
        region_override: str | None = None,
        http_client: HTTPClient | None = None,
    ) -> "IdentityChain[ChainIdentity]":
        """Create an identity chain from discovered providers.

        :param identity_type: The identity type to resolve.
        :param config_file: Parsed config/credentials file. Loaded from disk
            when not set.
        :param profile_name: Profile name to use. If omitted, the shared config
            provider uses ``AWS_PROFILE`` when set, otherwise ``default``.
        :param region_override: Region to use for providers whose resolvers
            fetch credentials through a service call.
        :param http_client: HTTP client to use for providers whose resolvers make
            network calls.
        """
        discovered_providers = _discover_chain_identity_providers()
        _validate_providers(discovered_providers)
        providers = _sort_by_ordering(discovered_providers)
        setup = ChainSetup(
            config_file=config_file,
            profile_name=profile_name,
            region_override=region_override,
            http_client=http_client,
        )
        unclaimed_sources = _find_unclaimed_sources(discovered_providers)

        for provider in providers:
            setup.set_current_provider(provider)
            await provider.setup(identity_type, setup)
            if setup.terminal:
                break

        for source in unclaimed_sources:
            logger.warning(str(source))
        return IdentityChain(
            setup.resolvers,
            identity_type=identity_type,
            unclaimed_sources=unclaimed_sources,
        )

    async def get_identity(self, *, properties: Mapping[str, Any]) -> I:
        """Return the first identity resolved by the chain."""
        failures: list[IdentityResolverFailure] = []
        for resolver in self._resolvers:
            try:
                return await resolver.get_identity(properties=properties)
            except SmithyIdentityError as error:
                if isinstance(resolver, NamedResolver):
                    provider_name = resolver.provider_name
                    failed_resolver = resolver.resolver
                else:
                    provider_name = type(resolver).__name__
                    failed_resolver = resolver
                failures.append(
                    IdentityResolverFailure(
                        provider_name=provider_name,
                        resolver=failed_resolver,
                        error=error,
                    )
                )

        raise IdentityChainError(
            failures=tuple(failures),
            unclaimed_sources=self._unclaimed_sources,
        )

    async def invalidate(self) -> None:
        """Invalidate every resolver in the chain."""
        for resolver in self._resolvers:
            await resolver.invalidate()
