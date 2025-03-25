#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import logging
from collections.abc import Mapping, Sequence
from typing import Any, Final

from ..exceptions import SmithyIdentityError
from ..interfaces.identity import Identity
from .interfaces.identity import IdentityResolver

logger: Final = logging.getLogger(__name__)


# TODO: turn this into a decorator
class CachingIdentityResolver[I: Identity, IP: Mapping[str, Any]](
    IdentityResolver[I, IP]
):
    def __init__(self) -> None:
        self._cached: I | None = None

    async def get_identity(self, *, properties: IP) -> I:
        if self._cached is None or self._cached.is_expired:
            self._cached = await self._get_identity(properties=properties)
        return self._cached

    async def _get_identity(self, *, properties: IP) -> I:
        raise NotImplementedError


class ChainedIdentityResolver[I: Identity, IP: Mapping[str, Any]](
    CachingIdentityResolver[I, IP]
):
    """Attempts to resolve an identity by checking a sequence of sub-resolvers.

    If a nested resolver raises a :py:class:`SmithyIdentityError`, the next
    resolver in the chain will be attempted.
    """

    def __init__(self, resolvers: Sequence[IdentityResolver[I, IP]]) -> None:
        """Construct a ChainedIdentityResolver.

        :param resolvers: The sequence of resolvers to resolve identity from.
        """
        super().__init__()
        self._resolvers = resolvers

    async def _get_identity(self, *, properties: IP) -> I:
        logger.debug("Attempting to resolve identity from resolver chain.")
        for resolver in self._resolvers:
            try:
                logger.debug("Attempting to resolve identity from %s.", type(resolver))
                return await resolver.get_identity(properties=properties)
            except SmithyIdentityError as e:
                logger.debug(
                    "Failed to resolve identity from %s: %s", type(resolver), e
                )

        raise SmithyIdentityError("Failed to resolve identity from resolver chain.")
