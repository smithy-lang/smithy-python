# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
# pyright: reportPrivateUsage=false
"""Regenerate the committed Python codegen snapshot."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from smithy_python.cli import main as generate

_ROOT = Path(__file__).resolve().parents[2]
_MODEL = Path(__file__).with_name("model.json")
_OUTPUT = _ROOT / "codegen-output-py" / "types"
_PACKAGE = "example_types"
_SERVICE = "example#ExampleService"


def main() -> None:
    result = generate(
        (
            "generate",
            "types",
            "--model",
            str(_MODEL),
            "--output",
            str(_OUTPUT),
            "--service",
            _SERVICE,
            "--package",
            _PACKAGE,
            "--package-version",
            "1.0.0",
            "--package-description",
            "Example Python codegen output",
            "--include-operation-io",
        ),
        environ={},
    )
    if result:
        raise SystemExit(result)
    _format_output()


def _format_output() -> None:
    config = _ROOT / "pyproject.toml"
    for command in ("check", "format"):
        args = [sys.executable, "-m", "ruff", command]
        if command == "check":
            args.append("--fix")
        subprocess.run(  # noqa: S603
            [*args, str(_OUTPUT), "--config", str(config)],
            check=True,
        )

    manifest = _OUTPUT / ".smithy-python-manifest.json"
    files = {
        path.relative_to(_OUTPUT).as_posix(): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in sorted(_OUTPUT.rglob("*"))
        if path.is_file() and path != manifest
    }
    manifest.write_text(
        json.dumps({"version": 1, "files": files}, indent=2, sort_keys=True) + "\n"
    )


if __name__ == "__main__":
    main()
