#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any, Protocol, runtime_checkable

from ..utils import ensure_utc


@runtime_checkable
class Identity(Protocol):
    """An entity available to the client representing who the user is."""

    expiration: datetime | None = None
    """The expiration time of the identity.

    If time zone is provided, it is updated to UTC. The value must always be in UTC.
    """

    def __post_init__(self) -> None:
        if self.expiration is not None:
            self.expiration = ensure_utc(self.expiration)

    @property
    def is_expired(self) -> bool:
        """Whether the identity is expired."""
        if self.expiration is None:
            return False
        return datetime.now(tz=UTC) >= self.expiration


class IdentityResolver[I: Identity, IP: Mapping[str, Any]](Protocol):
    """Synchronously loads a user's ``Identity`` from a given source.

    The canonical (synchronous) counterpart to
    :py:class:`smithy_core.aio.interfaces.identity.IdentityResolver`.
    """

    def get_identity(self, *, properties: IP) -> I:
        """Load the user's identity from this resolver.

        :param properties: Properties used to help determine the identity to return.
        """
        ...

    def invalidate(self) -> None:
        """Discard any cached identity so the next resolution re-reads its source.

        Defaults to a no-op for non-refreshable resolvers.
        """
        return None
