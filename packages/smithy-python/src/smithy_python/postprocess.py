# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import logging
import shutil
import subprocess
import sys
from pathlib import Path

from .exceptions import CodegenError

_LOGGER = logging.getLogger(__name__)


def format_python(output_dir: Path, files: tuple[Path, ...]) -> None:
    executable = _executable("ruff")
    python_files = [str(path) for path in files if path.suffix == ".py"]
    if executable is None or not python_files:
        if executable is None:
            _LOGGER.info("ruff is not installed; generated Python was not formatted")
        return
    _run([executable, "format", *python_files], output_dir, "ruff formatter")


def lint_python(output_dir: Path) -> None:
    ruff = _executable("ruff")
    if ruff is not None:
        _run([ruff, "check", "--fix", str(output_dir)], output_dir, "ruff linter")
        _run([ruff, "format", str(output_dir)], output_dir, "ruff formatter")
    pyright = _executable("pyright")
    if pyright is not None:
        _run([pyright, str(output_dir)], output_dir, "pyright")


def _executable(name: str) -> str | None:
    if found := shutil.which(name):
        return found
    candidate = Path(sys.prefix, "bin", name)
    return str(candidate) if candidate.is_file() else None


def _run(command: list[str], cwd: Path, description: str) -> None:
    result = subprocess.run(  # noqa: S603 - command is a fixed executable and args list.
        command,
        cwd=cwd,
        capture_output=True,
        check=False,
        text=True,
    )
    if result.returncode:
        details = result.stderr.strip() or result.stdout.strip()
        raise CodegenError(f"{description} failed: {details}")
