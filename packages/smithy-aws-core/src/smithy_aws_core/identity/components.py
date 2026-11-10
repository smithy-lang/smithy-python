#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol

from aws_sdk_signers.interfaces.identity import AWSIdentityProperties
from smithy_core.interfaces.identity import Identity, IdentityResolver

__all__ = [
    "AWSCredentialsIdentity",
    "AWSCredentialsResolver",
    "AWSIdentityConfig",
]


@dataclass(kw_only=True)
class AWSCredentialsIdentity(Identity):
    """AWS credentials used to sign requests."""

    access_key_id: str
    """A unique identifier for an AWS user or role."""

    secret_access_key: str = field(repr=False)
    """A secret key used in conjunction with the access key ID to authenticate
    programmatic access to AWS services."""

    session_token: str | None = field(default=None, repr=False)
    """A temporary token used to specify the current session for the supplied
    credentials."""

    expiration: datetime | None = None
    """The expiration time of the identity.

    If time zone is provided, it is updated to UTC. The value must always be in UTC.
    """

    account_id: str | None = None
    """The AWS account's ID."""


type AWSCredentialsResolver = IdentityResolver[
    AWSCredentialsIdentity, AWSIdentityProperties
]


class AWSIdentityConfig(Protocol):
    """Client config that may carry explicit AWS credentials."""

    aws_access_key_id: str | None
    aws_secret_access_key: str | None
    aws_session_token: str | None = None
