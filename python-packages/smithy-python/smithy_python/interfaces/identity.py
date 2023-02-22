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
from typing import Any, Protocol


class Identity(Protocol):
    """An entity available to the client representing who the user is."""

    expiration: datetime | None = None


class IdentityResolver(Protocol):
    """Used to load a user's `Identity` from a given source.

    Each `Identity` may have one or more resolver implementations.
    """

    async def get_identity(self, *, identity_properties: dict[str, Any]) -> Identity:
        """Load the user's identity from this resolver.

        :param identity_properties: Properties used to help determine the
        identity to return.
        """
        ...


class IdentityResolverConfiguration(Protocol):
    """The identity resolvers configured in the client."""

    def get_identity_resolver(
        self, *, identity_type: type[Identity]
    ) -> IdentityResolver:
        """Retrieve an identity resolver for the provided identity type.

        :param identity_type: The type of identity to resolve.
        """
        ...
