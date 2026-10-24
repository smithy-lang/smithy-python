# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Staged output and ownership tracking for generated artifacts."""

from __future__ import annotations

import hashlib
import itertools
import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Final, cast

from . import dependencies as _dependencies
from . import exceptions as _exceptions
from . import writer as _writer

__all__ = ["FileManifest"]

_MANIFEST_PATH: Final = ".smithy-python-manifest.json"
_MANIFEST_VERSION: Final = 1


class FileManifest:
    """Collect, validate, publish, and track files for one generated artifact."""

    def __init__(self, dependencies: _dependencies.DependencySet | None = None) -> None:
        self._dependencies = (
            dependencies if dependencies is not None else _dependencies.DependencySet()
        )
        self._files: dict[str, _GeneratedFile] = {}

    @property
    def dependencies(self) -> _dependencies.DependencySet:
        """Dependencies recorded by writers owned by this manifest."""
        return self._dependencies

    def python_module(self, path: str, module: str) -> _writer.PythonWriter:
        """Return the shared writer for a generated Python module."""
        path = _normalize_path(path)
        self._claim_public_path(path)
        existing = self._files.get(path)
        if isinstance(existing, _PythonFile):
            if existing.module != module:
                raise _exceptions.CodegenError(
                    f"Generated path {path!r} already uses module "
                    f"{existing.module!r}, not {module!r}"
                )
            return existing.writer
        if existing is not None:
            raise _exceptions.CodegenError(
                f"Generated path {path!r} is already a text file"
            )
        writer = _writer.PythonWriter(module, dependencies=self._dependencies)
        self._files[path] = _PythonFile(module, writer)
        return writer

    def text_file(self, path: str, content: str) -> None:
        """Register one generated text file."""
        path = _normalize_path(path)
        self._claim_public_path(path)
        if path in self._files:
            raise _exceptions.CodegenError(
                f"Generated path {path!r} is already claimed"
            )
        self._files[path] = _TextFile(content)

    def commit(self, output: Path) -> None:
        """Stage, validate, and publish all registered files."""
        output = output.absolute()
        self._validate_path_tree()
        if output.is_symlink() and not output.exists():
            raise _exceptions.CodegenError(
                f"Output path is a dangling symlink: {output}"
            )
        if output.exists() and not output.is_dir():
            raise _exceptions.CodegenError(f"Output path is not a directory: {output}")

        previous = self._load_previous_manifest(output)
        for path in self._files:
            self._validate_destination(output, path)
        for path in previous:
            self._validate_safe_path(output, path)

        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(
            prefix=f".{output.name or 'output'}.smithy-python-",
            dir=output.parent,
        ) as directory:
            staging = Path(directory)
            hashes = self._stage_files(staging)
            manifest_content = self._render_manifest(hashes)
            manifest_target = staging / _MANIFEST_PATH
            manifest_target.write_text(manifest_content, encoding="utf-8")
            self._publish(output, staging, hashes, previous)

    @staticmethod
    def _claim_public_path(path: str) -> None:
        if path == _MANIFEST_PATH:
            raise _exceptions.CodegenError(
                f"Generated path {_MANIFEST_PATH!r} is reserved for output ownership"
            )

    def _validate_path_tree(self) -> None:
        paths = sorted(PurePosixPath(path).parts for path in self._files)
        for previous, current in itertools.pairwise(paths):
            if len(previous) < len(current) and current[: len(previous)] == previous:
                raise _exceptions.CodegenError(
                    f"Generated path {'/'.join(previous)!r} conflicts with "
                    f"{'/'.join(current)!r}"
                )

    @staticmethod
    def _validate_safe_path(output: Path, path: str) -> None:
        root = output.resolve(strict=False)
        current = output
        for part in PurePosixPath(path).parts:
            current /= part
            if current.is_symlink():
                if not current.exists():
                    raise _exceptions.CodegenError(
                        f"Generated path {path!r} contains a dangling symlink"
                    )
                resolved = current.resolve(strict=False)
                if not resolved.is_relative_to(root):
                    raise _exceptions.CodegenError(
                        f"Generated path {path!r} escapes the output directory"
                    )

    @classmethod
    def _validate_destination(cls, output: Path, path: str) -> None:
        cls._validate_safe_path(output, path)
        parts = PurePosixPath(path).parts
        current = output
        for index, part in enumerate(parts):
            current /= part
            if index < len(parts) - 1 and current.is_symlink():
                raise _exceptions.CodegenError(
                    f"Generated path {path!r} contains a symlinked ancestor"
                )
            if current.exists():
                is_target = index == len(parts) - 1
                if (is_target and current.is_dir()) or (
                    not is_target and not current.is_dir()
                ):
                    raise _exceptions.CodegenError(
                        f"Generated path {path!r} conflicts with {current}"
                    )

    @staticmethod
    def _load_previous_manifest(output: Path) -> dict[str, str]:
        manifest = output / _MANIFEST_PATH
        if manifest.is_symlink():
            raise _exceptions.CodegenError(
                f"Output ownership manifest cannot be a symlink: {manifest}"
            )
        if not manifest.exists():
            return {}
        try:
            value: object = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise _exceptions.CodegenError(
                f"Cannot read output ownership manifest: {error}"
            ) from error
        if not isinstance(value, dict):
            raise _exceptions.CodegenError("Invalid output ownership manifest")
        manifest_data = cast(dict[object, object], value)
        files = manifest_data.get("files")
        if manifest_data.get("version") != _MANIFEST_VERSION or not isinstance(
            files, dict
        ):
            raise _exceptions.CodegenError("Invalid output ownership manifest")
        file_data = cast(dict[object, object], files)
        result: dict[str, str] = {}
        for raw_path, digest in file_data.items():
            if not isinstance(raw_path, str) or not isinstance(digest, str):
                raise _exceptions.CodegenError("Invalid output ownership manifest")
            path = _normalize_path(raw_path)
            if (
                path != raw_path
                or path == _MANIFEST_PATH
                or len(digest) != 64
                or any(character not in "0123456789abcdef" for character in digest)
            ):
                raise _exceptions.CodegenError("Invalid output ownership manifest")
            result[path] = digest
        return result

    def _stage_files(self, staging: Path) -> dict[str, str]:
        hashes: dict[str, str] = {}
        for path in sorted(self._files):
            generated = self._files[path]
            if isinstance(generated, _PythonFile):
                content = generated.writer.render()
                try:
                    compile(content, path, "exec", dont_inherit=True)
                except (SyntaxError, ValueError) as error:
                    raise _exceptions.CodegenError(
                        f"Generated Python module {path!r} is invalid: {error}"
                    ) from error
            else:
                content = generated.content
            if "\0" in content:
                raise _exceptions.CodegenError(
                    f"Generated text file {path!r} contains a null byte"
                )
            encoded = content.encode()
            target = staging.joinpath(*PurePosixPath(path).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(encoded)
            hashes[path] = hashlib.sha256(encoded).hexdigest()
        return hashes

    @staticmethod
    def _render_manifest(hashes: dict[str, str]) -> str:
        return (
            json.dumps(
                {"version": _MANIFEST_VERSION, "files": hashes},
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )

    @staticmethod
    def _publish(
        output: Path,
        staging: Path,
        hashes: dict[str, str],
        previous: dict[str, str],
    ) -> None:
        output.mkdir(parents=True, exist_ok=True)
        for path in hashes:
            source = staging.joinpath(*PurePosixPath(path).parts)
            target = output.joinpath(*PurePosixPath(path).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            os.replace(source, target)

        for path in sorted(previous.keys() - hashes.keys()):
            parts = PurePosixPath(path).parts
            target = output.joinpath(*parts)
            if not target.is_file() or any(
                output.joinpath(*parts[:index]).is_symlink()
                for index in range(1, len(parts) + 1)
            ):
                continue
            try:
                unchanged = _digest_file(target) == previous[path]
            except OSError:
                unchanged = False
            if unchanged:
                target.unlink()

        os.replace(staging / _MANIFEST_PATH, output / _MANIFEST_PATH)


@dataclass(slots=True)
class _PythonFile:
    module: str
    writer: _writer.PythonWriter


@dataclass(frozen=True, slots=True)
class _TextFile:
    content: str


type _GeneratedFile = _PythonFile | _TextFile


def _normalize_path(path: str) -> str:
    parts = path.split("/")
    if (
        not path
        or path.startswith("/")
        or "\\" in path
        or any(
            part in ("", ".", "..")
            or (
                len(part) >= 2
                and part[0].isascii()
                and part[0].isalpha()
                and part[1] == ":"
            )
            for part in parts
        )
    ):
        raise _exceptions.CodegenError(f"Invalid generated path: {path!r}")
    return str(PurePosixPath(path))


def _digest_file(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()
