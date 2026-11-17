#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from collections.abc import Mapping
from typing import Any, Protocol, TypeVar

from ...interfaces.identity import Identity

_I_co = TypeVar("_I_co", bound=Identity, covariant=True)
_IP_contra = TypeVar("_IP_contra", bound=Mapping[str, Any], contravariant=True)


class AsyncIdentityResolver(Protocol[_I_co, _IP_contra]):
    """Used to load a user's `Identity` from a given source.

    Each `Identity` may have one or more resolver implementations.
    """

    async def get_identity(self, *, properties: _IP_contra) -> _I_co:
        """Load the user's identity from this resolver.

        :param properties: Properties used to help determine the identity to return.
        """
        ...

    async def invalidate(self) -> None:
        """Discard any cached identity so the next resolution re-reads its source.

        Defaults to a no-op for non-refreshable resolvers.
        """
        return None
