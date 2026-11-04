#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import re
from typing import TYPE_CHECKING, Protocol, Self

from aws_sdk_signers import AsyncEventSigner, AsyncSigV4Signer, SigV4SigningProperties
from smithy_core.aio.interfaces.auth import (
    AsyncAuthScheme,
    AsyncSigner,
)
from smithy_core.aio.interfaces.auth import (
    AsyncEventSigner as AsyncEventSignerProtocol,
)
from smithy_core.exceptions import SmithyIdentityError
from smithy_core.interfaces import TypedProperties as _TypedProperties
from smithy_core.types import PropertyKey
from smithy_http.aio.interfaces import HTTPRequest

from ...business_metrics import AwsFeatureId, register_feature_id
from ...identity import (
    AWS_IDENTITY_CONFIG,
    AWSCredentialsIdentity,
    AWSIdentityProperties,
)
from ...traits import SigV4Trait
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


class _AccountIdRecordingResolver:
    """Records RESOLVED_ACCOUNT_ID when resolved credentials include an account ID.

    Wraps the credentials resolver used for SigV4, so this is recorded for each request
    whose credentials are resolved with request properties, whether they come from the
    credential chain or another resolver. Nothing is recorded without request
    properties, such as when signing event stream messages.
    """

    def __init__(self, resolver: AsyncAWSCredentialsResolver) -> None:
        self._resolver = resolver

    async def get_identity(
        self,
        *,
        properties: AWSIdentityProperties,
        context: _TypedProperties | None = None,
    ) -> AWSCredentialsIdentity:
        identity = await self._resolver.get_identity(
            properties=properties, context=context
        )
        # The resolver may return an identity without an account_id field, such as
        # aws_sdk_signers.AWSCredentialIdentity.
        if context is not None and getattr(identity, "account_id", None):
            register_feature_id(context, AwsFeatureId.RESOLVED_ACCOUNT_ID)
        return identity

    async def invalidate(self) -> None:
        await self._resolver.invalidate()


class AsyncSigV4AuthScheme(
    AsyncAuthScheme[
        HTTPRequest,
        AWSCredentialsIdentity,
        AWSIdentityProperties,
        SigV4SigningProperties,
    ]
):
    """SigV4 AsyncAuthScheme."""

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

    def identity_resolver(
        self, *, context: _TypedProperties
    ) -> AsyncAWSCredentialsResolver:
        config = context.get(SIGV4_CONFIG)
        if config is None or config.aws_credentials_identity_resolver is None:
            raise SmithyIdentityError(
                "Attempted to use SigV4 auth, but aws_credentials_identity_resolver was not "
                "set on the config."
            )
        return _AccountIdRecordingResolver(config.aws_credentials_identity_resolver)

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

    @classmethod
    def from_trait(cls, trait: SigV4Trait, /) -> Self:
        return cls(service=trait.name)
