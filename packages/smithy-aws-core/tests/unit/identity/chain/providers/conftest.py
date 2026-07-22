#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from collections.abc import Awaitable, Callable, Mapping
from typing import Any

import pytest
from smithy_aws_core.config.file_parser import Section, StandardizedOutput
from smithy_aws_core.config.merged_config import MergedConfig
from smithy_aws_core.identity import AWSCredentialsIdentity
from smithy_aws_core.identity.chain.provider import ChainSetup
from smithy_core.interfaces.identity import Identity


class OtherIdentity(Identity):
    """A non-AWS identity type used to verify providers ignore unknown types."""


@pytest.fixture
def merged_config() -> Callable[..., MergedConfig]:
    def _build(
        profiles: Mapping[str, Mapping[str, str]] | None = None,
    ) -> MergedConfig:
        sections = {
            name: Section(properties=dict(properties))
            for name, properties in (profiles or {}).items()
        }
        return MergedConfig(StandardizedOutput(profiles=sections), StandardizedOutput())

    return _build


@pytest.fixture
def setup_provider() -> Callable[..., Awaitable[ChainSetup]]:
    async def _setup(
        provider: Any,
        *,
        identity_type: type[Identity] = AWSCredentialsIdentity,
        profile: Section | None = None,
        profile_file: MergedConfig | None = None,
        profile_name_override: str | None = None,
    ) -> ChainSetup:
        setup = ChainSetup(
            profile_file=profile_file,
            profile_name_override=profile_name_override,
        )
        setup.set_current_provider(provider)
        if profile is not None:
            setup.set_profile(profile)
        await provider.setup(identity_type, setup)
        return setup

    return _setup
