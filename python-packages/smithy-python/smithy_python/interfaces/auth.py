# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
# http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

from dataclasses import dataclass
from typing import Any, Protocol, TypedDict, TypeVar

from .http import HTTPRequest
from .identity import IdentityResolver, IdentityType, IdentityType_contra


class SigningProperties(TypedDict):
    """Additional properties loaded to modify the signing process."""

    ...


SigningPropertiesType = TypeVar("SigningPropertiesType", bound=SigningProperties)
SigningPropertiesType_contra = TypeVar(
    "SigningPropertiesType_contra", bound=SigningProperties, contravariant=True
)


class HTTPSigner(Protocol[IdentityType_contra, SigningPropertiesType_contra]):
    """An interface for generating a signed HTTP request."""

    async def sign(
        self,
        *,
        http_request: HTTPRequest,
        identity: IdentityType_contra,
        signing_properties: SigningPropertiesType_contra,
    ) -> HTTPRequest:
        """Sign the provided HTTP request, and generate a new HTTP request with the
        signature added.

        :param http_request: The HTTP request to sign.

        :param identity: The signing identity.

        :param signing_properties: Additional properties loaded to modify the
        signing process.
        """
        ...


@dataclass(kw_only=True)
class HTTPAuthScheme(Protocol[IdentityType, SigningPropertiesType]):
    """Represents a way a service will authenticate the user's identity."""

    # A unique identifier for the authentication scheme.
    scheme_id: str

    # An API that can be queried to resolve an identity.
    identity_resolver: IdentityResolver

    # An API that can be used to sign HTTP requests.
    signer: HTTPSigner[IdentityType, SigningPropertiesType]


@dataclass(kw_only=True)
class HTTPAuthOption:
    """Auth scheme used for signing and identity resolution."""

    # The ID of the scheme to use. This string matches the one returned by
    # HttpAuthScheme.scheme_id
    scheme_id: str

    # Parameters to pass to IdentityResolver.get_identity.
    identity_properties: dict[str, Any]

    # Parameters to pass to HttpSigner.sign.
    signer_properties: dict[str, Any]


@dataclass(kw_only=True)
class AuthSchemeParameters:
    """The input to the auth scheme resolver.

    A code-generated interface for passing in the data required for determining the
    authentication scheme. By default, this only includes the operation name.
    """

    # The service operation being invoked by the client.
    operation: str


class AuthSchemeResolver(Protocol):
    """Determines which authentication scheme to use for a given service."""

    def resolve_auth_scheme(
        self, *, auth_parameters: AuthSchemeParameters
    ) -> list[HTTPAuthOption]:
        """Resolve an ordered list of applicable auth schemes.

        :param auth_parameters: The parameters required for determining which
        authentication schemes to potentially use.
        """
        ...
