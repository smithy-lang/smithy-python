# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from typing import Any, Protocol, Self

from smithy_core.exceptions import SmithyIdentityError
from smithy_core.interfaces import TypedProperties as _TypedProperties
from smithy_core.interfaces.auth import AuthScheme, Signer
from smithy_core.interfaces.identity import IdentityResolver
from smithy_core.shapes import ShapeID
from smithy_core.traits import HTTPBearerAuthTrait

from smithy_http.interfaces import HTTPRequest

from .. import Field
from ..exceptions import SmithyHTTPError
from ..identity import TokenIdentity, TokenIdentityProperties

__all__ = ["BearerAuthScheme", "BearerSigner", "TokenResolverConfig"]


class TokenResolverConfig(Protocol):
    """A config bearing bearer token properties for a synchronous client."""

    token: str | None
    """An explicit bearer token.

    If not set, it MAY be retrieved from elsewhere by the resolver.
    """

    token_identity_resolver: (
        IdentityResolver[TokenIdentity, TokenIdentityProperties] | None
    )
    """A bearer token identity resolver."""


class BearerSigner(Signer[HTTPRequest, TokenIdentity, Any]):
    """A signer that signs http requests with a bearer token.

    The token is sent in the ``Authorization`` header as defined in RFC 6750 §2.1,
    replacing any value already present.
    """

    def sign(
        self,
        *,
        request: HTTPRequest,
        identity: TokenIdentity,
        properties: Any,
    ) -> HTTPRequest:
        """Add the bearer token to the request's ``Authorization`` header.

        :raises SmithyIdentityError: If the identity's token is empty.
        :raises SmithyHTTPError: If the request is not bound for an ``https`` endpoint.
            RFC 6750 §5.2 requires TLS for bearer tokens.
        """
        if not identity.token:
            raise SmithyIdentityError("Bearer token auth requires a non-empty token.")
        if request.destination.scheme.lower() != "https":
            raise SmithyHTTPError(
                "Bearer token auth requires an https endpoint, but the request is "
                f"bound for {request.destination.scheme}://{request.destination.host}."
            )
        request.fields.set_field(
            Field(name="Authorization", values=[f"Bearer {identity.token}"])
        )
        return request


class _BearerAuthSchemeBase:
    """Bearer token auth scheme logic shared by the sync and async schemes."""

    scheme_id: ShapeID = HTTPBearerAuthTrait.id

    def __init__(self) -> None:
        self._signer = BearerSigner()

    def identity_properties(
        self, *, context: _TypedProperties
    ) -> TokenIdentityProperties:
        config = context.get("config")
        if config is not None and config.token is not None:
            return {"token": config.token}
        return {}

    def identity_resolver(self, *, context: _TypedProperties) -> Any:
        config = context.get("config")
        if config is None or config.token_identity_resolver is None:
            raise SmithyIdentityError(
                "Attempted to use bearer token auth, but token_identity_resolver was "
                "not set on the config."
            )
        return config.token_identity_resolver

    def signer_properties(self, *, context: _TypedProperties) -> Any:
        return {}

    def signer(self) -> BearerSigner:
        return self._signer

    @classmethod
    def from_trait(cls, trait: HTTPBearerAuthTrait, /) -> Self:
        return cls()


class BearerAuthScheme(
    _BearerAuthSchemeBase,
    AuthScheme[HTTPRequest, TokenIdentity, TokenIdentityProperties, Any],
):
    """An auth scheme containing necessary data and tools for bearer token auth."""

    def identity_resolver(
        self, *, context: _TypedProperties
    ) -> IdentityResolver[TokenIdentity, TokenIdentityProperties]:
        return super().identity_resolver(context=context)
