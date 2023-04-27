from dataclasses import dataclass
from enum import Enum
from typing import NotRequired, Protocol, TypedDict

from ..exceptions import SmithyIdentityException
from ..interfaces.auth import HTTPAuthScheme, HTTPSigner
from ..interfaces.http import HTTPRequest
from ..interfaces.identity import IdentityProperties, IdentityResolver
from . import URI, Field
from .identity import Identity


class ApiKeyIdentity(Identity):
    """The identity for auth that uses an api key."""

    def __init__(self, *, api_key: str) -> None:
        super().__init__(expiration=None)
        self.api_key = api_key


class ApiKeyIdentityResolver(IdentityResolver[ApiKeyIdentity, IdentityProperties]):
    """Loads the api key identity from the configuration."""

    def __init__(self, *, api_key: str | ApiKeyIdentity) -> None:
        """
        :param api_key: The API key to authenticate with.
        """
        match api_key:
            case str():
                self._identity = ApiKeyIdentity(api_key=api_key)
            case ApiKeyIdentity():
                self._identity = api_key

    async def get_identity(
        self, *, identity_properties: IdentityProperties
    ) -> ApiKeyIdentity:
        """Load the user's api key identity from this resolver.

        :param identity_properties: Properties used to help determine the
        identity to return.
        :returns: The api key identity.
        """
        return self._identity


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
    api_key_identity_resolver: IdentityResolver[
        ApiKeyIdentity, IdentityProperties
    ] | None


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
