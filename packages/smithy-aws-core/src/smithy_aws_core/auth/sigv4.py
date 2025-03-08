#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass
from typing import Protocol

from smithy_aws_core.identity import AWSCredentialsIdentity
from smithy_core.aio.interfaces.identity import IdentityResolver
from smithy_core.exceptions import SmithyIdentityException
from smithy_core.interfaces.identity import IdentityProperties
from smithy_http.aio.interfaces.auth import HTTPAuthScheme, HTTPSigner
from aws_sdk_signers import SigV4SigningProperties, AsyncSigV4Signer


class SigV4Config(Protocol):
    aws_credentials_identity_resolver: (
        IdentityResolver[AWSCredentialsIdentity, IdentityProperties] | None
    )


@dataclass(init=False)
class SigV4AuthScheme(
    HTTPAuthScheme[
        AWSCredentialsIdentity, SigV4Config, IdentityProperties, SigV4SigningProperties
    ]
):
    """SigV4 AuthScheme."""

    scheme_id: str
    signer: HTTPSigner[AWSCredentialsIdentity, SigV4SigningProperties]

    def __init__(
        self,
        *,
        signer: HTTPSigner[AWSCredentialsIdentity, SigV4SigningProperties]
        | None = None,
    ) -> None:
        """Constructor.

        :param identity_resolver: The identity resolver to extract the api key identity.
        :param signer: The signer used to sign the request.
        """
        self.scheme_id = "aws.auth#sigv4"
        # TODO: There are type mismatches in the signature of the "sign" method.
        self.signer = signer or AsyncSigV4Signer()  # type: ignore

    def identity_resolver(
        self, *, config: SigV4Config
    ) -> IdentityResolver[AWSCredentialsIdentity, IdentityProperties]:
        if not config.aws_credentials_identity_resolver:
            raise SmithyIdentityException(
                "Attempted to use SigV4 auth, but aws_credentials_identity_resolver was not "
                "set on the config."
            )
        return config.aws_credentials_identity_resolver
