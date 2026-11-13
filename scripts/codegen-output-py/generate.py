# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
# pyright: reportPrivateUsage=false
"""Generate types and client snapshots from checked-in Smithy JSON ASTs."""

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from smithy_python.cli import main as generate

_ROOT = Path(__file__).resolve().parents[2]
_INPUTS = Path(__file__).parent
_OUTPUT = _ROOT / "codegen-output-py"
# Each artifact, its projection inputs, and its extra command options.
_ARTIFACTS = (
    ("types", "projections.json", ("--include-operation-io",)),
    ("client", "client-projections.json", ()),
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="Check without publishing."
    )
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    args = parser.parse_args()

    # A fresh tree also detects removed projections and obsolete partitions.
    with TemporaryDirectory(prefix="smithy-python-snapshots-") as temporary:
        staged = Path(temporary)
        for artifact, inputs, options in _ARTIFACTS:
            projections = json.loads((_INPUTS / inputs).read_text())
            for name, settings in sorted(projections.items()):
                result = generate(
                    (
                        "generate",
                        artifact,
                        "--model",
                        str(_INPUTS / settings["model"]),
                        "--output",
                        str(staged / name),
                        "--service",
                        settings["service"],
                        "--package",
                        settings["package"],
                        "--package-version",
                        settings["version"],
                        "--package-description",
                        settings["description"],
                        *options,
                    ),
                    environ={},
                )
                if result:
                    raise SystemExit(result)
        _format_output(staged)
        expected = _files(staged)
        actual = _files(args.output)
        changed = sorted(
            path
            for path in expected.keys() | actual.keys()
            if expected.get(path) != actual.get(path)
        )
        if args.check:
            if changed:
                sys.stderr.write(
                    "codegen-output-py differs from fresh generation:\n"
                    + "\n".join(changed)
                    + "\nRun make generate-codegen-output-py to update the snapshots.\n"
                )
                raise SystemExit(1)
            sys.stdout.write("codegen-output-py is up to date.\n")
        elif changed:
            if args.output.exists():
                shutil.rmtree(args.output)
            shutil.copytree(staged, args.output)
            sys.stdout.write(f"Updated {len(changed)} snapshot file(s).\n")
        else:
            sys.stdout.write("codegen-output-py is up to date; no files changed.\n")


def _files(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
        and not any(
            part.startswith(".") or part == "__pycache__"
            for part in path.relative_to(root).parts[:-1]
        )
        and path.suffix != ".pyc"
    }


def _format_output(output: Path) -> None:
    config = _ROOT / "pyproject.toml"
    for command in ("check", "format"):
        args = [sys.executable, "-m", "ruff", command]
        if command == "check":
            args.append("--fix")
        subprocess.run(  # noqa: S603
            [*args, str(output), "--config", str(config), "--no-cache"],
            check=True,
        )

    for projection in sorted(output.iterdir()):
        manifest = projection / ".smithy-python-manifest.json"
        files = {
            path: hashlib.sha256(content).hexdigest()
            for path, content in _files(projection).items()
            if path != manifest.name
        }
        manifest.write_text(
            json.dumps({"version": 1, "files": files}, indent=2, sort_keys=True) + "\n"
        )


if __name__ == "__main__":
    main()
