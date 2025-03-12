# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable


class Identity(Protocol):
    """An entity available to the client representing who the user is."""

    # The expiration time of the identity. If time zone is provided,
    # it is updated to UTC. The value must always be in UTC.
    expiration: datetime | None = None

    @property
    def is_expired(self) -> bool:
        """Whether the identity is expired."""
        ...


@runtime_checkable
class AWSCredentialsIdentity(Protocol):
    """AWS Credentials Identity."""

    # The access key ID.
    access_key_id: str

    # The secret access key.
    secret_access_key: str

    # The session token.
    session_token: str | None

    expiration: datetime | None = None

    @property
    def is_expired(self) -> bool:
        """Whether the identity is expired."""
        ...
