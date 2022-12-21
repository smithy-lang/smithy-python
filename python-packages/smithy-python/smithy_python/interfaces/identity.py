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

from datetime import datetime
from typing import Any, Generic, Protocol, TypeVar

from .http import Request


class Identity(Protocol):
    """An entity available to the client representing who the user is."""

    expiration: datetime | None = None


IdentityType = TypeVar("IdentityType", bound=Identity)


class TokenIdentity(Identity):

    token: str


class LoginIdentity(Identity):

    username: str
    password: str


class AnonymousIdentity(Identity):
    ...


class IdentityResolver(Generic[IdentityType]):
    """Used to load a user's `Identity` from a given source.

    Each `Identity` has one or more resolver implementations. The default resolver
    for AWS consults environment variables, IMDS, ~/.aws, etc.
    """

    async def get_identity(
        self, *, identity_properties: dict[str, Any]
    ) -> IdentityType:
        """Load the user's identity from this resolver.

        :param identity_properties: Properties loaded from the service's
        authentication rules.

        :returns: The user's identity.
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
    """An entity within the client representing a way to generate a signature for a
    HTTP request.
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
