# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path

import pytest
from smithy_python.cli import main


@pytest.mark.parametrize("artifact", ["client", "types"])
@pytest.mark.parametrize(
    ("service", "expected", "diagnostic"),
    [
        (None, 2, "example#First, example#Second"),
        ("example#Second", 1, "generation is not implemented yet"),
        ("Second", 2, "absolute"),
        ("example##Second", 2, "shape ID"),
        (" example#Second", 2, "shape ID"),
        ("example#Missing", 2, "is not defined"),
        ("example#Data", 2, "is not a service"),
        ("example#Data$value", 2, "is a member"),
        ("example#Base", 2, "is a mixin"),
        ("", 2, "shape ID"),
    ],
)
def test_cli_service_selection(
    artifact: str,
    service: str | None,
    expected: int,
    diagnostic: str,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source = json.dumps(
        {
            "smithy": "2.0",
            "shapes": {
                "example#First": {"type": "service"},
                "example#Second": {"type": "service"},
                "example#Base": {
                    "type": "service",
                    "traits": {"smithy.api#mixin": {}},
                },
                "example#Data": {
                    "type": "structure",
                    "members": {"value": {"target": "smithy.api#String"}},
                },
            },
        }
    ).encode()
    output = tmp_path / "output"
    argv = ["generate", artifact, "--output", str(output)]
    if service is not None:
        argv.extend(("--service", service))
    assert main(argv, environ={}, stdin=BytesIO(source)) == expected
    captured = capsys.readouterr()
    assert captured.out == ""
    assert diagnostic in captured.err
    assert "unrecognized arguments" not in captured.err
    if service is None:
        assert "example#Base" not in captured.err
    if expected == 2:
        assert "not implemented" not in captured.err
    assert not output.exists()


@pytest.mark.parametrize("artifact", ["client", "types"])
@pytest.mark.parametrize("has_service", [False, True])
def test_cli_implicit_service(
    artifact: str,
    has_service: bool,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    shapes: dict[str, object] = {
        "example#Base": {"type": "service", "traits": {"smithy.api#mixin": {}}}
    }
    if has_service:
        shapes["example#Service"] = {"type": "service"}
    source = json.dumps({"smithy": "2.0", "shapes": shapes}).encode()
    requires_service = artifact == "client" and not has_service
    assert main(
        ("generate", artifact),
        environ={"SMITHY_PLUGIN_DIR": str(tmp_path / "output")},
        stdin=BytesIO(source),
    ) == (2 if requires_service else 1)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert ("not implemented" in captured.err) is not requires_service
    if requires_service:
        assert "service" in captured.err
    assert not (tmp_path / "output").exists()


@pytest.mark.parametrize("artifact", ["client", "types"])
@pytest.mark.parametrize("plugin", [False, True])
def test_cli_reports_only_excluded_eligible_data(
    artifact: str,
    plugin: bool,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source = json.dumps(
        {
            "smithy": "2.0",
            "shapes": {
                "example#Service": {"type": "service"},
                "example#Unused": {"type": "string"},
                "example#Trait": {
                    "type": "structure",
                    "traits": {"smithy.api#trait": {}},
                },
                "example#Mixin": {
                    "type": "structure",
                    "traits": {"smithy.api#mixin": {}},
                },
                "example#Operation": {"type": "operation"},
                "example#Resource": {"type": "resource"},
            },
        }
    ).encode()
    output = tmp_path / "output"
    argv = ["generate", artifact, "--service", "example#Service"]
    environ = {"SMITHY_PLUGIN_DIR": str(output)} if plugin else {}
    if not plugin:
        argv.extend(("--output", str(output)))
    assert main(argv, environ=environ, stdin=BytesIO(source)) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == (
        "smithy-python: excluded 1 eligible data shape(s) "
        "outside the closure of service example#Service\n"
        f"smithy-python: error: {artifact} generation is not implemented yet\n"
    )
    assert not output.exists()


def test_cli_conflicts_are_model_errors(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = json.dumps(
        {
            "smithy": "2.0",
            "shapes": {
                shape_id: {"type": "string"}
                for shape_id in ("a#Name", "b#name", "c#NAME", "a#Other", "b#other")
            },
        }
    ).encode()
    output = tmp_path / "output"
    assert (
        main(
            ("generate", "types", "--output", str(output)),
            environ={},
            stdin=BytesIO(source),
        )
        == 1
    )
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "not implemented" not in captured.err
    for shape_id in ("a#Name", "b#name", "c#NAME", "a#Other", "b#other"):
        assert shape_id in captured.err
    assert not output.exists()
