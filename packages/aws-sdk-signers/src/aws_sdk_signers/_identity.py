# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
from datetime import UTC, datetime

from .interfaces.identity import Identity


@dataclass(kw_only=True)
class AWSCredentialIdentity(Identity):
    access_key_id: str
    secret_access_key: str
    session_token: str | None = None
    expiration: datetime | None = None

    @property
    def is_expired(self) -> bool:
        """Whether the identity is expired."""
        if self.expiration is None:
            return False
        return self.expiration < datetime.now(UTC)
