#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import sys
from collections.abc import Mapping
from typing import Any, Protocol

from ...interfaces.identity import Identity

if sys.version_info >= (3, 12):
    from typing import TypeVar
else:
    from typing_extensions import TypeVar


_I = TypeVar("_I", bound=Identity, infer_variance=True)
_IP = TypeVar("_IP", bound=Mapping[str, Any], infer_variance=True)


class AsyncIdentityResolver(Protocol[_I, _IP]):
    """Used to load a user's `Identity` from a given source.

    Each `Identity` may have one or more resolver implementations.
    """

    async def get_identity(self, *, properties: _IP) -> _I:
        """Load the user's identity from this resolver.

        :param properties: Properties used to help determine the identity to return.
        """
        ...

    async def invalidate(self) -> None:
        """Discard any cached identity so the next resolution re-reads its source.

        Defaults to a no-op for non-refreshable resolvers.
        """
        return None
