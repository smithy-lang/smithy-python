# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Protocol

from ..shapes import ShapeID
from . import TypedProperties

if TYPE_CHECKING:
    from ..auth import AuthParams


__all__ = ["AuthOption", "AuthSchemeResolver"]


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


class Signer(Protocol):
    """A class that signs requests before they are sent.

    Placeholder for the synchronous signer; populated alongside the sync client
    implementation.
    """

    # TODO(sync-api): implement alongside the sync client


class EventSigner(Protocol):
    """A class that signs event stream events before they are sent.

    Placeholder for the synchronous event signer; populated alongside the sync client
    implementation.
    """

    # TODO(sync-api): implement alongside the sync client


class AuthScheme(Protocol):
    """A class that coordinates identity and auth.

    Placeholder for the synchronous auth scheme; populated alongside the sync client
    implementation.
    """

    # TODO(sync-api): implement alongside the sync client
