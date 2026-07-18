# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from smithy_python.cli import main
from smithy_python.settings import PluginEnvironment


def test_cli_generates_from_model_and_settings_files(
    model_document: dict[str, Any], tmp_path: Path
) -> None:
    model_path = tmp_path / "model.json"
    settings_path = tmp_path / "settings.json"
    output_path = tmp_path / "generated"
    model_path.write_text(json.dumps(model_document))
    settings_path.write_text(
        json.dumps({"module": "weather_types", "moduleVersion": "1.0.0"})
    )

    assert (
        main(
            (
                "generate",
                "types",
                "--model",
                str(model_path),
                "--settings",
                f"@{settings_path}",
                "--output",
                str(output_path),
                "--no-format",
            )
        )
        == 0
    )
    assert (output_path / "src" / "weather_types" / "models.py").is_file()


def test_reads_smithy_run_plugin_environment() -> None:
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
