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
    artifact: str,
    model_json: bytes,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    model = tmp_path / "model.json"
    model.write_bytes(model_json)

    assert (
        main(
            (
                "generate",
                artifact,
                "--model",
                str(model),
                "--output",
                str(tmp_path / "output"),
            ),
            environ={},
        )
        == 1
    )
    assert capsys.readouterr().err == (
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
    argv: tuple[str, ...],
    expected_usage: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(argv) == 2
    assert capsys.readouterr().err.startswith(expected_usage)


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
    model_json: bytes, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert (
        main(
            ("generate", "client"),
            environ={"SMITHY_PLUGIN_DIR": str(tmp_path)},
            stdin=BytesIO(model_json),
        )
        == 1
    )
    assert "generation is not implemented yet" in capsys.readouterr().err


@pytest.mark.parametrize("option", ["--model", "--output"])
def test_run_plugin_rejects_direct_invocation_options(
    option: str,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert (
        main(
            ("generate", "client", option, str(tmp_path / "value")),
            environ={"SMITHY_PLUGIN_DIR": str(tmp_path)},
            stdin=BytesIO(b"{}"),
        )
        == 2
    )
    assert f"{option} cannot be used with the Smithy run plugin" in (
        capsys.readouterr().err
    )


def test_direct_invocation_requires_output(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    model = tmp_path / "model.json"
    model.write_text("{}")

    assert main(("generate", "client", "--model", str(model)), environ={}) == 2
    assert "Direct invocation requires --output" in capsys.readouterr().err


def test_invocation_rejects_empty_model(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert (
        main(
            ("generate", "client", "--output", str(tmp_path)),
            environ={},
            stdin=BytesIO(),
        )
        == 2
    )
    assert "Expected a Smithy JSON AST model" in capsys.readouterr().err


def test_direct_invocation_rejects_interactive_model_input(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert (
        main(
            ("generate", "client", "--output", str(tmp_path)),
            environ={},
            stdin=_InteractiveStdin(),
        )
        == 2
    )
    assert (
        "Direct invocation requires --model or a model piped to standard input"
        in capsys.readouterr().err
    )


def test_invocation_reports_unreadable_model(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    missing = tmp_path / "missing.json"

    assert (
        main(
            (
                "generate",
                "client",
                "--model",
                str(missing),
                "--output",
                str(tmp_path),
            ),
            environ={},
        )
        == 2
    )
    assert f"Model path is not a file: {missing}" in capsys.readouterr().err


def test_invocation_rejects_empty_model_path(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert (
        main(
            (
                "generate",
                "client",
                "--model",
                "",
                "--output",
                str(tmp_path),
            ),
            environ={},
        )
        == 2
    )
    assert "Model path is not a file: ." in capsys.readouterr().err


def test_invocation_reports_model_io_error(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    model = tmp_path / "model.json"
    model.write_text("{}")

    def raise_io_error(self: Path) -> bytes:
        raise OSError("unable to read model")

    monkeypatch.setattr(Path, "read_bytes", raise_io_error)

    assert (
        main(
            (
                "generate",
                "client",
                "--model",
                str(model),
                "--output",
                str(tmp_path),
            ),
            environ={},
        )
        == 1
    )
    assert "unable to read model" in capsys.readouterr().err


def test_help_documents_service_option(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(("generate", "client", "--help")) == 0
    assert "--service SHAPE_ID" in capsys.readouterr().out


def test_invalid_model_is_a_generation_failure(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert (
        main(
            ("generate", "types", "--output", str(tmp_path)),
            environ={},
            stdin=BytesIO(b"{}"),
        )
        == 1
    )
    assert "missing a string 'smithy' version" in capsys.readouterr().err


def test_client_requires_a_service(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert (
        main(
            ("generate", "client", "--output", str(tmp_path)),
            environ={},
            stdin=BytesIO(b'{"smithy": "2.0"}'),
        )
        == 2
    )
    assert "does not contain a service" in capsys.readouterr().err


def test_types_does_not_require_a_service(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert (
        main(
            ("generate", "types", "--output", str(tmp_path)),
            environ={},
            stdin=BytesIO(b'{"smithy": "2.0"}'),
        )
        == 1
    )
    assert "types generation is not implemented yet" in capsys.readouterr().err


def test_multiple_services_require_service_option(
    model_document: dict[str, Any],
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    model_document["shapes"]["example.other#Other"] = {
        "type": "service",
        "version": "1",
    }
    source = json.dumps(model_document).encode()

    assert (
        main(
            ("generate", "client", "--output", str(tmp_path)),
            environ={},
            stdin=BytesIO(source),
        )
        == 2
    )
    assert "select one with --service" in capsys.readouterr().err

    assert (
        main(
            (
                "generate",
                "client",
                "--output",
                str(tmp_path),
                "--service",
                "example.weather#Weather",
            ),
            environ={},
            stdin=BytesIO(source),
        )
        == 1
    )
    assert "client generation is not implemented yet" in capsys.readouterr().err


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
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert (
        main(
            ("generate", "client", "--output", str(tmp_path), "--service", value),
            environ={},
            stdin=BytesIO(model_json),
        )
        == 2
    )
    assert message in capsys.readouterr().err


def test_shape_name_conflicts_are_a_generation_failure(
    model_document: dict[str, Any],
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    model_document["shapes"]["example.other#coordinates"] = {"type": "string"}

    assert (
        main(
            ("generate", "types", "--output", str(tmp_path)),
            environ={},
            stdin=BytesIO(json.dumps(model_document).encode()),
        )
        == 1
    )
    assert "case-insensitively unique" in capsys.readouterr().err
