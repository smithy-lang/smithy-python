#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from smithy_core.aio.interfaces.identity import (
    IdentityResolver as AsyncIdentityResolver,
)
from smithy_core.exceptions import SmithyIdentityError
from smithy_core.interfaces.identity import IdentityResolver

from .components import AWSCredentialsIdentity, AWSIdentityProperties


def _resolve_static(
    identity: AWSCredentialsIdentity | None, properties: AWSIdentityProperties
) -> AWSCredentialsIdentity:
    """Resolve credentials from a fixed identity or request properties (no I/O)."""
    if identity is not None:
        return identity

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


class StaticCredentialsResolver(
    IdentityResolver[AWSCredentialsIdentity, AWSIdentityProperties]
):
    """Resolves static AWS credentials synchronously (no I/O)."""

    def __init__(self, identity: AWSCredentialsIdentity | None = None) -> None:
        self._identity = identity

    def get_identity(
        self, *, properties: AWSIdentityProperties
    ) -> AWSCredentialsIdentity:
        return _resolve_static(self._identity, properties)


class AsyncStaticCredentialsResolver(
    AsyncIdentityResolver[AWSCredentialsIdentity, AWSIdentityProperties]
):
    """Async view over :py:class:`StaticCredentialsResolver`.

    Static resolution does no I/O, so the async form delegates to the sync body.
    """

    def __init__(self, identity: AWSCredentialsIdentity | None = None) -> None:
        self._identity = identity

    async def get_identity(
        self, *, properties: AWSIdentityProperties
    ) -> AWSCredentialsIdentity:
        return _resolve_static(self._identity, properties)

    def invalidate(self) -> None:
        return None
