#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import os

from smithy_core.aio.interfaces.identity import IdentityResolver
from smithy_core.exceptions import SmithyIdentityException
from smithy_core.interfaces.identity import IdentityProperties

from ..identity import AWSCredentialsIdentity


class EnvironmentCredentialsResolver(
    IdentityResolver[AWSCredentialsIdentity, IdentityProperties]
):
    """Resolves AWS Credentials from system environment variables."""

    def __init__(self):
        self._credentials = None

    async def get_identity(
        self, *, identity_properties: IdentityProperties
    ) -> AWSCredentialsIdentity:
        if self._credentials is not None:
            return self._credentials

        access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        session_token = os.getenv("AWS_SESSION_TOKEN")
        account_id = os.getenv("AWS_ACCOUNT_ID")

        if access_key_id is None or secret_access_key is None:
            raise SmithyIdentityException(
                "AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are required"
            )

        self._credentials = AWSCredentialsIdentity(
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
            session_token=session_token,
            account_id=account_id,
        )

        return self._credentials
