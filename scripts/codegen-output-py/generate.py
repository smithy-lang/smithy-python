# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Regenerate the committed Python codegen snapshot."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from smithy_python.dependencies import DependencySet
from smithy_python.files import FileManifest
from smithy_python.generation import GenerationContext, GenerationPlan, TypesSettings
from smithy_python.model import load_model
from smithy_python.schemas import SchemaGenerator
from smithy_python.selection import select_type_shapes
from smithy_python.symbols import SymbolProvider

_ROOT = Path(__file__).resolve().parents[2]
_MODEL = Path(__file__).with_name("model.json")
_OUTPUT = _ROOT / "codegen-output-py" / "types"
_PACKAGE = "example_types"
_SERVICE = "example#ExampleService"


def main() -> None:
    model = load_model(_MODEL.read_bytes())
    selection = select_type_shapes(
        model,
        service_id=_SERVICE,
        generate_inputs_and_outputs=True,
    )
    settings = TypesSettings(
        package=_PACKAGE,
        package_version="1.0.0",
        package_description="Example Python codegen output",
    )
    symbols = SymbolProvider(model, selection, package=settings.package)
    dependencies = DependencySet()
    context = GenerationContext(
        model=model,
        selection=selection,
        settings=settings,
        symbols=symbols,
        plan=GenerationPlan.from_selection(model, selection, symbols),
        dependencies=dependencies,
        files=FileManifest(dependencies),
    )
    SchemaGenerator().generate(context)
    context.files.commit(_OUTPUT)
    _format_output()


def _format_output() -> None:
    config = _ROOT / "pyproject.toml"
    for command in ("check", "format"):
        args = [sys.executable, "-m", "ruff", command]
        if command == "check":
            args.append("--fix")
        subprocess.run(
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
