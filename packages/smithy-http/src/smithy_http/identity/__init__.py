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
