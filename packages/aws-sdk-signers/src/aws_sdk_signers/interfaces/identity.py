# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol, runtime_checkable


@runtime_checkable
class Identity(Protocol):
    """An entity available to the client representing who the user is."""

    expiration: datetime | None = None
    """The expiration time of the identity.

    If time zone is provided, it is updated to UTC. The value must always be in UTC.
    """

    @property
    def is_expired(self) -> bool:
        """Whether the identity is expired."""
        if self.expiration is None:
            return False
        return datetime.now(tz=UTC) >= self.expiration


@runtime_checkable
class AWSCredentialsIdentity(Identity, Protocol):
    """AWS Credentials Identity."""

    access_key_id: str
    """A unique identifier for an AWS user or role."""

    secret_access_key: str
    """A secret key used in conjunction with the access key ID to authenticate
    programmatic access to AWS services."""

    session_token: str | None = None
    """A temporary token used to specify the current session for the supplied
    credentials."""
