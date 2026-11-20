#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass, field
from datetime import datetime
from typing import TypedDict

from smithy_core.interfaces.identity import Identity


@dataclass(kw_only=True)
class APIKeyIdentity(Identity):
    """The identity for auth that uses an api key."""

    api_key: str = field(repr=False)
    """The API Key to add to requests."""

    expiration: datetime | None = None


class APIKeyIdentityProperties(TypedDict, total=False):
    """Identity properties that may carry an explicit API key."""

    api_key: str


@dataclass(kw_only=True)
class TokenIdentity(Identity):
    """The identity for auth that uses a bearer token."""

    token: str = field(repr=False)
    """The token to add to requests.

    It is opaque to the client: never introspected, decoded or validated.
    """

    expiration: datetime | None = None


class TokenIdentityProperties(TypedDict, total=False):
    """Identity properties that may carry an explicit token."""

    token: str
