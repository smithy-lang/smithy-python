#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass
from typing import Any

from smithy_core.aio.interfaces.identity import IdentityResolver
from smithy_core.exceptions import SmithyError, SmithyIdentityError


class IdentityChainConfigurationError(SmithyError):
    """Raised when discovered providers violate an assembly invariant."""


@dataclass(frozen=True, kw_only=True)
class UnclaimedSource:
    """A detected credential source that no registered provider claims.

    Carries the installable package to suggest so the caller can add the provider
    that would claim the source.
    """

    source_name: str
    package: str

    def __str__(self) -> str:
        return (
            f"{self.source_name} credential source was detected but no provider "
            f"claims it; install '{self.package}'."
        )


@dataclass(frozen=True, kw_only=True)
class IdentityResolverFailure:
    """A failed identity resolution attempt."""

    provider_name: str
    resolver: IdentityResolver[Any, Any]
    error: SmithyIdentityError


class IdentityChainError(SmithyIdentityError):
    """Raised when every resolver in an identity chain misses."""

    def __init__(
        self,
        *,
        failures: tuple[IdentityResolverFailure, ...],
        unclaimed_sources: tuple[UnclaimedSource, ...] = (),
    ) -> None:
        self.failures = failures
        self.unclaimed_sources = unclaimed_sources
        if not failures:
            message = "No credential providers were configured to resolve an identity."
        else:
            attempted = "; ".join(
                f"{failure.provider_name}: {failure.error}" for failure in failures
            )
            message = "Unable to resolve identity from any provider in the chain."
            message = f"{message} Providers attempted: {attempted}."
        if unclaimed_sources:
            suggestions = " ".join(str(source) for source in unclaimed_sources)
            message = f"{message} {suggestions}"
        super().__init__(message)
