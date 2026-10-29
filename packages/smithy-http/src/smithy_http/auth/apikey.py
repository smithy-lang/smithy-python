# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from typing import Any, Protocol, Self

from smithy_core import URI
from smithy_core.exceptions import SmithyIdentityError
from smithy_core.interfaces import TypedProperties as _TypedProperties
from smithy_core.interfaces.auth import AuthScheme, Signer
from smithy_core.interfaces.identity import IdentityResolver
from smithy_core.traits import APIKeyLocation, HTTPAPIKeyAuthTrait

from .. import Field
from ..aio.interfaces import HTTPRequest
from ..identity import APIKeyIdentity, APIKeyIdentityProperties

__all__ = ["APIKeyAuthScheme", "APIKeyResolverConfig", "APIKeySigner"]


class APIKeyResolverConfig(Protocol):
    """A config bearing API key properties for a synchronous client."""

    api_key: str | None
    """An explicit API key.

    If not set, it MAY be retrieved from elsewhere by the resolver.
    """

    api_key_identity_resolver: (
        IdentityResolver[APIKeyIdentity, APIKeyIdentityProperties] | None
    )
    """An API key identity resolver."""


class APIKeySigner(Signer[HTTPRequest, APIKeyIdentity, Any]):
    """A signer that signs http requests with an api key."""

    def __init__(
        self, *, name: str, location: APIKeyLocation, scheme: str | None = None
    ) -> None:
        self._name = name
        self._location = location
        self._scheme = scheme

    def sign(
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


class _APIKeyAuthSchemeBase:
    """API key auth scheme logic shared by the sync and async schemes."""

    scheme_id = HTTPAPIKeyAuthTrait.id

    def __init__(
        self, *, name: str, location: APIKeyLocation, scheme: str | None = None
    ) -> None:
        self._name = name
        self._location = location
        self._scheme = scheme

    def identity_properties(
        self, *, context: _TypedProperties
    ) -> APIKeyIdentityProperties:
        config = context.get("config")
        if config is not None and config.api_key is not None:
            return {"api_key": config.api_key}
        return {}

    def identity_resolver(self, *, context: _TypedProperties) -> Any:
        config = context.get("config")
        if config is None or config.api_key_identity_resolver is None:
            raise SmithyIdentityError(
                "Attempted to use API key auth, but api_key_identity_resolver was not "
                "set on the config."
            )
        return config.api_key_identity_resolver

    def signer_properties(self, *, context: _TypedProperties) -> Any:
        return {}

    @classmethod
    def from_trait(cls, trait: HTTPAPIKeyAuthTrait, /) -> Self:
        return cls(name=trait.name, location=trait.location, scheme=trait.scheme)


class APIKeyAuthScheme(
    _APIKeyAuthSchemeBase,
    AuthScheme[HTTPRequest, APIKeyIdentity, APIKeyIdentityProperties, Any],
):
    """An auth scheme containing necessary data and tools for api key auth."""

    def identity_resolver(
        self, *, context: _TypedProperties
    ) -> IdentityResolver[APIKeyIdentity, APIKeyIdentityProperties]:
        return super().identity_resolver(context=context)

    def signer(self) -> APIKeySigner:
        return APIKeySigner(
            name=self._name, location=self._location, scheme=self._scheme
        )
