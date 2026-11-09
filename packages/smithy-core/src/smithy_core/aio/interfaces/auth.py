# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Mapping
from typing import Any, Protocol

from smithy_core.interfaces import Request

from ...interfaces import TypedProperties as _TypedProperties
from ...interfaces.auth import EventSigner, Signer
from ...interfaces.identity import Identity
from ...shapes import ShapeID
from .identity import AsyncIdentityResolver


class AsyncSigner[R: Request, I, SP: Mapping[str, Any]](Protocol):
    """A class that signs requests before they are sent."""

    async def sign(self, *, request: R, identity: I, properties: SP) -> R:
        """Get a signed version of the request.

        :param request: The request to be signed.
        :param identity: The identity to use to sign the request.
        :param properties: Additional properties used to sign the request.
        """
        ...


class AsyncAuthScheme[
    R: Request,
    I: Identity,
    IP: Mapping[str, Any],
    SP: Mapping[str, Any],
](Protocol):
    """A class that coordinates identity and auth."""

    scheme_id: ShapeID
    """The ID of the auth scheme."""

    def identity_properties(self, *, context: _TypedProperties) -> IP:
        """Construct identity properties from the request context.

        The context will always include the client's config under "config". Other
        properties may be added by :py:class:`smithy_core.interceptors.Interceptor`s.

        :param context: The context of the request.
        """
        ...

    def identity_resolver(
        self, *, context: _TypedProperties
    ) -> AsyncIdentityResolver[I, IP]:
        """Get an identity resolver for the request.

        The context will always include the client's config under "config". Other
        properties may be added by :py:class:`smithy_core.interceptors.Interceptor`s.

        :param context: The context of the request.
        """
        ...

    def signer_properties(self, *, context: _TypedProperties) -> SP:
        """Construct signer properties from the request context.

        The context will always include the client's config under "config". Other
        properties may be added by :py:class:`smithy_core.interceptors.Interceptor`s.

        :param context: The context of the request.
        """
        ...

    def signer(self) -> AsyncSigner[R, I, SP] | Signer[R, I, SP]:
        """Get a signer for the request.

        Signers that do no I/O may be synchronous.
        """
        ...

    def event_signer(self, *, request: R) -> EventSigner[I, SP] | None:
        """Construct a signer for event stream events.

        :param request: The request that will initiate the event stream. The request
            will not have been sent when this method is called.
        :returns: An event signer if the scheme supports signing events, otherwise None.
        """
        return None
