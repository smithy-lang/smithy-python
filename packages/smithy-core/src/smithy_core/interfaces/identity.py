#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from datetime import UTC, datetime
from typing import Protocol, runtime_checkable

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
