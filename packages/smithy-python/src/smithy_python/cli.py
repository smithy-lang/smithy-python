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

from packaging.version import InvalidVersion, Version

from . import __version__
from . import dependencies as _dependencies
from . import exceptions as _exceptions
from . import files as _files
from . import generation as _generation
from . import model as _model
from . import models as _models
from . import selection as _selection
from . import symbols as _symbols
from . import types as _types
from .environment import PluginEnvironment
from .exceptions import CodegenError, InvalidInvocationError
from .model import load_model
from .selection import select_shapes

__all__ = ["main"]

_GENERATION_NOT_IMPLEMENTED: Final = (
    "smithy-python: error: {artifact} generation is not implemented yet\n"
)


@dataclass(frozen=True, slots=True)
class _Invocation:
    model_source: bytes
    output_dir: Path


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
        invocation = _resolve_invocation(args, environ=environ, stdin=stdin)
        model = load_model(invocation.model_source)
        if args.artifact == "types":
            selection = _generate_types(args, invocation.output_dir, model)
        else:
            selection = select_shapes(
                model,
                service_id=args.service,
                require_service=True,
            )
    except InvalidInvocationError as error:
        sys.stderr.write(f"smithy-python: error: {error}\n")
        return 2
    except (CodegenError, OSError) as error:
        sys.stderr.write(f"smithy-python: error: {error}\n")
        return 1

    if selection.excluded_count and selection.service is not None:
        sys.stderr.write(
            f"smithy-python: excluded {selection.excluded_count} eligible data shape(s) "
            f"outside the closure of service {selection.service.id}\n"
        )
    if args.artifact == "types":
        return 0
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
    common = _common_artifact_options()
    artifacts.add_parser("client", help="Generate a client package", parents=[common])
    types = artifacts.add_parser(
        "types", help="Generate a standalone types package", parents=[common]
    )
    types.add_argument(
        "--package",
        required=True,
        help="Import package and distribution name for the generated artifact.",
    )
    types.add_argument(
        "--package-version",
        required=True,
        type=_package_version,
        help="Version for the generated package.",
    )
    types.add_argument(
        "--package-description",
        help='Package description; defaults to "<package> types package".',
    )
    types.add_argument(
        "--selector",
        type=_parse_selector,
        default=_selection.Selector.identity(),
        help="Smithy selector used to narrow generated declaration roots.",
    )
    types.add_argument(
        "--generate-inputs-and-outputs",
        action="store_true",
        help="Include operation input and output structures as generation roots.",
    )

    return parser


def _common_artifact_options() -> argparse.ArgumentParser:
    """Build a parent parser with the options shared by every artifact."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "--service",
        metavar="SHAPE_ID",
        help="Absolute service shape ID; defaults to the sole non-mixin service.",
    )
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
            "Output directory for generated files. Defaults to the Smithy run "
            "plugin's output directory (SMITHY_PLUGIN_DIR) when invoked by Smithy."
        ),
    )
    return parser


def _resolve_invocation(
    args: argparse.Namespace,
    *,
    environ: Mapping[str, str] | None,
    stdin: BinaryIO | None,
) -> _Invocation:
    # PluginEnvironment falls back to os.environ, so the defaulting lives there.
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
        # A model that cannot be read is an I/O failure like any other, whether
        # the path is missing, a directory, or unreadable.
        try:
            model_source = model_path.read_bytes()
        except OSError as error:
            raise OSError(
                f"Cannot read model {model_path}: {error.strerror or error}"
            ) from error
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
        model_source=model_source,
        output_dir=output_dir,
    )


def _generate_types(
    args: argparse.Namespace,
    output_dir: Path,
    model: _model.Model,
) -> _selection.Selection:
    description = args.package_description or f"{args.package} types package"
    settings = _generation.TypesSettings(
        package=args.package,
        package_version=args.package_version,
        package_description=description,
        selector=args.selector,
        generate_inputs_and_outputs=args.generate_inputs_and_outputs,
    )
    selection = _selection.select_type_shapes(
        model,
        service_id=args.service,
        selector=settings.selector,
        generate_inputs_and_outputs=settings.generate_inputs_and_outputs,
    )
    try:
        symbols = _symbols.SymbolProvider(
            model,
            selection,
            package=settings.package,
            reserved_member_names=_models._model_reserved_member_names(  # pyright: ignore[reportPrivateUsage]
                model
            ),
        )
    except ValueError as error:
        raise InvalidInvocationError(str(error)) from error

    dependencies = _dependencies.DependencySet()
    context = _generation.GenerationContext(
        model=model,
        selection=selection,
        settings=settings,
        symbols=symbols,
        plan=_generation.GenerationPlan.from_selection(model, selection, symbols),
        dependencies=dependencies,
        files=_files.FileManifest(dependencies),
    )
    _types.TypesGenerator().generate(context)
    context.files.commit(output_dir)
    return selection


def _parse_selector(value: str) -> _selection.Selector:
    try:
        return _selection.Selector.parse(value)
    except _exceptions.SelectorSyntaxError as error:
        raise argparse.ArgumentTypeError(str(error)) from error


def _package_version(value: str) -> str:
    if not value:
        raise argparse.ArgumentTypeError("expected a non-empty value")
    try:
        return str(Version(value))
    except InvalidVersion as error:
        raise argparse.ArgumentTypeError(str(error)) from error
