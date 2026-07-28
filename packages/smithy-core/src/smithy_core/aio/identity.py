#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import logging
from collections.abc import Mapping
from typing import Any, Final

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

    async def invalidate(self) -> None:
        """Discard the cached identity so the next resolution re-reads its source."""
        self._cached = None
