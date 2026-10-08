# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

import pytest
from smithy_python.environment import PluginEnvironment


def test_loads_run_plugin_environment() -> None:
    environment = PluginEnvironment.from_environ(
        {
            "SMITHY_ROOT_DIR": "/tmp/root",
            "SMITHY_PLUGIN_DIR": "/tmp/plugin",
            "SMITHY_PROJECTION_NAME": "client",
            "SMITHY_ARTIFACT_NAME": "python-client",
            "SMITHY_INCLUDES_PRELUDE": "true",
        }
    )

    assert environment.root_dir == Path("/tmp/root")
    assert environment.plugin_dir == Path("/tmp/plugin")
    assert environment.projection_name == "client"
    assert environment.artifact_name == "python-client"
    assert environment.includes_prelude


def test_defaults_to_direct_invocation() -> None:
    environment = PluginEnvironment.from_environ({})

    assert environment.root_dir is None
    assert environment.plugin_dir is None
    assert environment.projection_name is None
    assert environment.artifact_name is None
    assert not environment.includes_prelude


def test_loads_os_environment_by_default(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("SMITHY_PLUGIN_DIR", str(tmp_path))

    assert PluginEnvironment.from_environ().plugin_dir == tmp_path
