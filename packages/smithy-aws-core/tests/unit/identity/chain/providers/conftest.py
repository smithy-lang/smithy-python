#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from collections.abc import Awaitable, Callable, Mapping
from inspect import isawaitable
from typing import Any

import pytest
from smithy_aws_core.aio.identity.chain.provider import AsyncChainSetup
from smithy_aws_core.config.file_parser import Section, StandardizedOutput
from smithy_aws_core.config.merged_config import MergedConfig
from smithy_aws_core.identity import AWSCredentialsIdentity
from smithy_core.interfaces.identity import Identity


class OtherIdentity(Identity):
    """A non-AWS identity type used to verify providers ignore unknown types."""


@pytest.fixture
def merged_config() -> Callable[..., MergedConfig]:
    """Build merged config for provider tests."""

    def _build(
        profiles: Mapping[str, Mapping[str, str | dict[str, str]]] | None = None,
    ) -> MergedConfig:
        sections = {
            name: Section(properties=dict(properties))
            for name, properties in (profiles or {}).items()
        }
        return MergedConfig(StandardizedOutput(profiles=sections), StandardizedOutput())

    return _build


@pytest.fixture
def setup_provider() -> Callable[..., Awaitable[AsyncChainSetup]]:
    """Setup a provider with a configured AsyncChainSetup."""

    async def _setup(
        provider: Any,
        *,
        identity_type: type[Identity] = AWSCredentialsIdentity,
        config_file: MergedConfig | None = None,
        profile_name: str | None = None,
    ) -> AsyncChainSetup:
        setup = AsyncChainSetup(
            config_file=config_file,
            profile_name=profile_name,
        )
        setup.set_current_provider(provider)
        if isawaitable(result := provider.setup(identity_type, setup)):
            await result
        return setup

    return _setup
