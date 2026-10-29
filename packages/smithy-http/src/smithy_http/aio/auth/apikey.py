#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from typing import Any, Protocol

from smithy_core.aio.interfaces.auth import AsyncAuthScheme, AsyncSigner
from smithy_core.aio.interfaces.identity import AsyncIdentityResolver
from smithy_core.interfaces import TypedProperties as _TypedProperties
from smithy_core.traits import APIKeyLocation
from smithy_core.types import PropertyKey

from ...auth.apikey import (
    APIKeySigner,
    _APIKeyAuthSchemeBase,  # pyright: ignore[reportPrivateUsage]
)
from ...identity import APIKeyIdentity, APIKeyIdentityProperties
from ..interfaces import HTTPRequest

__all__ = [
    "API_KEY_RESOLVER_CONFIG",
    "APIKeyResolverConfig",
    "AsyncAPIKeyAuthScheme",
    "AsyncAPIKeySigner",
]


class APIKeyResolverConfig(Protocol):
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


API_KEY_RESOLVER_CONFIG = PropertyKey(key="config", value_type=APIKeyResolverConfig)
"""A context property bearing an API key config."""


class AsyncAPIKeySigner(AsyncSigner[HTTPRequest, APIKeyIdentity, Any]):
    """A signer that signs http requests with an api key."""

    def __init__(
        self, *, name: str, location: APIKeyLocation, scheme: str | None = None
    ) -> None:
        self._sync = APIKeySigner(name=name, location=location, scheme=scheme)

    async def sign(
        self,
        *,
        request: HTTPRequest,
        identity: APIKeyIdentity,
        properties: Any,
    ) -> HTTPRequest:
        return self._sync.sign(
            request=request, identity=identity, properties=properties
        )


class AsyncAPIKeyAuthScheme(
    _APIKeyAuthSchemeBase,
    AsyncAuthScheme[HTTPRequest, APIKeyIdentity, APIKeyIdentityProperties, Any],
):
    """An auth scheme containing necessary data and tools for api key auth."""

    _signer: AsyncAPIKeySigner

    def __init__(
        self, *, name: str, location: APIKeyLocation, scheme: str | None = None
    ) -> None:
        super().__init__(name=name, location=location, scheme=scheme)
        self._signer = AsyncAPIKeySigner(name=name, location=location, scheme=scheme)

    def identity_resolver(
        self, *, context: _TypedProperties
    ) -> AsyncIdentityResolver[APIKeyIdentity, APIKeyIdentityProperties]:
        return super().identity_resolver(context=context)

    def signer(self) -> AsyncSigner[HTTPRequest, APIKeyIdentity, Any]:
        return self._signer
