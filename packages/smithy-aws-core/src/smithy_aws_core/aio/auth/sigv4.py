#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import re
from typing import TYPE_CHECKING, Protocol

from aws_sdk_signers import AsyncEventSigner, AsyncSigV4Signer, SigV4SigningProperties
from smithy_core.aio.interfaces.auth import (
    AsyncAuthScheme,
    AsyncSigner,
)
from smithy_core.aio.interfaces.auth import (
    AsyncEventSigner as AsyncEventSignerProtocol,
)
from smithy_core.interfaces import TypedProperties as _TypedProperties
from smithy_core.types import PropertyKey
from smithy_http.aio.interfaces import HTTPRequest

from ...auth.sigv4 import _SigV4AuthSchemeBase  # pyright: ignore[reportPrivateUsage]
from ...identity import AWSCredentialsIdentity, AWSIdentityProperties
from ..identity import AsyncAWSCredentialsResolver

if TYPE_CHECKING:
    from smithy_aws_event_stream.events import EventHeaderEncoder

try:
    from smithy_aws_event_stream.events import EventHeaderEncoder

    HAS_EVENT_STREAM = True
except ImportError:
    HAS_EVENT_STREAM = False  # type: ignore


class SigV4Config(Protocol):
    region: str | None
    aws_credentials_identity_resolver: AsyncAWSCredentialsResolver | None


SIGV4_CONFIG = PropertyKey(key="config", value_type=SigV4Config)

type SigV4Signer = AsyncSigner[
    HTTPRequest, AWSCredentialsIdentity, SigV4SigningProperties
]


class AsyncSigV4AuthScheme(
    _SigV4AuthSchemeBase,
    AsyncAuthScheme[
        HTTPRequest,
        AWSCredentialsIdentity,
        AWSIdentityProperties,
        SigV4SigningProperties,
    ],
):
    """SigV4 AsyncAuthScheme."""

    _signer: SigV4Signer

    def __init__(
        self,
        *,
        service: str,
        signer: SigV4Signer | None = None,
    ) -> None:
        """Constructor.

        :param service: The name of the service to sign requests for.
        :param signer: The signer used to sign the request.
        """
        super().__init__(service=service)
        # TODO: There are type mismatches in the signature of the "sign" method.
        # The issues seems to be that it's not using protocols in its signature
        self._signer = signer or AsyncSigV4Signer()  # type: ignore

    def identity_resolver(
        self, *, context: _TypedProperties
    ) -> AsyncAWSCredentialsResolver:
        return super().identity_resolver(context=context)

    def signer(self) -> SigV4Signer:
        return self._signer

    def event_signer(
        self, *, request: HTTPRequest
    ) -> (
        AsyncEventSignerProtocol[AWSCredentialsIdentity, SigV4SigningProperties] | None
    ):
        if not HAS_EVENT_STREAM:
            return None

        auth_value = request.fields["Authorization"].as_string()
        signature: str = re.split("Signature=", auth_value)[-1]

        return AsyncEventSigner(
            initial_signature=signature.encode("utf-8"),
            event_encoder_cls=EventHeaderEncoder,
        )
