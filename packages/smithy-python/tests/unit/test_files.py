# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
from pathlib import Path

import pytest
from smithy_python.dependencies import SMITHY_CORE, DependencySet
from smithy_python.exceptions import CodegenError
from smithy_python.files import FileManifest
from smithy_python.symbols import TypeReference

_OWNERSHIP_MANIFEST = ".smithy-python-manifest.json"


def test_file_manifest_reuses_python_writer_and_records_dependencies(
    tmp_path: Path,
) -> None:
    dependencies = DependencySet()
    files = FileManifest(dependencies)
    writer = files.python_module("example/models.py", "example.models")
    assert writer is files.python_module("example/models.py", "example.models")
    writer.line(
        "value: ",
        TypeReference(
            "list",
            "builtins",
            (
                TypeReference(
                    "Document",
                    "smithy_core.documents",
                    dependencies=(SMITHY_CORE,),
                ),
            ),
        ),
    )
    files.text_file("example/py.typed", "")

    output = tmp_path / "output"
    files.commit(output)

    assert (
        output.joinpath("example/models.py").read_text(encoding="utf-8")
        == "from __future__ import annotations\n\n"
        "from smithy_core.documents import Document\n\n\n"
        "value: list[Document]\n"
    )
    assert output.joinpath("example/py.typed").read_text(encoding="utf-8") == ""
    assert tuple(dependencies) == (SMITHY_CORE,)
    ownership = json.loads(
        output.joinpath(_OWNERSHIP_MANIFEST).read_text(encoding="utf-8")
    )
    assert ownership["version"] == 1
    assert tuple(ownership["files"]) == ("example/models.py", "example/py.typed")
    assert all(len(digest) == 64 for digest in ownership["files"].values())


@pytest.mark.parametrize(
    "path",
    (
        "",
        "/models.py",
        "example//models.py",
        "./models.py",
        "../models.py",
        "a\\b",
        "D:/outside/models.py",
        "D:outside/models.py",
        "nested/D:/outside/models.py",
    ),
)
def test_file_manifest_rejects_invalid_paths(path: str) -> None:
    files = FileManifest()
    with pytest.raises(CodegenError, match="Invalid generated path"):
        files.text_file(path, "")


def test_file_manifest_rejects_conflicting_claims(tmp_path: Path) -> None:
    files = FileManifest()
    files.python_module("models.py", "example.models")
    with pytest.raises(CodegenError, match="already uses module"):
        files.python_module("models.py", "other.models")
    with pytest.raises(CodegenError, match="already claimed"):
        files.text_file("models.py", "")
    with pytest.raises(CodegenError, match="reserved"):
        files.text_file(_OWNERSHIP_MANIFEST, "")

    files.text_file("package", "")
    files.text_file("package/models.py", "")
    with pytest.raises(CodegenError, match="conflicts"):
        files.commit(tmp_path / "output")


def test_validation_failure_leaves_existing_output_untouched(tmp_path: Path) -> None:
    output = tmp_path / "output"
    output.mkdir()
    existing = output / "existing.py"
    existing.write_text("value = 'original'\n", encoding="utf-8")

    files = FileManifest()
    files.python_module("invalid.py", "invalid").line("if")
    with pytest.raises(CodegenError, match="not valid Python"):
        files.commit(output)

    assert existing.read_text(encoding="utf-8") == "value = 'original'\n"
    assert not output.joinpath("invalid.py").exists()
    assert not output.joinpath(_OWNERSHIP_MANIFEST).exists()


def test_unowned_current_file_is_not_overwritten(tmp_path: Path) -> None:
    output = tmp_path / "output"
    output.mkdir()
    existing = output / "current.txt"
    existing.write_text("user\n", encoding="utf-8")

    files = FileManifest()
    files.text_file("current.txt", "generated\n")
    with pytest.raises(CodegenError, match="not owned"):
        files.commit(output)

    assert existing.read_text(encoding="utf-8") == "user\n"
    assert not output.joinpath(_OWNERSHIP_MANIFEST).exists()


def test_owned_current_file_is_replaced_even_when_modified(tmp_path: Path) -> None:
    output = tmp_path / "output"
    first = FileManifest()
    first.text_file("current.txt", "first\n")
    first.commit(output)
    output.joinpath("current.txt").write_text("modified\n", encoding="utf-8")

    second = FileManifest()
    second.text_file("current.txt", "second\n")
    second.commit(output)

    assert output.joinpath("current.txt").read_text(encoding="utf-8") == "second\n"


def test_stale_owned_files_are_deleted_only_when_unmodified(tmp_path: Path) -> None:
    output = tmp_path / "output"
    first = FileManifest()
    first.text_file("delete.txt", "generated\n")
    first.text_file("retain.txt", "generated\n")
    first.commit(output)
    output.joinpath("retain.txt").write_text("modified\n", encoding="utf-8")
    output.joinpath("unowned.txt").write_text("unowned\n", encoding="utf-8")

    second = FileManifest()
    second.text_file("current.txt", "current\n")
    second.commit(output)

    assert not output.joinpath("delete.txt").exists()
    assert output.joinpath("retain.txt").read_text(encoding="utf-8") == "modified\n"
    assert output.joinpath("unowned.txt").read_text(encoding="utf-8") == "unowned\n"
    ownership = json.loads(
        output.joinpath(_OWNERSHIP_MANIFEST).read_text(encoding="utf-8")
    )
    assert tuple(ownership["files"]) == ("current.txt",)


def test_stale_owned_path_changed_to_directory_is_retained(tmp_path: Path) -> None:
    output = tmp_path / "output"
    first = FileManifest()
    first.text_file("stale", "generated\n")
    first.commit(output)
    output.joinpath("stale").unlink()
    output.joinpath("stale").mkdir()
    output.joinpath("stale/user.txt").write_text("user\n", encoding="utf-8")

    FileManifest().commit(output)

    assert output.joinpath("stale/user.txt").read_text(encoding="utf-8") == "user\n"


def test_stale_owned_path_with_symlinked_ancestor_is_retained(tmp_path: Path) -> None:
    output = tmp_path / "output"
    first = FileManifest()
    first.text_file("old/file.txt", "generated\n")
    first.commit(output)
    output.joinpath("old/file.txt").unlink()
    output.joinpath("old").rmdir()
    output.joinpath("current").mkdir()
    try:
        output.joinpath("old").symlink_to("current", target_is_directory=True)
    except OSError as error:
        pytest.skip(f"Cannot create symlinks: {error}")

    second = FileManifest()
    second.text_file("current/file.txt", "generated\n")
    second.commit(output)

    assert output.joinpath("current/file.txt").read_text() == "generated\n"


def test_without_previous_manifest_existing_files_are_not_deleted(
    tmp_path: Path,
) -> None:
    output = tmp_path / "output"
    output.mkdir()
    existing = output / "existing.txt"
    existing.write_text("existing\n", encoding="utf-8")

    FileManifest().commit(output)

    assert existing.read_text(encoding="utf-8") == "existing\n"


def test_symlink_that_escapes_output_is_rejected(tmp_path: Path) -> None:
    output = tmp_path / "output"
    outside = tmp_path / "outside"
    output.mkdir()
    outside.mkdir()
    try:
        output.joinpath("escape").symlink_to(outside, target_is_directory=True)
    except OSError as error:
        pytest.skip(f"Cannot create symlinks: {error}")

    files = FileManifest()
    files.text_file("escape/generated.txt", "content\n")
    with pytest.raises(CodegenError, match="escapes"):
        files.commit(output)

    assert not outside.joinpath("generated.txt").exists()


def test_symlinked_destination_ancestor_is_rejected(tmp_path: Path) -> None:
    output = tmp_path / "output"
    output.mkdir()
    output.joinpath("real").mkdir()
    try:
        output.joinpath("alias").symlink_to("real", target_is_directory=True)
    except OSError as error:
        pytest.skip(f"Cannot create symlinks: {error}")

    files = FileManifest()
    files.text_file("alias/generated.txt", "content\n")
    with pytest.raises(CodegenError, match="symlinked ancestor"):
        files.commit(output)

    assert not output.joinpath("real/generated.txt").exists()


def test_invalid_previous_manifest_prevents_publication(tmp_path: Path) -> None:
    output = tmp_path / "output"
    output.mkdir()
    output.joinpath(_OWNERSHIP_MANIFEST).write_text("{}", encoding="utf-8")
    files = FileManifest()
    files.text_file("generated.txt", "content\n")

    with pytest.raises(CodegenError, match="Invalid output ownership manifest"):
        files.commit(output)

    assert not output.joinpath("generated.txt").exists()
