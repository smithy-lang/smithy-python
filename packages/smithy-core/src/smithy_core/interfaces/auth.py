# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Protocol

from ..shapes import ShapeID
from . import TypedProperties

if TYPE_CHECKING:
    from ..auth import AuthParams


class AuthOption(Protocol):
    """Auth scheme used for signing and identity resolution."""

    scheme_id: ShapeID
    """The ID of the auth scheme to use."""

    identity_properties: TypedProperties
    """Paramters to pass to the identity resolver method."""

    signer_properties: TypedProperties
    """Paramters to pass to the signing method."""


class AuthSchemeResolver(Protocol):
    """Determines which authentication scheme to use for a given service."""

    def resolve_auth_scheme(
        self, *, auth_parameters: "AuthParams[Any, Any]"
    ) -> Sequence[AuthOption]:
        """Resolve an ordered list of applicable auth schemes.

        :param auth_parameters: The parameters required for determining which
            authentication schemes to potentially use.
        """
        ...
