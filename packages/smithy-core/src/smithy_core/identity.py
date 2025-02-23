#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from datetime import datetime, timezone

from .interfaces import identity as identity_interface
from .utils import ensure_utc


class Identity(identity_interface.Identity):
    """An entity available to the client representing who the user is."""

    def __init__(
        self,
        *,
        expiration: datetime | None = None,
    ) -> None:
        """Initialize an identity.

        :param expiration: The expiration time of the identity. If time zone is
            provided, it is updated to UTC. The value must always be in UTC.
        """
        if expiration is not None:
            expiration = ensure_utc(expiration)
        self.expiration: datetime | None = expiration

    @property
    def is_expired(self) -> bool:
        """Whether the identity is expired."""
        if self.expiration is None:
            return False
        return datetime.now(tz=timezone.utc) >= self.expiration
