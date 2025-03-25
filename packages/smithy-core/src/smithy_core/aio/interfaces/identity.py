#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from collections.abc import Mapping
from typing import Any, Protocol

from ...interfaces.identity import Identity


class IdentityResolver[I: Identity, IP: Mapping[str, Any]](Protocol):
    """Used to load a user's `Identity` from a given source.

    Each `Identity` may have one or more resolver implementations.
    """

    async def get_identity(self, *, properties: IP) -> I:
        """Load the user's identity from this resolver.

        :param properties: Properties used to help determine the identity to return.
        """
        ...
