#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from unittest.mock import AsyncMock

import pytest
from smithy_aws_core.config.file_parser import StandardizedOutput
from smithy_aws_core.config.merged_config import MergedConfig
from smithy_aws_core.identity.chain.ordering import Standard, StandardProvider
from smithy_aws_core.identity.chain.provider import ChainSetup
from smithy_core.interfaces.identity import Identity


class _FakeProvider:
    def __init__(self, name: str = "Environment") -> None:
        self.name = name
        self.ordering = Standard(slot=StandardProvider.ENVIRONMENT)

    async def setup(self, identity_type: type[Identity], setup: ChainSetup) -> None:
        pass


def _empty_config() -> MergedConfig:
    return MergedConfig(StandardizedOutput(), StandardizedOutput())


def test_add_resolver_tags_with_current_provider() -> None:
    resolver = AsyncMock()
    setup = ChainSetup()
    setup.set_current_provider(_FakeProvider("Environment"))

    setup.add_resolver(resolver)

    assert len(setup.resolvers) == 1
    assert setup.resolvers[0].resolver is resolver
    assert setup.resolvers[0].provider_name == "Environment"
    assert not setup.terminal


def test_add_resolver_stacks_multiple() -> None:
    first, second = AsyncMock(), AsyncMock()
    setup = ChainSetup()
    setup.set_current_provider(_FakeProvider())

    setup.add_resolver(first)
    setup.add_resolver(second)

    assert [r.resolver for r in setup.resolvers] == [first, second]
    assert not setup.terminal


def test_add_terminal_resolver_stops_assembly() -> None:
    setup = ChainSetup()
    setup.set_current_provider(_FakeProvider())

    setup.add_terminal_resolver(AsyncMock())

    assert setup.terminal
    with pytest.raises(
        RuntimeError, match="Cannot add a resolver after a terminal resolver"
    ):
        setup.add_resolver(AsyncMock())


def test_cannot_change_provider_after_terminal() -> None:
    setup = ChainSetup()
    setup.set_current_provider(_FakeProvider())
    setup.add_terminal_resolver(AsyncMock())

    with pytest.raises(
        RuntimeError, match="Cannot change provider after a terminal resolver"
    ):
        setup.set_current_provider(_FakeProvider())


def test_cannot_add_without_current_provider() -> None:
    setup = ChainSetup()

    with pytest.raises(
        RuntimeError, match="Cannot add a resolver without a current provider"
    ):
        setup.add_resolver(AsyncMock())


def test_set_profile_file_cannot_overwrite() -> None:
    setup = ChainSetup(profile_file=_empty_config())

    with pytest.raises(
        RuntimeError, match="Cannot overwrite a profile file already present"
    ):
        setup.set_profile_file(_empty_config())


def test_properties_bag_is_shared_and_mutable() -> None:
    setup = ChainSetup()

    setup.properties["key"] = "value"

    assert setup.properties["key"] == "value"
