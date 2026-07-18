# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Command-line interface used directly and by Smithy's run plugin."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import cast

from .exceptions import CodegenError
from .generator import PythonCodeGenerator
from .model import Model
from .plugins import PluginRegistry
from .settings import ArtifactType, GeneratorSettings, PluginEnvironment


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "artifact_type"):
        parser.print_help(sys.stderr)
        return 2
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )
    try:
        environment = PluginEnvironment.from_environ()
        settings = _settings(args)
        source = (
            Path(args.model).read_bytes() if args.model else sys.stdin.buffer.read()
        )
        if not source:
            raise CodegenError("Expected a Smithy JSON AST model on standard input")
        model = Model.from_json(source)
        output = (
            Path(args.output) if args.output else environment.plugin_dir or Path.cwd()
        )
        registry = PluginRegistry.discover(args.plugin)
        PythonCodeGenerator(registry).generate(
            model,
            settings,
            output_dir=output,
            environment=environment,
        )
    except (CodegenError, OSError) as error:
        sys.stderr.write(f"smithy-python: error: {error}\n")
        return 2
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="smithy-python")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    commands = parser.add_subparsers(dest="command")
    generate = commands.add_parser("generate", help="Generate Python source")
    modes = generate.add_subparsers(dest="mode")
    for mode in ArtifactType:
        command = modes.add_parser(mode.value, help=f"Generate a {mode.value} package")
        command.set_defaults(artifact_type=mode)
        command.add_argument("--settings", help="JSON settings object or @path to JSON")
        command.add_argument(
            "--model", help="Read the JSON AST from a file instead of stdin"
        )
        command.add_argument(
            "--output", help="Output directory (defaults to SMITHY_PLUGIN_DIR)"
        )
        command.add_argument("--service", help="Absolute Smithy service shape ID")
        command.add_argument(
            "--module", dest="module_name", help="Generated Python module"
        )
        command.add_argument("--module-version", help="Generated package version")
        command.add_argument(
            "--module-description", help="Generated package description"
        )
        command.add_argument("--selector", help="Types selector")
        command.add_argument(
            "--include-shape",
            action="append",
            default=[],
            help="Include this shape and its closure (repeatable)",
        )
        command.add_argument(
            "--generate-inputs-and-outputs",
            action="store_true",
            default=None,
            help="Include operation input/output shapes in types mode",
        )
        command.add_argument(
            "--plugin", action="append", default=[], help="Load package.module:object"
        )
        command.add_argument(
            "--no-format", action="store_true", help="Do not run ruff format"
        )
        command.add_argument(
            "--lint", action="store_true", default=None, help="Run available linters"
        )
    return parser


def _settings(args: argparse.Namespace) -> GeneratorSettings:
    settings_value = cast(str | None, args.settings)
    values = _settings_json(settings_value) if settings_value else {}
    overrides: dict[str, object | None] = {
        "service": args.service,
        "module": args.module_name,
        "moduleVersion": args.module_version,
        "moduleDescription": args.module_description,
        "selector": args.selector,
        "generateInputsAndOutputs": args.generate_inputs_and_outputs,
        "lint": args.lint,
    }
    for key, value in overrides.items():
        if value is not None:
            values[key] = value
    include_shapes = cast(list[str], args.include_shape)
    if include_shapes:
        existing = values.get("includeShapes", [])
        if not isinstance(existing, list):
            raise CodegenError("includeShapes in settings must be an array")
        values["includeShapes"] = [*existing, *include_shapes]
    if args.no_format:
        values["format"] = False
    return GeneratorSettings.from_mapping(
        cast(ArtifactType, args.artifact_type), values
    )


def _settings_json(value: str) -> dict[str, object]:
    try:
        source = Path(value[1:]).read_text() if value.startswith("@") else value
        result = cast(object, json.loads(source))
    except (OSError, json.JSONDecodeError) as error:
        raise CodegenError(f"Unable to read generator settings: {error}") from error
    if not isinstance(result, dict):
        raise CodegenError("Generator settings must be a JSON object")
    untyped = cast(dict[object, object], result)
    if not all(isinstance(key, str) for key in untyped):
        raise CodegenError("Generator setting names must be strings")
    return {key: item for key, item in untyped.items() if isinstance(key, str)}
