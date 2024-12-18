"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import re
import typing
from datetime import UTC, datetime
from io import BytesIO

import pytest
from aws_sdk_signers import (
    URI,
    AsyncSigV4Signer,
    AWSCredentialIdentity,
    AWSRequest,
    Fields,
    SigV4Signer,
    SigV4SigningProperties,
)

SIGV4_RE = re.compile(
    r"AWS4-HMAC-SHA256 "
    r"Credential=(?P<access_key>\w+)/\d+/"
    r"(?P<signing_region>[a-z0-9-]+)/"
)


@pytest.fixture(scope="module")
def aws_identity() -> AWSCredentialIdentity:
    return AWSCredentialIdentity(
        access_key_id="AKID123456",
        secret_access_key="EXAMPLE1234SECRET",
        session_token="X123456SESSION",
    )


@pytest.fixture(scope="module")
def signing_properties() -> SigV4SigningProperties:
    return SigV4SigningProperties(
        region="us-west-2",
        service="ec2",
        payload_signing_enabled=False,
    )


@pytest.fixture(scope="module")
def aws_request() -> AWSRequest:
    return AWSRequest(
        destination=URI(
            scheme="https",
            host="127.0.0.1",
            port=8000,
        ),
        method="GET",
        body=BytesIO(b"123456"),
        fields=Fields({}),
    )


class TestSigV4Signer:
    SIGV4_SYNC_SIGNER = SigV4Signer()

    def test_sign(
        self,
        aws_identity: AWSCredentialIdentity,
        aws_request: AWSRequest,
        signing_properties: SigV4SigningProperties,
    ) -> None:
        signed_request = self.SIGV4_SYNC_SIGNER.sign(
            signing_properties=signing_properties,
            request=aws_request,
            identity=aws_identity,
        )
        assert isinstance(signed_request, AWSRequest)
        assert signed_request is not aws_request
        assert "authorization" in signed_request.fields
        authorization_field = signed_request.fields["authorization"]
        assert SIGV4_RE.match(authorization_field.as_string())

    @typing.no_type_check
    def test_sign_with_invalid_identity(
        self, aws_request: AWSRequest, signing_properties: SigV4SigningProperties
    ) -> None:
        """Ignore typing as we're testing an invalid input state."""
        identity = object()
        assert not isinstance(identity, AWSCredentialIdentity)
        with pytest.raises(ValueError):
            self.SIGV4_SYNC_SIGNER.sign(
                signing_properties=signing_properties,
                request=aws_request,
                identity=identity,
            )

    def test_sign_with_expired_identity(
        self, aws_request: AWSRequest, signing_properties: SigV4SigningProperties
    ) -> None:
        identity = AWSCredentialIdentity(
            access_key_id="AKID123456",
            secret_access_key="EXAMPLE1234SECRET",
            session_token="X123456SESSION",
            expiration=datetime(1970, 1, 1, tzinfo=UTC),
        )
        with pytest.raises(ValueError):
            self.SIGV4_SYNC_SIGNER.sign(
                signing_properties=signing_properties,
                request=aws_request,
                identity=identity,
            )


class TestAsyncSigV4Signer:
    SIGV4_ASYNC_SIGNER = AsyncSigV4Signer()

    async def test_sign(
        self,
        aws_identity: AWSCredentialIdentity,
        aws_request: AWSRequest,
        signing_properties: SigV4SigningProperties,
    ) -> None:
        signed_request = await self.SIGV4_ASYNC_SIGNER.sign(
            signing_properties=signing_properties,
            request=aws_request,
            identity=aws_identity,
        )
        assert isinstance(signed_request, AWSRequest)
        assert signed_request is not aws_request
        assert "authorization" in signed_request.fields
        authorization_field = signed_request.fields["authorization"]
        assert SIGV4_RE.match(authorization_field.as_string())

    @typing.no_type_check
    async def test_sign_with_invalid_identity(
        self, aws_request: AWSRequest, signing_properties: SigV4SigningProperties
    ) -> None:
        """Ignore typing as we're testing an invalid input state."""
        identity = object()
        assert not isinstance(identity, AWSCredentialIdentity)
        with pytest.raises(ValueError):
            await self.SIGV4_ASYNC_SIGNER.sign(
                signing_properties=signing_properties,
                request=aws_request,
                identity=identity,
            )

    async def test_sign_with_expired_identity(
        self, aws_request: AWSRequest, signing_properties: SigV4SigningProperties
    ) -> None:
        identity = AWSCredentialIdentity(
            access_key_id="AKID123456",
            secret_access_key="EXAMPLE1234SECRET",
            session_token="X123456SESSION",
            expiration=datetime(1970, 1, 1, tzinfo=UTC),
        )
        with pytest.raises(ValueError):
            await self.SIGV4_ASYNC_SIGNER.sign(
                signing_properties=signing_properties,
                request=aws_request,
                identity=identity,
            )
