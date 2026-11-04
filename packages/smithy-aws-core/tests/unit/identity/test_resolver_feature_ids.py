#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import json
from collections.abc import Callable
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from smithy_aws_core.aio.identity.environment import (
    AsyncEnvironmentCredentialsResolver,
)
from smithy_aws_core.aio.identity.process import AsyncProcessCredentialsResolver
from smithy_aws_core.aio.identity.static import AsyncStaticCredentialsResolver
from smithy_aws_core.business_metrics import FEATURE_IDS, AwsFeatureId
from smithy_aws_core.identity import AWSCredentialsIdentity
from smithy_core.types import TypedProperties

_IDENTITY = AWSCredentialsIdentity(access_key_id="akid", secret_access_key="secret")


@pytest.mark.parametrize(
    "create",
    [
        lambda: AsyncStaticCredentialsResolver(_IDENTITY, feature_ids=()),
        lambda: AsyncEnvironmentCredentialsResolver(feature_ids=()),
        lambda: AsyncProcessCredentialsResolver(["mock-process"], feature_ids=()),
    ],
)
async def test_registers_nothing_with_empty_feature_ids(
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
    context = TypedProperties()

    with patch("asyncio.create_subprocess_exec", return_value=process):
        await create().get_identity(properties={}, context=context)

    assert FEATURE_IDS not in context


async def test_environment_resolver_registers_env_vars_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "akid")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")
    context = TypedProperties()

    await AsyncEnvironmentCredentialsResolver().get_identity(
        properties={}, context=context
    )

    assert context[FEATURE_IDS] == {AwsFeatureId.CREDENTIALS_ENV_VARS: None}
