# Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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
from typing import Any, Generic, Protocol, TypeVar

from smithy_python.interfaces.http import Request
from smithy_python.interfaces.identity import Identity, IdentityType


class AwsCredentialIdentity(Identity):

    access_key_id: str
    secret_key_id: str
    session_token: str | None = None


class IdentityResolver(Generic[IdentityType]):
    """Used to load a customer's `Identity` from a given source.

    Each `Identity` has one or more resolver implementations. The default resolver
    for AWS consults environment variables, IMDS, ~/.aws, etc.
    """

    async def get_identity(
        self, *, identity_properties: dict[str, Any]
    ) -> IdentityType:
        """Load the customer's identity from this resolver. Additional keyword
        arguments can be provided.

        :param identity_properties: Properties loaded from the service's
        authentication rules.

        :returns: The customer's identity.
        """
        ...


IdentityResolverType = TypeVar("IdentityResolverType", bound=IdentityResolver[Identity])


class IdentityResolverConfiguration(Protocol):
    """The identity resolvers configured in the client."""

    # TODO: Should we we use an IdentityType type or just a string delineating
    # the different identity types?
    def get_identity_resolver(
        self, identity_type: type[IdentityType]
    ) -> IdentityResolver[IdentityType]:
        """Retrieve an identity resolver for the provided identity type.

        :param identity_type: The type of identity to resolve.

        :returns: The identity resolver for the provided identity type.

        :raises `SmithyIdentityException`: If the identity type is not supported.
        """
        ...


class HttpSigner(Protocol):
    """An entity within the SDK representing a way to generate a signature for a
    request.
    """

    def sign(
        self,
        http_request: Request,
        identity: IdentityType,
        signing_properties: dict[str, Any],
    ) -> Request:
        """Sign the provided HTTP request, and generate a new HTTP request with the
        signature added.

        :param http_request: The HTTP request to sign.

        :param identity: The customer's identity.

        :param signing_properties: Additional properties loaded from the service's
        authentication rules.

        :returns: The signed HTTP request.

        :raises `SmithyIdentityException`: If the provided identity is not
        compatible with this signer.
        """
        ...


HttpSignerType = TypeVar("HttpSignerType", bound=HttpSigner)


@dataclass(kw_only=True)
class HttpAuthScheme(Generic[IdentityResolverType, HttpSignerType]):
    """Represents a way an AWS service will authenticate the customer's identity."""

    scheme_id: str
    """A unique identifier for the authentication scheme (v4, v4a, none, bearer, etc.)."""

    identity_resolver: IdentityResolverType
    """An API that can be queried to acquire the customer's identity."""

    signer: HttpSignerType
    """An API that can be used to sign HTTP requests."""


@dataclass(kw_only=True)
class HttpAuthOption:
    """The output from the auth scheme resolver. The resolver returns a list of these,
    in the order the auth scheme resolver wishes to use them.
    """

    scheme_id: str
    """The ID of the scheme to use. This string matches the one returned by
    HttpAuthScheme.scheme_id
    """

    identity_properties: dict[str, Any]
    """Parameters to pass to IdentityResolver.get_identity."""

    signer_properties: dict[str, Any]
    """Parameters to pass to HttpSigner.sign."""


@dataclass(kw_only=True)
class AuthSchemeParameters:
    """The input to the auth scheme resolver.

    A code-generated interface for passing in the data required for determining the
    authentication scheme. By default, this only includes the operation name.
    """

    operation: str
    """The service operation being invoked by the SDK user."""


AuthSchemeParametersType = TypeVar(
    "AuthSchemeParametersType", bound=AuthSchemeParameters
)


class AuthSchemeResolver(Generic[AuthSchemeParametersType]):
    """Determines which authentication scheme to use for a given AWS service.
    Code-generated per service.
    """

    def resolve_auth_scheme(
        self, auth_parameters: AuthSchemeParametersType
    ) -> list[HttpAuthOption]:
        """Resolve the authentication scheme that should be used.

        :param auth_parameters: The parameters required for determining which
        authentication schemes to potentially use.

        :returns: A list of authentication schemes that should be used by a given
        request in order of preference.
        """
