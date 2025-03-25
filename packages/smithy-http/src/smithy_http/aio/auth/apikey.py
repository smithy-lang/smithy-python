#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from typing import Any, Protocol, Self

from smithy_core import URI
from smithy_core.aio.interfaces.auth import AuthScheme, Signer
from smithy_core.aio.interfaces.identity import IdentityResolver
from smithy_core.exceptions import SmithyIdentityError
from smithy_core.interfaces import TypedProperties as _TypedProperties
from smithy_core.traits import APIKeyLocation, HTTPAPIKeyAuthTrait
from smithy_core.types import PropertyKey

from ... import Field
from ..identity.apikey import APIKeyIdentity, APIKeyIdentityProperties
from ..interfaces import HTTPRequest


class APIKeyResolverConfig(Protocol):
    """A config bearing API key properties."""

    api_key: str | None
    """An explicit API key.

    If not set, it MAY be retrieved from elsewhere by the resolver.
    """

    api_key_identity_resolver: (
        IdentityResolver[APIKeyIdentity, APIKeyIdentityProperties] | None
    )
    """An API key identity resolver.

    The default implementation only checks the explicitly configured key.
    """


API_KEY_RESOLVER_CONFIG = PropertyKey(key="config", value_type=APIKeyResolverConfig)
"""A context property bearing an API key config."""


class APIKeySigner(Signer[HTTPRequest, APIKeyIdentity, Any]):
    """A signer that signs http requests with an api key."""

    def __init__(
        self, *, name: str, location: APIKeyLocation, scheme: str | None = None
    ) -> None:
        self._name = name
        self._location = location
        self._scheme = scheme

    async def sign(
        self,
        *,
        request: HTTPRequest,
        identity: APIKeyIdentity,
        properties: Any,
    ) -> HTTPRequest:
        match self._location:
            case APIKeyLocation.QUERY:
                query = request.destination.query or ""
                if query:
                    query += "&"
                query += f"{self._name}={identity.api_key}"
                request.destination = URI(
                    scheme=request.destination.scheme,
                    username=request.destination.username,
                    password=request.destination.password,
                    host=request.destination.host,
                    port=request.destination.port,
                    path=request.destination.password,
                    query=query,
                    fragment=request.destination.fragment,
                )
            case APIKeyLocation.HEADER:
                value = identity.api_key
                if self._scheme is not None:
                    value = f"{self._scheme} {value}"
                request.fields.set_field(Field(name=self._name, values=[value]))

        return request


class APIKeyAuthScheme(
    AuthScheme[HTTPRequest, APIKeyIdentity, APIKeyIdentityProperties, Any]
):
    """An auth scheme containing necessary data and tools for api key auth."""

    scheme_id = HTTPAPIKeyAuthTrait.id
    _signer: APIKeySigner

    def __init__(
        self, *, name: str, location: APIKeyLocation, scheme: str | None = None
    ) -> None:
        self._signer = APIKeySigner(name=name, location=location, scheme=scheme)

    def identity_properties(
        self, *, context: _TypedProperties
    ) -> APIKeyIdentityProperties:
        config = context.get(API_KEY_RESOLVER_CONFIG)
        if config is not None and config.api_key is not None:
            return {"api_key": config.api_key}
        return {}

    def identity_resolver(
        self, *, context: _TypedProperties
    ) -> IdentityResolver[APIKeyIdentity, APIKeyIdentityProperties]:
        config = context.get(API_KEY_RESOLVER_CONFIG)
        if config is None or config.api_key_identity_resolver is None:
            raise SmithyIdentityError(
                "Attempted to use API key auth, but api_key_identity_resolver was not "
                "set on the config."
            )
        return config.api_key_identity_resolver

    def signer_properties(self, *, context: _TypedProperties) -> Any:
        return {}

    def signer(self) -> Signer[HTTPRequest, APIKeyIdentity, Any]:
        return self._signer

    @classmethod
    def from_trait(cls, trait: HTTPAPIKeyAuthTrait, /) -> Self:
        return cls(name=trait.name, location=trait.location, scheme=trait.scheme)
