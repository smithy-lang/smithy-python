#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock

import pytest
from aws_sdk_signers import AWSCredentialIdentity as SignersCredentialIdentity
from smithy_aws_core.aio.auth.sigv4 import AsyncSigV4AuthScheme
from smithy_aws_core.aio.identity.static import AsyncStaticCredentialsResolver
from smithy_aws_core.business_metrics import FEATURE_IDS, AwsFeatureId
from smithy_aws_core.identity import AWSCredentialsIdentity
from smithy_core.types import TypedProperties


@dataclass
class _Config:
    aws_credentials_identity_resolver: Any
    region: str = "us-west-2"


def _identity_resolver(resolver: Any) -> Any:
    context = TypedProperties({"config": _Config(resolver)})
    return AsyncSigV4AuthScheme(service="svc").identity_resolver(context=context)


async def test_records_resolved_account_id() -> None:
    identity = AWSCredentialsIdentity(
        access_key_id="akid", secret_access_key="s", account_id="123456789012"
    )
    resolver = _identity_resolver(AsyncStaticCredentialsResolver(identity))
    context = TypedProperties()

    assert await resolver.get_identity(properties={}, context=context) is identity
    assert list(context[FEATURE_IDS]) == [
        AwsFeatureId.CREDENTIALS_CODE,
        AwsFeatureId.RESOLVED_ACCOUNT_ID,
    ]


@pytest.mark.parametrize(
    "identity",
    [
        AWSCredentialsIdentity(access_key_id="akid", secret_access_key="s"),
        # Has no account_id field at all.
        SignersCredentialIdentity(access_key_id="akid", secret_access_key="s"),
    ],
)
async def test_does_not_record_account_id_when_missing(identity: Any) -> None:
    configured = AsyncMock()
    configured.get_identity.return_value = identity
    context = TypedProperties()

    result = await _identity_resolver(configured).get_identity(
        properties={}, context=context
    )

    assert result is identity
    assert FEATURE_IDS not in context


async def test_resolves_without_context() -> None:
    identity = AWSCredentialsIdentity(
        access_key_id="akid", secret_access_key="s", account_id="123456789012"
    )
    resolver = _identity_resolver(AsyncStaticCredentialsResolver(identity))

    assert await resolver.get_identity(properties={}) is identity


async def test_invalidate_reaches_configured_resolver() -> None:
    configured = AsyncMock()
    await _identity_resolver(configured).invalidate()
    configured.invalidate.assert_awaited_once()
