#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import logging
from collections.abc import Callable, Mapping, Sequence
from importlib import metadata
from typing import Any, cast

from smithy_core._program import Program, run_program
from smithy_core.exceptions import SmithyIdentityError
from smithy_core.interfaces.identity import Identity, IdentityResolver
from smithy_http.interfaces import HTTPClient

from ...config.merged_config import MergedConfig
from .exceptions import (
    IdentityChainConfigurationError,
    IdentityChainError,
    IdentityResolverFailure,
    UnclaimedSource,
)
from .ordering import After, Before, Standard, StandardProvider
from .provider import (
    ChainIdentityProvider,
    ChainSetup,
    _NamedResolverBase,  # pyright: ignore[reportPrivateUsage]
)

__all__ = ("IdentityChain",)

_CHAIN_PROVIDER_ENTRY_POINT_GROUP = "smithy_aws_core.identity.chain_providers"
logger = logging.getLogger(__name__)


def _discover_providers(group: str) -> tuple[Any, ...]:
    discovered: list[Any] = []
    for entry_point in metadata.entry_points(group=group):
        provider_factory = cast(Callable[[], Any], entry_point.load())
        discovered.append(provider_factory())
    return tuple(discovered)


def _assemble(
    identity_type: type[Identity],
    discovered_providers: Sequence[Any],
    setup: Any,
    chain_logger: logging.Logger,
) -> Program[tuple[UnclaimedSource, ...]]:
    """Run each discovered provider's setup in chain order."""
    _validate_providers(discovered_providers)
    providers = _sort_by_ordering(discovered_providers)
    unclaimed_sources = _find_unclaimed_sources(discovered_providers)

    for provider in providers:
        setup.set_current_provider(provider)
        yield lambda: provider.setup(identity_type, setup)
        if setup.terminal:
            break

    for source in unclaimed_sources:
        chain_logger.warning(str(source))
    return unclaimed_sources


class _IdentityChainBase[I: Identity]:
    """Identity chain logic shared by the sync and async chains."""

    _resolvers: tuple[Any, ...]
    _identity_type: type[I] | None
    _unclaimed_sources: tuple[UnclaimedSource, ...]

    def __init__(
        self,
        resolvers: Sequence[Any],
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

    def _get_identity(self, properties: Mapping[str, Any]) -> Program[I]:
        failures: list[IdentityResolverFailure] = []
        for resolver in self._resolvers:
            try:
                return (yield lambda: resolver.get_identity(properties=properties))
            except SmithyIdentityError as error:
                if isinstance(resolver, _NamedResolverBase):
                    provider_name = resolver.provider_name
                else:
                    provider_name = type(resolver).__name__
                failures.append(
                    IdentityResolverFailure(
                        provider_name=provider_name,
                        error=error,
                    )
                )

        raise IdentityChainError(
            failures=tuple(failures),
            unclaimed_sources=self._unclaimed_sources,
        )

    def _invalidate(self) -> Program[None]:
        for resolver in self._resolvers:
            yield resolver.invalidate


class IdentityChain[I: Identity](
    _IdentityChainBase[I], IdentityResolver[I, Mapping[str, Any]]
):
    """Resolves identities from an assembled sequence of resolvers."""

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
            chain assembly.
        """
        super().__init__(
            resolvers, identity_type=identity_type, unclaimed_sources=unclaimed_sources
        )

    @staticmethod
    def create[ChainIdentity: Identity](
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
        :param profile_name: Explicit profile name to use. When set, top-level
            environment credential resolution is suppressed.
        :param region_override: Region to use for providers whose resolvers
            fetch credentials through a service call.
        :param http_client: HTTP client to use for providers whose resolvers make
            network calls.
        """
        setup = ChainSetup(
            config_file=config_file,
            profile_name=profile_name,
            region_override=region_override,
            http_client=http_client,
        )
        discovered: tuple[ChainIdentityProvider, ...] = _discover_providers(
            _CHAIN_PROVIDER_ENTRY_POINT_GROUP
        )
        unclaimed_sources = run_program(
            _assemble(identity_type, discovered, setup, logger)
        )
        return IdentityChain(
            setup.resolvers,
            identity_type=identity_type,
            unclaimed_sources=unclaimed_sources,
        )

    def get_identity(self, *, properties: Mapping[str, Any]) -> I:
        """Return the first identity resolved by the chain."""
        return run_program(self._get_identity(properties))

    def invalidate(self) -> None:
        """Invalidate every resolver in the chain."""
        run_program(self._invalidate())


def _sort_by_ordering(
    providers: Sequence[Any],
) -> tuple[Any, ...]:
    if not providers:
        return ()
    slot_indexes = {slot: index for index, slot in enumerate(StandardProvider)}

    def sort_key(
        indexed_provider: tuple[int, Any],
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

        return (slot_indexes[ordering.slot], constraint_precedence, discovery_index)

    indexed_providers = enumerate(providers)
    ordered_providers = sorted(indexed_providers, key=sort_key)
    return tuple(provider for _, provider in ordered_providers)


def _validate_providers(providers: Sequence[Any]) -> None:
    discovered_names: dict[str, Any] = {}
    discovered_standard_slots: dict[StandardProvider, Any] = {}

    for provider in providers:
        normalized_name = provider.name.casefold()
        if (previous := discovered_names.get(normalized_name)) is not None:
            raise IdentityChainConfigurationError(
                f"Credential providers {type(previous).__name__} and "
                f"{type(provider).__name__} use the same name: {provider.name}."
            )
        discovered_names[normalized_name] = provider

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
    providers: Sequence[Any],
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
