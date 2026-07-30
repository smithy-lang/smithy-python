#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from collections.abc import Awaitable, Callable
from unittest.mock import AsyncMock

import pytest
from smithy_aws_core.config.merged_config import MergedConfig
from smithy_aws_core.identity.chain.provider import ChainSetup
from smithy_aws_core.identity.chain.providers import (
    shared_config as shared_config_module,
)
from smithy_aws_core.identity.chain.providers.shared_config import SharedConfigProvider

from .conftest import OtherIdentity


async def test_ignores_non_aws_identity_type(
    setup_provider: Callable[..., Awaitable[ChainSetup]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    load_config = AsyncMock()
    monkeypatch.setattr(shared_config_module, "load_config", load_config)

    setup = await setup_provider(SharedConfigProvider(), identity_type=OtherIdentity)

    assert setup.resolvers == ()
    assert not setup.terminal
    load_config.assert_not_awaited()


# profile selection precedence: profile_name_override wins over the AWS_PROFILE
# env var (environment_profile), which wins over the "default" fallback.
@pytest.mark.parametrize(
    "profile_name_override, environment_profile, expected",
    [
        ("override", "environment", "override"),
        (None, "environment", "environment"),
        (None, None, "default"),
    ],
)
async def test_selects_profile_without_reloading(
    profile_name_override: str | None,
    environment_profile: str | None,
    expected: str,
    setup_provider: Callable[..., Awaitable[ChainSetup]],
    merged_config: Callable[..., MergedConfig],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile_file = merged_config(
        {
            "override": {"name": "override"},
            "environment": {"name": "environment"},
            "default": {"name": "default"},
        }
    )
    if environment_profile is None:
        monkeypatch.delenv("AWS_PROFILE", raising=False)
    else:
        monkeypatch.setenv("AWS_PROFILE", environment_profile)
    load_config = AsyncMock()
    monkeypatch.setattr(shared_config_module, "load_config", load_config)

    setup = await setup_provider(
        SharedConfigProvider(),
        profile_file=profile_file,
        profile_name_override=profile_name_override,
    )

    assert setup.profile_file is profile_file
    assert setup.profile is profile_file.get_profile(expected)
    assert setup.resolvers == ()
    load_config.assert_not_awaited()


async def test_loads_when_not_preloaded(
    setup_provider: Callable[..., Awaitable[ChainSetup]],
    merged_config: Callable[..., MergedConfig],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    loaded = merged_config({"default": {"name": "loaded"}})
    load_config = AsyncMock(return_value=loaded)
    monkeypatch.setattr(shared_config_module, "load_config", load_config)
    monkeypatch.delenv("AWS_PROFILE", raising=False)

    setup = await setup_provider(SharedConfigProvider())

    assert setup.profile_file is loaded
    assert setup.profile is loaded.get_profile("default")
    assert setup.resolvers == ()
    load_config.assert_awaited_once_with()


async def test_leaves_missing_profile_unset(
    setup_provider: Callable[..., Awaitable[ChainSetup]],
    merged_config: Callable[..., MergedConfig],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    load_config = AsyncMock()
    monkeypatch.setattr(shared_config_module, "load_config", load_config)

    setup = await setup_provider(
        SharedConfigProvider(),
        profile_file=merged_config(),
        profile_name_override="missing",
    )

    assert setup.profile is None
    load_config.assert_not_awaited()
