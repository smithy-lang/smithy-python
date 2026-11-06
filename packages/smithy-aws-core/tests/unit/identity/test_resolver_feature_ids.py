#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import json
from collections.abc import Callable
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from smithy_aws_core.aio.identity.chain.provider import NamedResolver
from smithy_aws_core.aio.identity.environment import (
    AsyncEnvironmentCredentialsResolver,
)
from smithy_aws_core.aio.identity.process import AsyncProcessCredentialsResolver
from smithy_aws_core.aio.identity.static import AsyncStaticCredentialsResolver
from smithy_aws_core.business_metrics import AwsFeatureId
from smithy_aws_core.identity import AWSCredentialsIdentity

_IDENTITY = AWSCredentialsIdentity(access_key_id="akid", secret_access_key="secret")


@pytest.mark.parametrize(
    "create",
    [
        lambda: AsyncStaticCredentialsResolver(_IDENTITY),
        lambda: AsyncEnvironmentCredentialsResolver(),
        lambda: AsyncProcessCredentialsResolver(["mock-process"]),
    ],
)
async def test_chain_records_only_the_provider_feature_ids(
    create: Callable[[], Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "akid")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")
    process = AsyncMock()
    process.returncode = 0
    process.communicate.return_value = (
        json.dumps(
            {"Version": 1, "AccessKeyId": "akid", "SecretAccessKey": "secret"}
        ).encode("utf-8"),
        b"",
    )
    named = NamedResolver(
        provider_name="ProfileStaticKeys",
        resolver=create(),
        feature_ids=(AwsFeatureId.CREDENTIALS_PROFILE,),
    )
    features: dict[AwsFeatureId, None] = {}

    with patch("asyncio.create_subprocess_exec", return_value=process):
        await named.get_identity(properties={"_feature_ids": features})

    # The resolver's own feature, for when it's used directly, isn't recorded.
    assert features == {AwsFeatureId.CREDENTIALS_PROFILE: None}


async def test_environment_resolver_registers_env_vars_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "akid")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")
    features: dict[AwsFeatureId, None] = {}

    await AsyncEnvironmentCredentialsResolver().get_identity(
        properties={"_feature_ids": features}
    )

    assert features == {AwsFeatureId.CREDENTIALS_ENV_VARS: None}


@pytest.mark.parametrize("provider_feature_ids", [(), None])
async def test_chain_keeps_resolver_feature_ids_when_provider_has_none(
    provider_feature_ids: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "akid")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")
    named = NamedResolver(
        provider_name="Custom",
        resolver=AsyncEnvironmentCredentialsResolver(),
        feature_ids=provider_feature_ids,
    )
    features: dict[AwsFeatureId, None] = {}

    await named.get_identity(properties={"_feature_ids": features})

    assert features == {AwsFeatureId.CREDENTIALS_ENV_VARS: None}
