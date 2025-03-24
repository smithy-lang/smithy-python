#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from smithy_core.aio.interfaces.identity import IdentityResolver
from smithy_core.interfaces.identity import IdentityProperties

from smithy_aws_core.identity import AWSCredentialsIdentity


class StaticCredentialsResolver(
    IdentityResolver[AWSCredentialsIdentity, IdentityProperties]
):
    """Resolve Static AWS Credentials."""

    def __init__(self, *, credentials: AWSCredentialsIdentity) -> None:
        self._credentials = credentials

    async def get_identity(
        self, *, identity_properties: IdentityProperties
    ) -> AWSCredentialsIdentity:
        return self._credentials
