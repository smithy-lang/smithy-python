# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Command-line interface for the Smithy Python code generator."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Final

from . import __version__
from .environment import PluginEnvironment
from .exceptions import CodegenError, InvalidInvocationError, ModelError
from .model import Model, Shape, ShapeID
from .selection import Selection, resolve_service, select_generated_shapes

_PROGRAM: Final = "smithy-python"

_CLIENT_ARTIFACT: Final = "client"


def _write_error(message: str) -> None:
    sys.stderr.write(f"{_PROGRAM}: error: {message}\n")


def _write_note(message: str) -> None:
    sys.stderr.write(f"{_PROGRAM}: note: {message}\n")


@dataclass(frozen=True, slots=True)
class _Request:
    """The fully resolved generation request of a single run."""

    artifact: str
    model: Model
    output_dir: Path
    environment: PluginEnvironment
    service: Shape | None
    selection: Selection


def main(
    argv: Sequence[str] | None = None,
    *,
    environ: Mapping[str, str] | None = None,
    stdin: BinaryIO | None = None,
) -> int:
    """Run the CLI with the provided process inputs and return its exit code."""
    parser = _create_parser()

    try:
        args = parser.parse_args(argv)
    except SystemExit as error:
        return error.code if isinstance(error.code, int) else 1

    try:
        request = _resolve_request(args, environ=environ, stdin=stdin)
    except InvalidInvocationError as error:
        _write_error(str(error))
        return 2
    except (CodegenError, OSError) as error:
        _write_error(str(error))
        return 1

    _write_error(f"{request.artifact} generation is not implemented yet")
    return 1


def _create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=_PROGRAM,
        description="Generate Python source from Smithy models.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    commands = parser.add_subparsers(required=True)
    generate = commands.add_parser("generate", help="Generate Python source")
    artifacts = generate.add_subparsers(dest="artifact", required=True)
    common = _common_artifact_options()
    for name, help_text in (
        (_CLIENT_ARTIFACT, "Generate a client package"),
        ("types", "Generate a standalone types package"),
    ):
        artifacts.add_parser(name, help=help_text, parents=[common])

    return parser


def _common_artifact_options() -> argparse.ArgumentParser:
    """Build a parent parser with the options shared by every artifact."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "--model",
        type=Path,
        help=(
            "The Smithy JSON AST model file to use for code generation. "
            "If not set, the model is read from standard input."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "Output directory for generated files. Required unless the Smithy run "
            "plugin provides one (SMITHY_PLUGIN_DIR), which this cannot override."
        ),
    )
    parser.add_argument(
        "--service",
        metavar="SHAPE_ID",
        help=(
            "Absolute shape ID of the service to generate. Required only when the "
            "model contains more than one service."
        ),
    )
    return parser


def _resolve_request(
    args: argparse.Namespace,
    *,
    environ: Mapping[str, str] | None,
    stdin: BinaryIO | None,
) -> _Request:
    """Resolve the process inputs of a single run into a generation request."""
    environment = PluginEnvironment.from_environ(environ)
    output_dir = _resolve_output_dir(args, environment)
    requested_service = _parse_service(args.service)
    # Parsing here keeps the undecoded model out of memory for the rest of the run.
    model = Model.from_json(_read_model(args.model, environment, stdin))

    service = resolve_service(
        model, requested_service, required=args.artifact == _CLIENT_ARTIFACT
    )
    selection = select_generated_shapes(model, service)
    if selection.excluded and service is not None:
        _write_note(
            f"{len(selection.excluded)} shape(s) not connected to {service.id} "
            f"will not be generated"
        )

    return _Request(
        artifact=args.artifact,
        model=model,
        output_dir=output_dir,
        environment=environment,
        service=service,
        selection=selection,
    )


def _resolve_output_dir(
    args: argparse.Namespace, environment: PluginEnvironment
) -> Path:
    """Return the directory generated files are written to."""
    if (plugin_dir := environment.plugin_dir) is not None:
        for flag, value in (("--model", args.model), ("--output", args.output)):
            if value is not None:
                raise InvalidInvocationError(
                    f"{flag} cannot be used with the Smithy run plugin"
                )
        return plugin_dir

    output_path: Path | None = args.output
    if output_path is None:
        raise InvalidInvocationError("Direct invocation requires --output")
    return output_path


def _read_model(
    model_path: Path | None, environment: PluginEnvironment, stdin: BinaryIO | None
) -> bytes:
    """Read the JSON AST document from the model file or standard input."""
    if model_path is not None:
        if not model_path.is_file():
            raise InvalidInvocationError(f"Model path is not a file: {model_path}")
        model_source = model_path.read_bytes()
    else:
        model_stream = sys.stdin.buffer if stdin is None else stdin
        if environment.plugin_dir is None and model_stream.isatty():
            raise InvalidInvocationError(
                "Direct invocation requires --model or a model piped to standard input"
            )
        model_source = model_stream.read()
    if not model_source:
        raise InvalidInvocationError("Expected a Smithy JSON AST model")
    return model_source


def _parse_service(value: str | None) -> ShapeID | None:
    if value is None:
        return None
    try:
        service = ShapeID.parse(value)
    except ModelError as error:
        raise InvalidInvocationError(f"Invalid --service value: {error}") from error
    if service.member is not None:
        raise InvalidInvocationError(
            f"--service must identify a shape, not a member: {value}"
        )
    return service
