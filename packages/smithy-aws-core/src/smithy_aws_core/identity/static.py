#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from smithy_core.aio.interfaces.identity import IdentityResolver
from smithy_core.exceptions import SmithyIdentityError

from .components import AWSCredentialsIdentity, AWSIdentityProperties


class StaticCredentialsResolver(
    IdentityResolver[AWSCredentialsIdentity, AWSIdentityProperties]
):
    """Resolves static AWS credentials from a fixed identity or request properties."""

    def __init__(self, identity: AWSCredentialsIdentity | None = None) -> None:
        """Initialize the resolver with optional fixed credentials."""
        self._identity = identity

    async def get_identity(
        self, *, properties: AWSIdentityProperties
    ) -> AWSCredentialsIdentity:
        """Resolve credentials from the fixed identity or request properties."""
        if self._identity is not None:
            return self._identity

        access_key_id = properties.get("access_key_id")
        secret_access_key = properties.get("secret_access_key")
        if access_key_id is not None and secret_access_key is not None:
            return AWSCredentialsIdentity(
                access_key_id=access_key_id,
                secret_access_key=secret_access_key,
                session_token=properties.get("session_token"),
            )
        raise SmithyIdentityError(
            "Attempted to resolve AWS credentials from config, but credentials weren't configured."
        )
