# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
from datetime import datetime

from .interfaces.identity import AWSCredentialsIdentity


@dataclass(kw_only=True)
class AWSCredentialIdentity(AWSCredentialsIdentity):
    access_key_id: str
    secret_access_key: str
    session_token: str | None = None
    expiration: datetime | None = None
