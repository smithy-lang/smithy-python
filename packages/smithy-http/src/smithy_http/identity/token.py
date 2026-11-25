#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from smithy_core.exceptions import SmithyIdentityError
from smithy_core.interfaces.identity import IdentityResolver

from . import TokenIdentity, TokenIdentityProperties

__all__ = [
    "StaticTokenResolver",
    "TokenIdentity",
    "TokenIdentityProperties",
]


class StaticTokenResolver(IdentityResolver[TokenIdentity, TokenIdentityProperties]):
    """Resolves a bearer token from a fixed identity or request properties."""

    def __init__(self, identity: TokenIdentity | None = None) -> None:
        self._identity = identity

    def get_identity(self, *, properties: TokenIdentityProperties) -> TokenIdentity:
        if self._identity is not None:
            return self._identity

        if (token := properties.get("token")) is not None:
            return TokenIdentity(token=token)
        raise SmithyIdentityError(
            "Attempted to use bearer token auth, but no token was configured."
        )
