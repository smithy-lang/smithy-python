# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import subprocess
import sys
from io import BytesIO
from pathlib import Path
from typing import Any

import pytest
from smithy_python import __version__
from smithy_python.cli import main

from .conftest import CliRunner


class _InteractiveStdin(BytesIO):
    def isatty(self) -> bool:
        return True


@pytest.mark.parametrize(
    ("argv", "expected"),
    [
        (("--help",), "usage: smithy-python"),
        (("--version",), f"smithy-python {__version__}"),
    ],
)
def test_information_commands(
    argv: tuple[str, ...], expected: str, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(argv) == 0
    assert capsys.readouterr().out.startswith(expected)


@pytest.mark.parametrize("artifact", ["client", "types"])
def test_generation_commands_are_explicitly_unavailable(
    artifact: str, model_json: bytes, tmp_path: Path, run_cli: CliRunner
) -> None:
    model = tmp_path / "model.json"
    model.write_bytes(model_json)

    exit_code, stderr = run_cli(
        "generate",
        artifact,
        "--model",
        str(model),
        "--output",
        str(tmp_path / "output"),
    )

    assert exit_code == 1
    assert stderr.endswith(
        f"smithy-python: error: {artifact} generation is not implemented yet\n"
    )


@pytest.mark.parametrize(
    ("argv", "expected_usage"),
    [
        ((), "usage: smithy-python"),
        (("generate",), "usage: smithy-python generate"),
    ],
)
def test_missing_command_identifies_available_subcommands(
    argv: tuple[str, ...], expected_usage: str, run_cli: CliRunner
) -> None:
    exit_code, stderr = run_cli(*argv)

    assert exit_code == 2
    assert stderr.startswith(expected_usage)


def test_main_module_invokes_cli() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "smithy_python", "--version"],
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode == 0
    assert result.stdout == f"smithy-python {__version__}\n"
    assert result.stderr == ""


def test_run_plugin_invocation_reads_standard_input(
    model_json: bytes, tmp_path: Path, run_cli: CliRunner
) -> None:
    exit_code, stderr = run_cli(
        "generate",
        "client",
        environ={"SMITHY_PLUGIN_DIR": str(tmp_path)},
        stdin=model_json,
    )

    assert exit_code == 1
    assert "generation is not implemented yet" in stderr


@pytest.mark.parametrize("option", ["--model", "--output"])
def test_run_plugin_rejects_direct_invocation_options(
    option: str, tmp_path: Path, run_cli: CliRunner
) -> None:
    exit_code, stderr = run_cli(
        "generate",
        "client",
        option,
        str(tmp_path / "value"),
        environ={"SMITHY_PLUGIN_DIR": str(tmp_path)},
        stdin=b"{}",
    )

    assert exit_code == 2
    assert f"{option} cannot be used with the Smithy run plugin" in stderr


def test_direct_invocation_requires_output(tmp_path: Path, run_cli: CliRunner) -> None:
    model = tmp_path / "model.json"
    model.write_text("{}")

    exit_code, stderr = run_cli("generate", "client", "--model", str(model))

    assert exit_code == 2
    assert "Direct invocation requires --output" in stderr


def test_invocation_rejects_empty_model(tmp_path: Path, run_cli: CliRunner) -> None:
    exit_code, stderr = run_cli(
        "generate", "client", "--output", str(tmp_path), stdin=b""
    )

    assert exit_code == 2
    assert "Expected a Smithy JSON AST model" in stderr


def test_direct_invocation_rejects_interactive_model_input(
    tmp_path: Path, run_cli: CliRunner
) -> None:
    exit_code, stderr = run_cli(
        "generate", "client", "--output", str(tmp_path), stdin=_InteractiveStdin()
    )

    assert exit_code == 2
    assert (
        "Direct invocation requires --model or a model piped to standard input"
        in stderr
    )


def test_invocation_reports_unreadable_model(
    tmp_path: Path, run_cli: CliRunner
) -> None:
    missing = tmp_path / "missing.json"

    exit_code, stderr = run_cli(
        "generate", "client", "--model", str(missing), "--output", str(tmp_path)
    )

    assert exit_code == 2
    assert f"Model path is not a file: {missing}" in stderr


def test_invocation_rejects_empty_model_path(
    tmp_path: Path, run_cli: CliRunner
) -> None:
    exit_code, stderr = run_cli(
        "generate", "client", "--model", "", "--output", str(tmp_path)
    )

    assert exit_code == 2
    assert "Model path is not a file: ." in stderr


def test_invocation_reports_model_io_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, run_cli: CliRunner
) -> None:
    model = tmp_path / "model.json"
    model.write_text("{}")

    def raise_io_error(self: Path) -> bytes:
        raise OSError("unable to read model")

    monkeypatch.setattr(Path, "read_bytes", raise_io_error)

    exit_code, stderr = run_cli(
        "generate", "client", "--model", str(model), "--output", str(tmp_path)
    )

    assert exit_code == 1
    assert "unable to read model" in stderr


def test_help_documents_service_option(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(("generate", "client", "--help")) == 0
    assert "--service SHAPE_ID" in capsys.readouterr().out


def test_invalid_model_is_a_generation_failure(
    tmp_path: Path, run_cli: CliRunner
) -> None:
    exit_code, stderr = run_cli(
        "generate", "types", "--output", str(tmp_path), stdin=b"{}"
    )

    assert exit_code == 1
    assert "missing a string 'smithy' version" in stderr


def test_client_requires_a_service(tmp_path: Path, run_cli: CliRunner) -> None:
    exit_code, stderr = run_cli(
        "generate", "client", "--output", str(tmp_path), stdin=b'{"smithy": "2.0"}'
    )

    assert exit_code == 2
    assert "does not contain a service" in stderr


def test_types_does_not_require_a_service(tmp_path: Path, run_cli: CliRunner) -> None:
    exit_code, stderr = run_cli(
        "generate", "types", "--output", str(tmp_path), stdin=b'{"smithy": "2.0"}'
    )

    assert exit_code == 1
    assert "types generation is not implemented yet" in stderr


def test_multiple_services_require_service_option(
    model_document: dict[str, Any], tmp_path: Path, run_cli: CliRunner
) -> None:
    model_document["shapes"]["example.other#Other"] = {
        "type": "service",
        "version": "1",
    }
    source = json.dumps(model_document).encode()

    exit_code, stderr = run_cli(
        "generate", "client", "--output", str(tmp_path), stdin=source
    )
    assert exit_code == 2
    assert "select one with --service" in stderr

    exit_code, stderr = run_cli(
        "generate",
        "client",
        "--output",
        str(tmp_path),
        "--service",
        "example.weather#Weather",
        stdin=source,
    )
    assert exit_code == 1
    assert "client generation is not implemented yet" in stderr


@pytest.mark.parametrize(
    ("value", "message"),
    [
        ("Weather", "Invalid --service value"),
        ("example.weather#Weather$member", "not a member"),
        ("example.weather#Nope", "Service not found"),
        ("example.weather#Coordinates", "Expected a service shape"),
    ],
)
def test_invalid_service_option_is_an_invocation_error(
    value: str,
    message: str,
    model_json: bytes,
    tmp_path: Path,
    run_cli: CliRunner,
) -> None:
    exit_code, stderr = run_cli(
        "generate",
        "client",
        "--output",
        str(tmp_path),
        "--service",
        value,
        stdin=model_json,
    )

    assert exit_code == 2
    assert message in stderr


def test_unconnected_shapes_are_reported(
    model_json: bytes, tmp_path: Path, run_cli: CliRunner
) -> None:
    exit_code, stderr = run_cli(
        "generate", "client", "--output", str(tmp_path), stdin=model_json
    )

    assert exit_code == 1
    assert (
        "note: 1 shape(s) not connected to example.weather#Weather will not be "
        "generated"
    ) in stderr


def test_shape_name_conflicts_are_a_generation_failure(
    model_document: dict[str, Any], tmp_path: Path, run_cli: CliRunner
) -> None:
    del model_document["shapes"]["example.weather#Weather"]
    model_document["shapes"]["example.other#coordinates"] = {"type": "string"}

    exit_code, stderr = run_cli(
        "generate",
        "types",
        "--output",
        str(tmp_path),
        stdin=json.dumps(model_document).encode(),
    )

    assert exit_code == 1
    assert "case-insensitively unique" in stderr
