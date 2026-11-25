#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from typing import Any, Protocol

from smithy_core.aio.interfaces.auth import AsyncAuthScheme
from smithy_core.aio.interfaces.identity import AsyncIdentityResolver
from smithy_core.interfaces import TypedProperties as _TypedProperties
from smithy_core.types import PropertyKey

from smithy_http.interfaces import HTTPRequest

from ...auth.bearer import (
    _BearerAuthSchemeBase,  # pyright: ignore[reportPrivateUsage]
)
from ...identity import TokenIdentity, TokenIdentityProperties

__all__ = [
    "TOKEN_RESOLVER_CONFIG",
    "AsyncBearerAuthScheme",
    "AsyncTokenResolverConfig",
]


class AsyncTokenResolverConfig(Protocol):
    """A config bearing bearer token properties."""

    token: str | None
    """An explicit bearer token.

    If not set, it MAY be retrieved from elsewhere by the resolver.
    """

    token_identity_resolver: (
        AsyncIdentityResolver[TokenIdentity, TokenIdentityProperties] | None
    )
    """A bearer token identity resolver.

    The default implementation only returns the explicitly configured token.
    """


TOKEN_RESOLVER_CONFIG = PropertyKey(key="config", value_type=AsyncTokenResolverConfig)
"""A context property bearing a bearer token config."""


class AsyncBearerAuthScheme(
    _BearerAuthSchemeBase,
    AsyncAuthScheme[HTTPRequest, TokenIdentity, TokenIdentityProperties, Any],
):
    """An auth scheme containing necessary data and tools for bearer token auth."""

    def identity_resolver(
        self, *, context: _TypedProperties
    ) -> AsyncIdentityResolver[TokenIdentity, TokenIdentityProperties]:
        return super().identity_resolver(context=context)
