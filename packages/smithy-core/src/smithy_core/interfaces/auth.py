# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import sys
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Protocol

from ..shapes import ShapeID
from . import TypedProperties
from .identity import Identity

if sys.version_info >= (3, 12):
    from typing import TypeVar
else:
    from typing_extensions import TypeVar


if TYPE_CHECKING:
    from ..auth import AuthParams
    from .identity import IdentityResolver


__all__ = [
    "AuthOption",
    "AuthScheme",
    "AuthSchemeResolver",
    "EventSigner",
    "Signer",
]

_I = TypeVar("_I", infer_variance=True)
_AuthIdentity = TypeVar("_AuthIdentity", bound=Identity, infer_variance=True)
_IP = TypeVar("_IP", bound=Mapping[str, Any], infer_variance=True)
_R = TypeVar("_R", infer_variance=True)
_SP = TypeVar("_SP", bound=Mapping[str, Any], infer_variance=True)


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


class Signer(Protocol[_R, _I, _SP]):
    """A class that signs requests before they are sent."""

    def sign(self, *, request: _R, identity: _I, properties: _SP) -> _R:
        """Get a signed version of the request.

        :param request: The request to be signed.
        :param identity: The identity to use to sign the request.
        :param properties: Additional properties used to sign the request.
        """
        ...


class EventSigner(Protocol[_I, _SP]):
    """A class that signs event stream events before they are sent."""

    def sign(self, *, event: Any, identity: _I, properties: _SP) -> Any:
        """Get a signed version of the event.

        :param event: The event to be signed.
        :param identity: The identity to use to sign the event.
        :param properties: Additional properties used to sign the event.
        """
        ...

    def sign_empty(self, *, event: Any, identity: _I, properties: _SP) -> Any:
        """Get a signed version of an empty event.

        :param event: The empty event to be signed.
        :param identity: The identity to use to sign the event.
        :param properties: Additional properties used to sign the event.
        """
        ...


class AuthScheme(Protocol[_R, _AuthIdentity, _IP, _SP]):
    """A class that coordinates identity and auth."""

    scheme_id: ShapeID
    """The ID of the auth scheme."""

    def identity_properties(self, *, context: TypedProperties) -> _IP:
        """Construct identity properties from the request context.

        :param context: The context of the request.
        """
        ...

    def identity_resolver(
        self, *, context: TypedProperties
    ) -> "IdentityResolver[_AuthIdentity, _IP]":
        """Get an identity resolver for the request.

        :param context: The context of the request.
        """
        ...

    def signer_properties(self, *, context: TypedProperties) -> _SP:
        """Construct signer properties from the request context.

        :param context: The context of the request.
        """
        ...

    def signer(self) -> Signer[_R, _AuthIdentity, _SP]:
        """Get a signer for the request."""
        ...

    def event_signer(self, *, request: _R) -> EventSigner[_AuthIdentity, _SP] | None:
        """Construct a signer for event stream events.

        :param request: The request that will initiate the event stream.
        :returns: An event signer if the scheme supports signing events, otherwise None.
        """
        return None
