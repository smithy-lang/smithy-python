#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any, Protocol, runtime_checkable

from ..utils import ensure_utc

__all__ = ["Identity", "IdentityResolver"]


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
    """Loads a user's :py:class:`Identity` from a given source.

    Placeholder for the synchronous identity resolver; populated alongside the sync
    client implementation.
    """

    def get_identity(self, *, properties: IP) -> I:
        # TODO(sync-api): implement alongside the sync client
        ...

    def invalidate(self) -> None:
        # TODO(sync-api): implement alongside the sync client
        ...
