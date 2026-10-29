#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import logging
from collections.abc import Mapping, Sequence
from typing import Any, Final

from ..identity import (
    _invalidate_all,  # pyright: ignore[reportPrivateUsage]
    _resolve_from_chain,  # pyright: ignore[reportPrivateUsage]
)
from ..interfaces.identity import Identity
from ._program import run_program_async
from .interfaces.identity import AsyncIdentityResolver

__all__ = ["AsyncCachingIdentityResolver", "AsyncChainedIdentityResolver"]

logger: Final = logging.getLogger(__name__)


# TODO: turn this into a decorator
class AsyncCachingIdentityResolver[I: Identity, IP: Mapping[str, Any]](
    AsyncIdentityResolver[I, IP]
):
    def __init__(self) -> None:
        self._cached: I | None = None

    async def get_identity(self, *, properties: IP) -> I:
        if self._cached is None or self._cached.is_expired:
            self._cached = await self._get_identity(properties=properties)
        return self._cached

    async def _get_identity(self, *, properties: IP) -> I:
        raise NotImplementedError

    async def invalidate(self) -> None:
        """Discard the cached identity so the next resolution re-reads its source."""
        self._cached = None


class AsyncChainedIdentityResolver[I: Identity, IP: Mapping[str, Any]](
    AsyncCachingIdentityResolver[I, IP]
):
    """Attempts to resolve an identity by checking a sequence of sub-resolvers.

    If a nested resolver raises a :py:class:`SmithyIdentityError`, the next
    resolver in the chain will be attempted.
    """

    def __init__(self, resolvers: Sequence[AsyncIdentityResolver[I, IP]]) -> None:
        """Construct a AsyncChainedIdentityResolver.

        :param resolvers: The sequence of resolvers to resolve identity from.
        """
        super().__init__()
        self._resolvers = resolvers

    async def _get_identity(self, *, properties: IP) -> I:
        return await run_program_async(
            _resolve_from_chain(self._resolvers, properties)  # pyright: ignore[reportPrivateUsage]
        )

    async def invalidate(self) -> None:
        """Discard this chain's cached identity and invalidate every sub-resolver."""
        await super().invalidate()
        await run_program_async(_invalidate_all(self._resolvers))  # pyright: ignore[reportPrivateUsage]
