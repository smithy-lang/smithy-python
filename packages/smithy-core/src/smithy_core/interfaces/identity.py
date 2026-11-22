#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any, Protocol, TypeVar, runtime_checkable

from ..utils import ensure_utc

__all__ = ["Identity", "IdentityResolver"]

_I_co = TypeVar("_I_co", bound="Identity", covariant=True)
_IP_contra = TypeVar("_IP_contra", bound=Mapping[str, Any], contravariant=True)


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


class IdentityResolver(Protocol[_I_co, _IP_contra]):
    """Loads a user's :py:class:`Identity` from a given source."""

    def get_identity(self, *, properties: _IP_contra) -> _I_co:
        """Load the user's identity from this resolver.

        :param properties: Properties used to help determine the identity to return.
        """
        ...

    def invalidate(self) -> None:
        """Discard any cached identity so the next resolution re-reads its source.

        Defaults to a no-op for non-refreshable resolvers.
        """
        return None
