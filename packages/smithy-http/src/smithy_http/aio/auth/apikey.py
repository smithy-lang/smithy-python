#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from typing import Any, Protocol

from smithy_core.aio.interfaces.auth import AsyncAuthScheme
from smithy_core.aio.interfaces.identity import AsyncIdentityResolver
from smithy_core.interfaces import TypedProperties as _TypedProperties
from smithy_core.types import PropertyKey

from smithy_http.interfaces import HTTPRequest

from ...auth.apikey import (
    _APIKeyAuthSchemeBase,  # pyright: ignore[reportPrivateUsage]
)
from ...identity import APIKeyIdentity, APIKeyIdentityProperties

__all__ = [
    "API_KEY_RESOLVER_CONFIG",
    "AsyncAPIKeyAuthScheme",
    "AsyncAPIKeyResolverConfig",
]


class AsyncAPIKeyResolverConfig(Protocol):
    """A config bearing API key properties."""

    api_key: str | None
    """An explicit API key.

    If not set, it MAY be retrieved from elsewhere by the resolver.
    """

    api_key_identity_resolver: (
        AsyncIdentityResolver[APIKeyIdentity, APIKeyIdentityProperties] | None
    )
    """An API key identity resolver.

    The default implementation only checks the explicitly configured key.
    """


API_KEY_RESOLVER_CONFIG = PropertyKey(
    key="config", value_type=AsyncAPIKeyResolverConfig
)
"""A context property bearing an API key config."""


class AsyncAPIKeyAuthScheme(
    _APIKeyAuthSchemeBase,
    AsyncAuthScheme[HTTPRequest, APIKeyIdentity, APIKeyIdentityProperties, Any],
):
    """An auth scheme containing necessary data and tools for api key auth."""

    def identity_resolver(
        self, *, context: _TypedProperties
    ) -> AsyncIdentityResolver[APIKeyIdentity, APIKeyIdentityProperties]:
        return super().identity_resolver(context=context)
