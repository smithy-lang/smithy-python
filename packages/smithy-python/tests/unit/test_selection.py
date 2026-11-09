# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path

import pytest
from smithy_python.cli import main

_TYPES_OPTIONS = ("--package", "example_types", "--package-version", "1.0.0")


def _artifact_args(artifact: str, *options: str) -> list[str]:
    args = ["generate", artifact]
    if artifact == "types":
        args.extend(_TYPES_OPTIONS)
    args.extend(options)
    return args


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
    argv = _artifact_args(artifact, "--output", str(output))
    if service is not None:
        argv.extend(("--service", service))
    if artifact == "types" and service in (None, "example#Second"):
        expected = 0
        diagnostic = (
            ""
            if service is None
            else "excluded 1 eligible data shape(s) outside the closure"
        )
    assert main(argv, environ={}, stdin=BytesIO(source)) == expected
    captured = capsys.readouterr()
    assert captured.out == ""
    if diagnostic:
        assert diagnostic in captured.err
    else:
        assert captured.err == ""
    assert "unrecognized arguments" not in captured.err
    if service is None:
        assert "example#Base" not in captured.err
    if expected == 2:
        assert "not implemented" not in captured.err
    assert output.exists() is (expected == 0)


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
    argv = _artifact_args(artifact)
    expected = 0 if artifact == "types" else 1 if has_service else 2
    assert (
        main(
            argv,
            environ={"SMITHY_PLUGIN_DIR": str(tmp_path / "output")},
            stdin=BytesIO(source),
        )
        == expected
    )
    captured = capsys.readouterr()
    assert captured.out == ""
    assert ("not implemented" in captured.err) is (artifact == "client" and has_service)
    if artifact == "client" and not has_service:
        assert "service" in captured.err
    assert (tmp_path / "output").exists() is (artifact == "types")


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
    argv = _artifact_args(artifact, "--service", "example#Service")
    environ = {"SMITHY_PLUGIN_DIR": str(output)} if plugin else {}
    if not plugin:
        argv.extend(("--output", str(output)))
    assert main(argv, environ=environ, stdin=BytesIO(source)) == (
        0 if artifact == "types" else 1
    )
    captured = capsys.readouterr()
    assert captured.out == ""
    expected = ""
    if artifact == "client":
        expected = (
            "smithy-python: excluded 1 eligible data shape(s) "
            "outside the closure of service example#Service\n"
            "smithy-python: error: client generation is not implemented yet\n"
        )
    assert captured.err == expected
    assert output.exists() is (artifact == "types")


def test_cli_conflicts_are_model_errors(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = json.dumps(
        {
            "smithy": "2.0",
            "shapes": {
                shape_id: {"type": "structure"}
                for shape_id in ("a#Name", "b#name", "c#NAME", "a#Other", "b#other")
            },
        }
    ).encode()
    output = tmp_path / "output"
    assert (
        main(
            _artifact_args("types", "--output", str(output)),
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
