#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import json
import subprocess
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from inspect import isawaitable
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from smithy_aws_core.aio.identity.chain.provider import AsyncNamedResolver
from smithy_aws_core.aio.identity.environment import (
    AsyncEnvironmentCredentialsResolver,
)
from smithy_aws_core.aio.identity.process import AsyncProcessCredentialsResolver
from smithy_aws_core.aio.identity.static import AsyncStaticCredentialsResolver
from smithy_aws_core.business_metrics import AwsFeatureId
from smithy_aws_core.identity import AWSCredentialsIdentity
from smithy_aws_core.identity.chain.provider import NamedResolver
from smithy_aws_core.identity.environment import EnvironmentCredentialsResolver
from smithy_aws_core.identity.process import ProcessCredentialsResolver
from smithy_aws_core.identity.static import StaticCredentialsResolver

_IDENTITY = AWSCredentialsIdentity(access_key_id="akid", secret_access_key="secret")
_OUTPUT = json.dumps(
    {"Version": 1, "AccessKeyId": "akid", "SecretAccessKey": "secret"}
).encode("utf-8")

_SYNC = {
    "static": lambda: StaticCredentialsResolver(_IDENTITY),
    "environment": lambda: EnvironmentCredentialsResolver(),
    "process": lambda: ProcessCredentialsResolver(["mock-process"]),
}
_ASYNC = {
    "static": lambda: AsyncStaticCredentialsResolver(_IDENTITY),
    "environment": lambda: AsyncEnvironmentCredentialsResolver(),
    "process": lambda: AsyncProcessCredentialsResolver(["mock-process"]),
}
_OWN_FEATURE = {
    "static": AwsFeatureId.CREDENTIALS_CODE,
    "environment": AwsFeatureId.CREDENTIALS_ENV_VARS,
    "process": AwsFeatureId.CREDENTIALS_PROCESS,
}


@contextmanager
def _credential_sources(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "akid")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")
    process = AsyncMock(returncode=0)
    process.communicate.return_value = (_OUTPUT, b"")
    completed = subprocess.CompletedProcess([], 0, stdout=_OUTPUT, stderr=b"")
    with (
        patch("asyncio.create_subprocess_exec", return_value=process),
        patch("subprocess.run", return_value=completed),
    ):
        yield


async def _resolve(resolver: Any, properties: dict[str, Any]) -> Any:
    result = resolver.get_identity(properties=properties)
    return await result if isawaitable(result) else result


def _named(sync: bool, resolver: Any, feature_ids: Any) -> Any:
    named_type = NamedResolver if sync else AsyncNamedResolver
    return named_type(
        provider_name="ProfileStaticKeys", resolver=resolver, feature_ids=feature_ids
    )


_MODES = pytest.mark.parametrize("sync", [True, False], ids=["sync", "async"])
_KINDS = pytest.mark.parametrize("kind", list(_SYNC))


def _create(sync: bool, kind: str) -> Callable[[], Any]:
    return (_SYNC if sync else _ASYNC)[kind]


@_MODES
@_KINDS
async def test_resolvers_record_their_feature_when_used_directly(
    sync: bool, kind: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    features: dict[AwsFeatureId, None] = {}

    with _credential_sources(monkeypatch):
        await _resolve(_create(sync, kind)(), {"_feature_ids": features})

    assert features == {_OWN_FEATURE[kind]: None}


@_MODES
@_KINDS
async def test_chain_records_only_the_provider_feature_ids(
    sync: bool, kind: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    named = _named(sync, _create(sync, kind)(), (AwsFeatureId.CREDENTIALS_PROFILE,))
    features: dict[AwsFeatureId, None] = {}

    with _credential_sources(monkeypatch):
        await _resolve(named, {"_feature_ids": features})

    # The resolver's own feature, for when it's used directly, isn't recorded.
    assert features == {AwsFeatureId.CREDENTIALS_PROFILE: None}


@_MODES
@pytest.mark.parametrize("provider_feature_ids", [(), None])
async def test_chain_keeps_resolver_feature_ids_when_provider_has_none(
    sync: bool, provider_feature_ids: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    named = _named(sync, _create(sync, "environment")(), provider_feature_ids)
    features: dict[AwsFeatureId, None] = {}

    with _credential_sources(monkeypatch):
        await _resolve(named, {"_feature_ids": features})

    assert features == {AwsFeatureId.CREDENTIALS_ENV_VARS: None}


@_MODES
async def test_resolving_without_a_feature_record_records_nothing(
    sync: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    named = _named(
        sync, _create(sync, "environment")(), (AwsFeatureId.CREDENTIALS_PROFILE,)
    )

    with _credential_sources(monkeypatch):
        identity = await _resolve(named, {})

    assert identity.access_key_id == "akid"
