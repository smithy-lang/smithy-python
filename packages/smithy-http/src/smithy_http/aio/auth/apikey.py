#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass
from enum import Enum
from typing import NotRequired, Protocol, TypedDict

from smithy_core import URI
from smithy_core.aio.interfaces.identity import IdentityResolver
from smithy_core.exceptions import SmithyIdentityException
from smithy_core.interfaces.identity import IdentityProperties

from ... import Field
from ..identity.apikey import ApiKeyIdentity
from ..interfaces import HTTPRequest
from ..interfaces.auth import HTTPAuthScheme, HTTPSigner


class ApiKeyLocation(Enum):
    """The locations that the api key could be placed in the signed request."""

    HEADER = "header"
    QUERY = "query"


class ApiKeySigningProperties(TypedDict):
    """The properties needed to sign a request with api key auth.

    seealso:: The `Smithy API Key auth trait docs <https://smithy.io/2.0/spec/authentication-traits.html#smithy-api-httpapikeyauth-trait>`_
    , which have more details on these properties, including examples.
    """

    name: str
    """The name of the HTTP header or query string parameter containing the key."""

    scheme: NotRequired[str]
    """The :rfc:`9110#section-11.4` scheme to prefix a header value with."""

    location: ApiKeyLocation
    """Where the key is serialized."""


class ApiKeyConfig(Protocol):
    api_key_identity_resolver: (
        IdentityResolver[ApiKeyIdentity, IdentityProperties] | None
    )


@dataclass(init=False)
class ApiKeyAuthScheme(
    HTTPAuthScheme[
        ApiKeyIdentity, ApiKeyConfig, IdentityProperties, ApiKeySigningProperties
    ]
):
    """An auth scheme containing necessary data and tools for api key auth."""

    scheme_id: str
    signer: HTTPSigner[ApiKeyIdentity, ApiKeySigningProperties]

    def __init__(
        self,
        *,
        signer: HTTPSigner[ApiKeyIdentity, ApiKeySigningProperties] | None = None,
    ) -> None:
        """Constructor.

        :param identity_resolver: The identity resolver to extract the api key identity.
        :param signer: The signer used to sign the request.
        """
        self.scheme_id = "smithy.api#httpApiKeyAuth"
        self.signer = signer or ApiKeySigner()

    def identity_resolver(
        self, *, config: ApiKeyConfig
    ) -> IdentityResolver[ApiKeyIdentity, IdentityProperties]:
        if not config.api_key_identity_resolver:
            raise SmithyIdentityException(
                "Attempted to use API key auth, but api_key_identity_resolver was not"
                "set on the config."
            )
        return config.api_key_identity_resolver


class ApiKeySigner(HTTPSigner[ApiKeyIdentity, ApiKeySigningProperties]):
    """A signer that signs http requests with an api key."""

    async def sign(
        self,
        *,
        http_request: HTTPRequest,
        identity: ApiKeyIdentity,
        signing_properties: ApiKeySigningProperties,
    ) -> HTTPRequest:
        match signing_properties["location"]:
            case ApiKeyLocation.QUERY:
                query = http_request.destination.query or ""
                if query:
                    query += "&"
                query += f"{signing_properties['name']}={identity.api_key}"
                http_request.destination = URI(
                    scheme=http_request.destination.scheme,
                    username=http_request.destination.username,
                    password=http_request.destination.password,
                    host=http_request.destination.host,
                    port=http_request.destination.port,
                    path=http_request.destination.password,
                    query=query,
                    fragment=http_request.destination.fragment,
                )
            case ApiKeyLocation.HEADER:
                value = identity.api_key
                if "scheme" in signing_properties and signing_properties["scheme"]:
                    value = f"{signing_properties['scheme']} {value}"
                http_request.fields.set_field(
                    Field(name=signing_properties["name"], values=[value])
                )

        return http_request
