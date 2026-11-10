#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass
from typing import Any, ClassVar, Protocol

from smithy_core.interfaces.identity import Identity, IdentityResolver
from smithy_core.program import Program, run_program
from smithy_http.interfaces import HTTPClient

from ..._private.identity_features import (
    FEATURE_IDS_PROPERTY,
    record_features,
    without_feature_record,
)
from ...business_metrics import AwsFeatureId, normalize_feature_ids
from ...config.merged_config import MergedConfig
from ..components import AWSCredentialsIdentity
from .exceptions import IdentityChainConfigurationError
from .ordering import OrderingConstraint

__all__ = [
    "ChainIdentityProvider",
    "ChainSetup",
    "NamedResolver",
]


@dataclass(frozen=True, kw_only=True)
class _NamedResolverBase:
    """Associates an identity resolver with its provider's metadata."""

    provider_name: str
    resolver: Any
    feature_ids: tuple[AwsFeatureId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "feature_ids", normalize_feature_ids(self.feature_ids))

    def _get_identity(self, properties: Mapping[str, Any]) -> Program[Any]:
        """Resolve an identity and record the provider's features for the call."""
        if properties.get(FEATURE_IDS_PROPERTY) is None or not self.feature_ids:
            return (yield lambda: self.resolver.get_identity(properties=properties))
        # The provider's features replace the resolver's own, which are for when
        # it's used directly, so the resolver doesn't see the call's record.
        stripped = without_feature_record(properties)
        identity = yield lambda: self.resolver.get_identity(properties=stripped)
        record_features(properties, self.feature_ids)
        return identity


@dataclass(frozen=True, kw_only=True)
class NamedResolver(_NamedResolverBase):
    """Associates an identity resolver with its provider's metadata."""

    resolver: IdentityResolver[Any, Any]

    def get_identity(self, *, properties: Mapping[str, Any]) -> Any:
        """Resolve an identity and record the provider's features for the call."""
        return run_program(self._get_identity(properties))

    def invalidate(self) -> None:
        """Invalidate any identity cached by the underlying resolver."""
        self.resolver.invalidate()


class _ChainSetupBase:
    """Chain setup state shared by the sync and async chains."""

    _NAMED_RESOLVER: ClassVar[Any]

    def __init__(
        self,
        *,
        config_file: MergedConfig | None = None,
        profile_name: str | None = None,
        region_override: str | None = None,
        http_client: Any | None = None,
        properties: MutableMapping[str, Any] | None = None,
    ) -> None:
        self._config_file = config_file
        self._profile_name = profile_name
        self._region_override = region_override
        self._http_client = http_client
        self._properties: MutableMapping[str, Any] = (
            {} if properties is None else properties
        )
        self._resolvers: list[Any] = []
        self._current_provider: Any | None = None
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
    def properties(self) -> MutableMapping[str, Any]:
        """Return the property bag shared by custom providers."""
        return self._properties

    @property
    def resolvers(self) -> tuple[Any, ...]:
        """Return named resolvers in the order they were added."""
        return tuple(self._resolvers)

    @property
    def terminal(self) -> bool:
        """Return whether a provider added a terminal resolver."""
        return self._terminal

    def set_current_provider(self, provider: Any) -> None:
        """Set the provider whose setup method is currently running."""
        if self._terminal:
            raise IdentityChainConfigurationError(
                "Cannot change provider after a terminal resolver."
            )
        self._current_provider = provider

    def set_config_file(self, config_file: MergedConfig) -> None:
        """Set the parsed config file without overwriting an existing value."""
        if self._config_file is not None:
            raise IdentityChainConfigurationError(
                "Cannot overwrite a config file already present."
            )
        self._config_file = config_file

    def set_profile_name(self, profile_name: str) -> None:
        """Set the resolved name of the active profile."""
        self._profile_name = profile_name

    def _add(self, resolver: Any) -> None:
        """Add a named resolver and continue assembly."""
        if self._terminal:
            raise IdentityChainConfigurationError(
                "Cannot add a resolver after a terminal resolver."
            )
        if self._current_provider is None:
            raise IdentityChainConfigurationError(
                "Cannot add a resolver without a current provider."
            )
        # A provider's feature_ids may be a tuple of feature IDs, a single one, or
        # None for providers, such as custom ones, that have none.
        self._resolvers.append(
            self._NAMED_RESOLVER(
                provider_name=self._current_provider.name,
                resolver=resolver,
                feature_ids=getattr(self._current_provider, "feature_ids", ()),
            )
        )

    def _add_terminal(self, resolver: Any) -> None:
        self._add(resolver)
        self._terminal = True

    def _static_resolver(self, identity: AWSCredentialsIdentity) -> Any:
        """Create a resolver for fixed credentials in this chain's mode."""
        raise NotImplementedError

    def _environment_resolver(self) -> Any:
        """Create a resolver for environment credentials in this chain's mode."""
        raise NotImplementedError

    def _process_resolver(self, command: list[str], account_id: str | None) -> Any:
        """Create a credential process resolver in this chain's mode."""
        raise NotImplementedError

    def _load_config(self) -> Any:
        """Effect: load the shared config and credentials files."""
        raise NotImplementedError

    def _run(self, program: Program[None]) -> Any:
        """Drive a provider's setup program in this chain's mode."""
        raise NotImplementedError


class ChainSetup(_ChainSetupBase):
    """Tracks shared state and resolvers during chain setup."""

    _NAMED_RESOLVER = NamedResolver

    def __init__(
        self,
        *,
        config_file: MergedConfig | None = None,
        profile_name: str | None = None,
        region_override: str | None = None,
        http_client: HTTPClient | None = None,
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
    def http_client(self) -> HTTPClient | None:
        """Return the HTTP client to use for network calls, if provided."""
        return self._http_client

    @property
    def resolvers(self) -> tuple[NamedResolver, ...]:
        """Return named resolvers in the order they were added."""
        return tuple(self._resolvers)

    def add_resolver(self, resolver: IdentityResolver[Any, Any]) -> None:
        """Add a named resolver and continue assembly."""
        self._add(resolver)

    def add_terminal_resolver(self, resolver: IdentityResolver[Any, Any]) -> None:
        """Add a named resolver and stop assembly."""
        self._add_terminal(resolver)

    def _static_resolver(self, identity: AWSCredentialsIdentity) -> Any:
        from ..static import StaticCredentialsResolver

        return StaticCredentialsResolver(identity)

    def _environment_resolver(self) -> Any:
        from ..environment import EnvironmentCredentialsResolver

        return EnvironmentCredentialsResolver()

    def _process_resolver(self, command: list[str], account_id: str | None) -> Any:
        from ..process import ProcessCredentialsResolver

        return ProcessCredentialsResolver(command, account_id=account_id)

    def _load_config(self) -> Any:
        from ...config.context import load_config

        return load_config()

    def _run(self, program: Program[None]) -> None:
        run_program(program)


class ChainIdentityProvider(Protocol):
    """Inspects setup state and conditionally adds sync identity resolvers.

    A provider that only uses the setup's resolver factories works in the async
    chain too, since ``setup`` creates resolvers in its own mode. Providers may also
    define ``feature_ids``, the features recorded for a call when one of their
    resolvers returns its identity.
    """

    @property
    def name(self) -> str:
        """Return the canonical provider name."""
        ...

    @property
    def ordering(self) -> OrderingConstraint:
        """Return the provider's chain ordering constraint."""
        ...

    def setup(
        self,
        identity_type: type[Identity],
        setup: ChainSetup,
    ) -> None:
        """Add resolvers for the requested identity type."""
        ...
