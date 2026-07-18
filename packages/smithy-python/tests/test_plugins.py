# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import pytest
from smithy_python import GeneratorPlugin, PluginError, PluginRegistry


class First(GeneratorPlugin):
    name = "first"
    before = ("second",)


class Second(GeneratorPlugin):
    name = "second"


class Third(GeneratorPlugin):
    name = "third"
    after = ("second",)


def test_plugins_are_topologically_ordered_stably() -> None:
    registry = PluginRegistry((Third(), Second(), First()))
    assert [plugin.name for plugin in registry.plugins] == ["first", "second", "third"]


def test_plugin_cycles_are_rejected() -> None:
    class Left(GeneratorPlugin):
        name = "left"
        after = ("right",)

    class Right(GeneratorPlugin):
        name = "right"
        after = ("left",)

    with pytest.raises(PluginError, match="cycle"):
        PluginRegistry((Left(), Right()))
