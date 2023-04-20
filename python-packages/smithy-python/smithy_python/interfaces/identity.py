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

from datetime import datetime
from typing import Protocol, TypedDict, TypeVar


class Identity(Protocol):
    """An entity available to the client representing who the user is."""

    # The expiration time of the identity. If time zone is provided,
    # it is updated to UTC. The value must always be in UTC.
    expiration: datetime | None = None

    @property
    def is_expired(self) -> bool:
        """Whether the identity is expired."""
        ...


IdentityType = TypeVar("IdentityType", bound=Identity)
IdentityType_contra = TypeVar("IdentityType_contra", bound=Identity, contravariant=True)


class IdentityProperties(TypedDict):
    """Properties used to help determine the identity to return."""

    ...


IdentityPropertiesType_contra = TypeVar("IdentityPropertiesType", bound=IdentityProperties, contravariant=True)


class IdentityResolver(Protocol):
    """Used to load a user's `Identity` from a given source.

    Each `Identity` may have one or more resolver implementations.
    """

    async def get_identity(
        self, *, identity_properties: IdentityPropertiesType_contra
    ) -> IdentityType:
        """Load the user's identity from this resolver.

        :param identity_properties: Properties used to help determine the
        identity to return.
        """
        ...


class IdentityResolverConfiguration(Protocol):
    """The identity resolvers configured in the client."""

    def get_identity_resolver(
        self, *, identity_type: type[IdentityType]
    ) -> IdentityResolver:
        """Retrieve an identity resolver for the provided identity type.

        :param identity_type: The type of identity to resolve.
        """
        ...
