# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import importlib
import json
import subprocess
import sys
import tomllib
from io import BytesIO
from pathlib import Path

import pytest
from smithy_python import __version__
from smithy_python.cli import main

VALID_MODEL = '{"smithy": "2.0", "shapes": {"example#Service": {"type": "service"}}}'


class _InteractiveStdin(BytesIO):
    def isatty(self) -> bool:
        return True


def _types_args(
    output: Path,
    *options: str,
    package: str = "example_types",
    version: str = "1.2.3",
) -> tuple[str, ...]:
    args = ("generate", "types", "--output", str(output))
    return (*args, "--package", package, "--package-version", version, *options)


def _run_types(
    output: Path,
    *options: str,
    source: bytes = VALID_MODEL.encode(),
    package: str = "example_types",
    version: str = "1.2.3",
) -> int:
    args = _types_args(output, *options, package=package, version=version)
    return main(args, environ={}, stdin=BytesIO(source))


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


def test_client_generation_is_explicitly_unavailable(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    model = tmp_path / "model.json"
    model.write_text(VALID_MODEL)

    assert (
        main(
            (
                "generate",
                "client",
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
        "smithy-python: error: client generation is not implemented yet\n"
    )


def test_types_generation_writes_complete_package(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = tmp_path / "model.json"
    model.write_text(
        '{"smithy": "2.0", "shapes": {"example#Data": {"type": "structure"}}}'
    )
    output = tmp_path / "output"

    assert _run_types(output, "--model", str(model)) == 0
    assert capsys.readouterr().err == ""
    assert {
        path.relative_to(output).as_posix()
        for path in output.rglob("*")
        if path.is_file()
    } == {
        ".smithy-python-manifest.json",
        "README.md",
        "pyproject.toml",
        "src/example_types/__init__.py",
        "src/example_types/_private/__init__.py",
        "src/example_types/_private/schemas.py",
        "src/example_types/models.py",
        "src/example_types/models.pyi",
        "src/example_types/py.typed",
    }
    project = tomllib.loads((output / "pyproject.toml").read_text())
    assert project["project"] == {
        "name": "example_types",
        "version": "1.2.3",
        "description": "example_types types package",
        "readme": "README.md",
        "requires-python": ">=3.12",
        "keywords": ["smithy", "example_types"],
        "license": {"text": "Apache-2.0"},
        "dependencies": ["smithy-core~=0.10.0"],
    }
    assert project["build-system"] == {
        "requires": ["hatchling"],
        "build-backend": "hatchling.build",
    }
    monkeypatch.syspath_prepend(  # pyright: ignore[reportUnknownMemberType]
        str(output / "src")
    )
    package = importlib.import_module("example_types")
    models = importlib.import_module("example_types.models")
    assert package.__version__ == "1.2.3"
    assert models.Data.__module__ == "example_types.models"


def test_types_generation_escapes_del_in_toml_metadata(tmp_path: Path) -> None:
    output = tmp_path / "output"
    description = "before\x7fafter"

    assert _run_types(output, "--package-description", description) == 0
    pyproject = (output / "pyproject.toml").read_text()
    assert "\\u007f" in pyproject
    assert tomllib.loads(pyproject)["project"]["description"] == description


def test_types_generation_applies_selector_and_input_output_settings(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source = json.dumps(
        {
            "smithy": "2.0",
            "shapes": {
                "example#Operation": {
                    "type": "operation",
                    "input": {"target": "example#Input"},
                    "output": {"target": "example#Output"},
                },
                "example#Input": {"type": "structure"},
                "example#Output": {"type": "structure"},
                "example#Selected": {"type": "structure"},
                "example#Excluded": {"type": "structure"},
            },
        }
    ).encode()
    selected = tmp_path / "selected"
    assert (
        _run_types(
            selected,
            "--selector",
            "[id|name=Selected]",
            source=source,
        )
        == 0
    )
    stub = (selected / "src/example_types/models.pyi").read_text()
    assert "class Selected(" in stub
    assert "class Excluded(" not in stub
    assert "class Input(" not in stub
    assert "class Output(" not in stub

    complete = tmp_path / "complete"
    assert (
        _run_types(
            complete,
            "--generate-inputs-and-outputs",
            source=source,
        )
        == 0
    )
    stub = (complete / "src/example_types/models.pyi").read_text()
    assert "class Input(" in stub
    assert "class Output(" in stub
    assert capsys.readouterr().err == ""


def test_types_generation_packages_dotted_modules_from_namespace_root(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "output"
    assert (
        _run_types(
            output,
            package="generated.nested_types",
            version="1.0.0",
        )
        == 0
    )
    project = tomllib.loads((output / "pyproject.toml").read_text())
    wheel = project["tool"]["hatch"]["build"]["targets"]["wheel"]
    assert wheel["packages"] == ["src/generated"]

    monkeypatch.syspath_prepend(  # pyright: ignore[reportUnknownMemberType]
        str(output / "src")
    )
    package = importlib.import_module("generated.nested_types")
    assert package.__version__ == "1.0.0"
    assert capsys.readouterr().err == ""


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
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert (
        main(
            ("generate", "client"),
            environ={"SMITHY_PLUGIN_DIR": str(tmp_path)},
            stdin=BytesIO(VALID_MODEL.encode()),
        )
        == 1
    )
    assert "generation is not implemented yet" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (b"{not json", "Invalid JSON"),
        (b"[]", "must be a JSON object"),
        (b"{}", "smithy"),
        (
            b'{"smithy": "2.0", "shapes": {"a#B": {"type": "list",'
            b' "member": {"target": "a#Missing"}}}}',
            "a#B$member",
        ),
    ],
)
def test_invalid_model_is_a_model_failure(
    source: bytes,
    expected: str,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    model = tmp_path / "model.json"
    model.write_bytes(source)

    assert _run_types(tmp_path / "output", "--model", str(model)) == 1
    err = capsys.readouterr().err
    assert err.startswith("smithy-python: error: ")
    assert expected in err
    assert "not implemented" not in err


@pytest.mark.parametrize("option", ["--package", "--package-version"])
def test_types_generation_requires_package_settings(
    option: str,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output = tmp_path / "output"
    args = list(_types_args(output))
    index = args.index(option)
    del args[index : index + 2]

    assert main(args, environ={}, stdin=BytesIO(VALID_MODEL.encode())) == 2
    assert f"the following arguments are required: {option}" in capsys.readouterr().err
    assert not output.exists()


@pytest.mark.parametrize(
    ("option", "value", "expected"),
    [
        (
            "--package",
            "invalid-package",
            "Invalid Python package or distribution name",
        ),
        ("--package", "_example", "Invalid Python package or distribution name"),
        ("--package", "example_", "Invalid Python package or distribution name"),
        ("--package", "café", "Invalid Python package or distribution name"),
        ("--package-version", "", "expected a non-empty value"),
        ("--package-version", "not-a-version", "Invalid version"),
        ("--selector", "[", "Expected an attribute path segment"),
    ],
)
def test_types_generation_rejects_invalid_settings(
    option: str,
    value: str,
    expected: str,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output = tmp_path / "output"
    args = list(_types_args(output))
    index = args.index(option) if option in args else len(args)
    if option in args:
        args[index + 1] = value
    else:
        args.extend((option, value))

    assert main(args, environ={}, stdin=BytesIO(VALID_MODEL.encode())) == 2
    assert expected in capsys.readouterr().err
    assert not output.exists()


def test_types_generation_normalizes_package_version(tmp_path: Path) -> None:
    output = tmp_path / "output"

    assert _run_types(output, version="v1.2") == 0
    project = tomllib.loads((output / "pyproject.toml").read_text())
    assert project["project"]["version"] == "1.2"


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


def test_invocation_reports_missing_model(
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
        == 1
    )
    assert f"Cannot read model {missing}: No such file" in capsys.readouterr().err


def test_invocation_reports_model_path_that_is_a_directory(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # An empty path resolves to the current directory.
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
        == 1
    )
    assert "Cannot read model .:" in capsys.readouterr().err


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
