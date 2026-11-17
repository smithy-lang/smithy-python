# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Mapping
from typing import Any, Protocol, TypeVar

from smithy_core.interfaces import Request

from ...interfaces import TypedProperties as _TypedProperties
from ...interfaces.auth import EventSigner, Signer
from ...interfaces.identity import Identity
from ...shapes import ShapeID
from .identity import AsyncIdentityResolver

_I_contra = TypeVar("_I_contra", contravariant=True)
_AuthIdentity = TypeVar("_AuthIdentity", bound=Identity)
_IP = TypeVar("_IP", bound=Mapping[str, Any])
_R = TypeVar("_R", bound=Request)
_SP = TypeVar("_SP", bound=Mapping[str, Any])
_SP_contra = TypeVar("_SP_contra", bound=Mapping[str, Any], contravariant=True)


class AsyncSigner(Protocol[_R, _I_contra, _SP_contra]):
    """A class that signs requests before they are sent."""

    async def sign(
        self, *, request: _R, identity: _I_contra, properties: _SP_contra
    ) -> _R:
        """Get a signed version of the request.

        :param request: The request to be signed.
        :param identity: The identity to use to sign the request.
        :param properties: Additional properties used to sign the request.
        """
        ...


class AsyncAuthScheme(Protocol[_R, _AuthIdentity, _IP, _SP]):
    """A class that coordinates identity and auth."""

    scheme_id: ShapeID
    """The ID of the auth scheme."""

    def identity_properties(self, *, context: _TypedProperties) -> _IP:
        """Construct identity properties from the request context.

        The context will always include the client's config under "config". Other
        properties may be added by :py:class:`smithy_core.interceptors.Interceptor`s.

        :param context: The context of the request.
        """
        ...

    def identity_resolver(
        self, *, context: _TypedProperties
    ) -> AsyncIdentityResolver[_AuthIdentity, _IP]:
        """Get an identity resolver for the request.

        The context will always include the client's config under "config". Other
        properties may be added by :py:class:`smithy_core.interceptors.Interceptor`s.

        :param context: The context of the request.
        """
        ...

    def signer_properties(self, *, context: _TypedProperties) -> _SP:
        """Construct signer properties from the request context.

        The context will always include the client's config under "config". Other
        properties may be added by :py:class:`smithy_core.interceptors.Interceptor`s.

        :param context: The context of the request.
        """
        ...

    def signer(
        self,
    ) -> AsyncSigner[_R, _AuthIdentity, _SP] | Signer[_R, _AuthIdentity, _SP]:
        """Get a signer for the request.

        Signers that do no I/O may be synchronous.
        """
        ...

    def event_signer(self, *, request: _R) -> EventSigner[_AuthIdentity, _SP] | None:
        """Construct a signer for event stream events.

        :param request: The request that will initiate the event stream. The request
            will not have been sent when this method is called.
        :returns: An event signer if the scheme supports signing events, otherwise None.
        """
        return None
