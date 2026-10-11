#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from collections.abc import Awaitable, Callable

import pytest
from smithy_aws_core.identity.chain.provider import ChainSetup
from smithy_aws_core.identity.chain.providers.environment import (
    EnvironmentCredentialsProvider,
)
from smithy_aws_core.identity.environment import EnvironmentCredentialsResolver

from .conftest import OtherIdentity


async def test_ignores_non_aws_identity_type(
    setup_provider: Callable[..., Awaitable[ChainSetup]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "akid")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")

    setup = await setup_provider(
        EnvironmentCredentialsProvider(), identity_type=OtherIdentity
    )

    assert setup.resolvers == ()
    assert not setup.terminal


@pytest.mark.parametrize(
    "environment",
    [
        {},
        {"AWS_ACCESS_KEY_ID": "akid"},
        {"AWS_SECRET_ACCESS_KEY": "secret"},
    ],
)
async def test_requires_both_keys(
    environment: dict[str, str],
    setup_provider: Callable[..., Awaitable[ChainSetup]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)
    for name, value in environment.items():
        monkeypatch.setenv(name, value)

    setup = await setup_provider(EnvironmentCredentialsProvider())

    assert setup.resolvers == ()
    assert not setup.terminal


async def test_registers_terminal_resolver(
    setup_provider: Callable[..., Awaitable[ChainSetup]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "akid")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")

    setup = await setup_provider(EnvironmentCredentialsProvider())

    assert setup.terminal
    assert len(setup.resolvers) == 1
    assert setup.resolvers[0].provider_name == "Environment"
    assert isinstance(setup.resolvers[0].resolver, EnvironmentCredentialsResolver)


async def test_explicit_profile_suppresses_environment_credentials(
    setup_provider: Callable[..., Awaitable[ChainSetup]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "akid")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")

    setup = await setup_provider(
        EnvironmentCredentialsProvider(),
        profile_name="work",
    )

    assert setup.resolvers == ()
    assert not setup.terminal


async def test_aws_profile_env_var_does_not_suppress_environment_credentials(
    setup_provider: Callable[..., Awaitable[ChainSetup]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AWS_PROFILE", "work")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "akid")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")

    setup = await setup_provider(EnvironmentCredentialsProvider())

    assert setup.terminal
    assert len(setup.resolvers) == 1
    assert isinstance(setup.resolvers[0].resolver, EnvironmentCredentialsResolver)
