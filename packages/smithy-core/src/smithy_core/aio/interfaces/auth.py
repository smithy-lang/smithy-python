# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import sys
from collections.abc import Mapping
from typing import Any, Protocol

from smithy_core.interfaces import Request

from ...interfaces import TypedProperties as _TypedProperties
from ...interfaces.auth import EventSigner, Signer
from ...interfaces.identity import Identity
from ...shapes import ShapeID
from .identity import AsyncIdentityResolver

if sys.version_info >= (3, 12):
    from typing import TypeVar
else:
    from typing_extensions import TypeVar


_I = TypeVar("_I", infer_variance=True)
_AuthIdentity = TypeVar("_AuthIdentity", bound=Identity, infer_variance=True)
_IP = TypeVar("_IP", bound=Mapping[str, Any], infer_variance=True)
_R = TypeVar("_R", bound=Request, infer_variance=True)
_SP = TypeVar("_SP", bound=Mapping[str, Any], infer_variance=True)


class AsyncSigner(Protocol[_R, _I, _SP]):
    """A class that signs requests before they are sent."""

    async def sign(self, *, request: _R, identity: _I, properties: _SP) -> _R:
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
