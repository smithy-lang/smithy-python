#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass
from datetime import datetime
from typing import TypedDict

from smithy_core.interfaces.identity import Identity


@dataclass(kw_only=True)
class APIKeyIdentity(Identity):
    """The identity for auth that uses an api key."""

    api_key: str
    """The API Key to add to requests."""

    expiration: datetime | None = None


class APIKeyIdentityProperties(TypedDict, total=False):
    api_key: str


class APIKeyIdentityResolver:
    """Loads the API key identity from the configuration.

    Placeholder for the synchronous resolver; populated alongside the sync client
    implementation.
    """

    # TODO(sync-api): implement alongside the sync client
