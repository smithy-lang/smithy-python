#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, TypedDict

from smithy_core.aio.interfaces.identity import IdentityResolver
from smithy_core.interfaces.identity import Identity


@dataclass(kw_only=True)
class AWSCredentialsIdentity(Identity):
    access_key_id: str
    """A unique identifier for an AWS user or role."""

    secret_access_key: str
    """A secret key used in conjunction with the access key ID to authenticate
    programmatic access to AWS services."""

    session_token: str | None = None
    """A temporary token used to specify the current session for the supplied
    credentials."""

    expiration: datetime | None = None
    """The expiration time of the identity.

    If time zone is provided, it is updated to UTC. The value must always be in UTC.
    """

    account_id: str | None = None
    """The AWS account's ID."""


class AWSIdentityProperties(TypedDict, total=False):
    access_key_id: str | None
    secret_access_key: str | None
    session_token: str | None


type AWSCredentialsResolver = IdentityResolver[
    AWSCredentialsIdentity, AWSIdentityProperties
]


class AWSIdentityConfig(Protocol):
    aws_access_key_id: str | None
    aws_secret_access_key: str | None
    aws_session_token: str | None = None
