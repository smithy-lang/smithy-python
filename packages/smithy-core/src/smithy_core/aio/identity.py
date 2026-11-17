#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import logging
import sys
from collections.abc import Mapping, Sequence
from typing import Any, Final, Generic

from ..identity import (
    _cached_identity,  # pyright: ignore[reportPrivateUsage]
    _invalidate_all,  # pyright: ignore[reportPrivateUsage]
    _resolve_from_chain,  # pyright: ignore[reportPrivateUsage]
)
from ..interfaces.identity import Identity
from .interfaces.identity import AsyncIdentityResolver
from .program import run_program_async

if sys.version_info >= (3, 12):
    from typing import TypeVar
else:
    from typing_extensions import TypeVar


__all__ = ["AsyncCachingIdentityResolver", "AsyncChainedIdentityResolver"]

_I = TypeVar("_I", bound=Identity, infer_variance=True)
_IP = TypeVar("_IP", bound=Mapping[str, Any], infer_variance=True)


logger: Final = logging.getLogger(__name__)


# TODO: turn this into a decorator
class AsyncCachingIdentityResolver(AsyncIdentityResolver[_I, _IP], Generic[_I, _IP]):
    """Identity resolver that caches its identity until it expires."""

    def __init__(self) -> None:
        self._cached: _I | None = None

    async def get_identity(self, *, properties: _IP) -> _I:
        return await run_program_async(
            _cached_identity(self, lambda: self._get_identity(properties=properties))  # pyright: ignore[reportPrivateUsage]
        )

    async def invalidate(self) -> None:
        """Discard the cached identity so the next resolution re-reads its source."""
        self._cached = None

    async def _get_identity(self, *, properties: _IP) -> _I:
        raise NotImplementedError


class AsyncChainedIdentityResolver(
    AsyncCachingIdentityResolver[_I, _IP], Generic[_I, _IP]
):
    """Attempts to resolve an identity by checking a sequence of sub-resolvers.

    If a nested resolver raises a :py:class:`SmithyIdentityError`, the next
    resolver in the chain will be attempted.
    """

    def __init__(self, resolvers: Sequence[AsyncIdentityResolver[_I, _IP]]) -> None:
        """Construct a AsyncChainedIdentityResolver.

        :param resolvers: The sequence of resolvers to resolve identity from.
        """
        super().__init__()
        self._resolvers = resolvers

    async def invalidate(self) -> None:
        """Discard this chain's cached identity and invalidate every sub-resolver."""
        await super().invalidate()
        await run_program_async(_invalidate_all(self._resolvers))  # pyright: ignore[reportPrivateUsage]

    async def _get_identity(self, *, properties: _IP) -> _I:
        return await run_program_async(
            _resolve_from_chain(self._resolvers, properties)  # pyright: ignore[reportPrivateUsage]
        )
