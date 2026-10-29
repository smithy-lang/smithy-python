#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import logging
from collections.abc import Mapping, Sequence
from typing import Any, Final

from ._program import Program, run_program
from .exceptions import SmithyIdentityError
from .interfaces.identity import Identity, IdentityResolver

__all__ = ["CachingIdentityResolver", "ChainedIdentityResolver"]

logger: Final = logging.getLogger(__name__)


def _resolve_from_chain[I](
    resolvers: Sequence[object], properties: Mapping[str, Any]
) -> Program[I]:
    """Resolve an identity from the first resolver in a chain that can provide one."""
    logger.debug("Attempting to resolve identity from resolver chain.")
    for resolver in resolvers:
        resolve: Any = getattr(resolver, "get_identity")
        try:
            logger.debug("Attempting to resolve identity from %s.", type(resolver))
            return (yield lambda: resolve(properties=properties))
        except SmithyIdentityError as e:
            logger.debug("Failed to resolve identity from %s: %s", type(resolver), e)
    raise SmithyIdentityError("Failed to resolve identity from resolver chain.")


def _invalidate_all(resolvers: Sequence[object]) -> Program[None]:
    for resolver in resolvers:
        yield getattr(resolver, "invalidate")


class CachingIdentityResolver[I: Identity, IP: Mapping[str, Any]](
    IdentityResolver[I, IP]
):
    """An identity resolver that caches an identity until it expires."""

    def __init__(self) -> None:
        self._cached: I | None = None

    def get_identity(self, *, properties: IP) -> I:
        if self._cached is None or self._cached.is_expired:
            self._cached = self._get_identity(properties=properties)
        return self._cached

    def _get_identity(self, *, properties: IP) -> I:
        raise NotImplementedError

    def invalidate(self) -> None:
        """Discard the cached identity so the next resolution re-reads its source."""
        self._cached = None


class ChainedIdentityResolver[I: Identity, IP: Mapping[str, Any]](
    CachingIdentityResolver[I, IP]
):
    """Attempts to resolve an identity by checking a sequence of sub-resolvers.

    If a nested resolver raises a :py:class:`SmithyIdentityError`, the next resolver in
    the chain will be attempted.
    """

    def __init__(self, resolvers: Sequence[IdentityResolver[I, IP]]) -> None:
        """Construct a ChainedIdentityResolver.

        :param resolvers: The sequence of resolvers to resolve identity from.
        """
        super().__init__()
        self._resolvers = resolvers

    def _get_identity(self, *, properties: IP) -> I:
        return run_program(_resolve_from_chain(self._resolvers, properties))

    def invalidate(self) -> None:
        """Discard this chain's cached identity and invalidate every sub-resolver."""
        super().invalidate()
        run_program(_invalidate_all(self._resolvers))
