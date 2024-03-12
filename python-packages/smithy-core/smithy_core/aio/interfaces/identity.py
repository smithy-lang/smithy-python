#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from typing import Protocol

from ...interfaces.identity import IdentityPropertiesType_contra, IdentityType_cov


class IdentityResolver(Protocol[IdentityType_cov, IdentityPropertiesType_contra]):
    """Used to load a user's `Identity` from a given source.

    Each `Identity` may have one or more resolver implementations.
    """

    async def get_identity(
        self, *, identity_properties: IdentityPropertiesType_contra
    ) -> IdentityType_cov:
        """Load the user's identity from this resolver.

        :param identity_properties: Properties used to help determine the identity to
            return.
        """
        ...
