# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Command-line interface for the Smithy Python code generator."""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Final

from . import __version__
from .environment import PluginEnvironment
from .exceptions import CodegenError, InvalidInvocationError

_GENERATION_NOT_IMPLEMENTED: Final = (
    "smithy-python: error: {artifact} generation is not implemented yet\n"
)


@dataclass(frozen=True, slots=True)
class _Invocation:
    artifact: str
    model_source: bytes
    output_dir: Path
    environment: PluginEnvironment


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
        _resolve_invocation(
            args,
            environ=os.environ if environ is None else environ,
            stdin=stdin,
        )
    except InvalidInvocationError as error:
        sys.stderr.write(f"smithy-python: error: {error}\n")
        return 2
    except (CodegenError, OSError) as error:
        sys.stderr.write(f"smithy-python: error: {error}\n")
        return 1

    sys.stderr.write(_GENERATION_NOT_IMPLEMENTED.format(artifact=args.artifact))
    return 1


def _create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="smithy-python",
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
    for name, help_text in (
        ("client", "Generate a client package"),
        ("types", "Generate a standalone types package"),
    ):
        artifact = artifacts.add_parser(name, help=help_text)
        artifact.add_argument(
            "--model",
            type=Path,
            help="Read the JSON AST from a file instead of standard input",
        )
        artifact.add_argument(
            "--output",
            type=Path,
            help="Output directory for direct invocation",
        )

    return parser


def _resolve_invocation(
    args: argparse.Namespace,
    *,
    environ: Mapping[str, str],
    stdin: BinaryIO | None,
) -> _Invocation:
    environment = PluginEnvironment.from_environ(environ)
    model_path: Path | None = args.model
    output_path: Path | None = args.output

    if (plugin_dir := environment.plugin_dir) is not None:
        if model_path is not None:
            raise InvalidInvocationError(
                "--model cannot be used with the Smithy run plugin"
            )
        if output_path is not None:
            raise InvalidInvocationError(
                "--output cannot be used with the Smithy run plugin"
            )
        output_dir = plugin_dir
    else:
        if output_path is None:
            raise InvalidInvocationError("Direct invocation requires --output")
        output_dir = output_path

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

    return _Invocation(
        artifact=args.artifact,
        model_source=model_source,
        output_dir=output_dir,
        environment=environment,
    )
