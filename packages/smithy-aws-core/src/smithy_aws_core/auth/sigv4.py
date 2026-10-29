#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from typing import Any, Self

from aws_sdk_signers import SigV4Signer, SigV4SigningProperties
from smithy_core.exceptions import SmithyIdentityError
from smithy_core.interfaces import TypedProperties as _TypedProperties
from smithy_core.interfaces.auth import AuthScheme, Signer
from smithy_http.aio.interfaces import HTTPRequest

from ..identity import (
    AWS_IDENTITY_CONFIG,
    AWSCredentialsIdentity,
    AWSCredentialsResolver,
    AWSIdentityProperties,
)
from ..traits import SigV4Trait

__all__ = ["SigV4AuthScheme"]


class _SigV4AuthSchemeBase:
    """SigV4 auth scheme logic shared by the sync and async schemes."""

    scheme_id = SigV4Trait.id

    def __init__(self, *, service: str) -> None:
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

    def identity_resolver(self, *, context: _TypedProperties) -> Any:
        config = context.get("config")
        if config is None or config.aws_credentials_identity_resolver is None:
            raise SmithyIdentityError(
                "Attempted to use SigV4 auth, but aws_credentials_identity_resolver was not "
                "set on the config."
            )
        return config.aws_credentials_identity_resolver

    def signer_properties(self, *, context: _TypedProperties) -> SigV4SigningProperties:
        config = context.get("config")
        if config is None or config.region is None:
            raise SmithyIdentityError(
                "Attempted to use SigV4 auth, but region was not set on the config."
            )
        return {
            "region": config.region,
            "service": self._service,
        }

    @classmethod
    def from_trait(cls, trait: SigV4Trait, /) -> Self:
        return cls(service=trait.name)


class SigV4AuthScheme(
    _SigV4AuthSchemeBase,
    AuthScheme[
        HTTPRequest,
        AWSCredentialsIdentity,
        AWSIdentityProperties,
        SigV4SigningProperties,
    ],
):
    """SigV4 AuthScheme."""

    _signer: Signer[HTTPRequest, AWSCredentialsIdentity, SigV4SigningProperties]

    def __init__(
        self,
        *,
        service: str,
        signer: Signer[HTTPRequest, AWSCredentialsIdentity, SigV4SigningProperties]
        | None = None,
    ) -> None:
        """Constructor.

        :param service: The name of the service to sign requests for.
        :param signer: The signer used to sign the request.
        """
        super().__init__(service=service)
        # The signer's own request type is structurally compatible but not declared
        # as an HTTPRequest protocol.
        self._signer = signer or SigV4Signer()  # type: ignore

    def identity_resolver(self, *, context: _TypedProperties) -> AWSCredentialsResolver:
        return super().identity_resolver(context=context)

    def signer(
        self,
    ) -> Signer[HTTPRequest, AWSCredentialsIdentity, SigV4SigningProperties]:
        return self._signer
