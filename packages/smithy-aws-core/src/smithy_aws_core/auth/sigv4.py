#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import re
from typing import TYPE_CHECKING, Protocol, Self

from aws_sdk_signers import AsyncEventSigner, AsyncSigV4Signer, SigV4SigningProperties
from smithy_core.aio.interfaces.auth import AuthScheme, EventSigner, Signer
from smithy_core.exceptions import SmithyIdentityError
from smithy_core.interfaces import TypedProperties as _TypedProperties
from smithy_core.types import PropertyKey
from smithy_http.aio.interfaces import HTTPRequest

from ..identity import (
    AWS_IDENTITY_CONFIG,
    AWSCredentialsIdentity,
    AWSCredentialsResolver,
    AWSIdentityProperties,
)
from ..traits import SigV4Trait

if TYPE_CHECKING:
    from smithy_aws_event_stream.events import EventHeaderEncoder

try:
    from smithy_aws_event_stream.events import EventHeaderEncoder

    HAS_EVENT_STREAM = True
except ImportError:
    HAS_EVENT_STREAM = False  # type: ignore


class SigV4Config(Protocol):
    region: str | None
    aws_credentials_identity_resolver: AWSCredentialsResolver | None


SIGV4_CONFIG = PropertyKey(key="config", value_type=SigV4Config)

type SigV4Signer = Signer[HTTPRequest, AWSCredentialsIdentity, SigV4SigningProperties]


class SigV4AuthScheme(
    AuthScheme[
        HTTPRequest,
        AWSCredentialsIdentity,
        AWSIdentityProperties,
        SigV4SigningProperties,
    ]
):
    """SigV4 AuthScheme."""

    scheme_id = SigV4Trait.id
    _signer: SigV4Signer

    def __init__(
        self,
        *,
        service: str,
        signer: SigV4Signer | None = None,
    ) -> None:
        """Constructor.

        :param identity_resolver: The identity resolver to extract the api key identity.
        :param signer: The signer used to sign the request.
        """
        # TODO: There are type mismatches in the signature of the "sign" method.
        # The issues seems to be that it's not using protocols in its signature
        self._signer = signer or AsyncSigV4Signer()  # type: ignore
        self._service = service

    def identity_properties(
        self, *, context: _TypedProperties
    ) -> AWSIdentityProperties:
        config = context[AWS_IDENTITY_CONFIG]
        return {
            "access_key_id": config.aws_access_key_id,
            "secret_access_key": config.aws_secret_access_key,
            "session_token": config.aws_session_token,
        }

    def identity_resolver(self, *, context: _TypedProperties) -> AWSCredentialsResolver:
        config = context.get(SIGV4_CONFIG)
        if config is None or config.aws_credentials_identity_resolver is None:
            raise SmithyIdentityError(
                "Attempted to use SigV4 auth, but aws_credentials_identity_resolver was not "
                "set on the config."
            )
        return config.aws_credentials_identity_resolver

    def signer_properties(self, *, context: _TypedProperties) -> SigV4SigningProperties:
        config = context.get(SIGV4_CONFIG)
        if config is None or config.region is None:
            raise SmithyIdentityError(
                "Attempted to use SigV4 auth, but region was not set on the config."
            )
        return {
            "region": config.region,
            "service": self._service,
        }

    def signer(self) -> SigV4Signer:
        return self._signer

    def event_signer(
        self, *, request: HTTPRequest
    ) -> EventSigner[AWSCredentialsIdentity, SigV4SigningProperties] | None:
        if not HAS_EVENT_STREAM:
            return None

        auth_value = request.fields["Authorization"].as_string()
        signature: str = re.split("Signature=", auth_value)[-1]

        return AsyncEventSigner(
            initial_signature=signature.encode("utf-8"),
            event_encoder_cls=EventHeaderEncoder,
        )

    @classmethod
    def from_trait(cls, trait: SigV4Trait, /) -> Self:
        return cls(service=trait.name)
