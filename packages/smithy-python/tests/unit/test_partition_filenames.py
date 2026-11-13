# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import importlib
import subprocess
import sys
from pathlib import Path

import pytest
from smithy_core._schema_compact import hydrate
from smithy_python.dependencies import DependencySet
from smithy_python.files import FileManifest
from smithy_python.generation import GenerationContext, GenerationPlan, TypesSettings
from smithy_python.model import load_model
from smithy_python.selection import select_type_shapes
from smithy_python.symbols import SymbolProvider
from smithy_python.types import TypesGenerator


def _generate(output: Path, shape_count: int, package: str) -> None:
    model = load_model(
        {
            "smithy": "2.0",
            "shapes": {
                f"example#Shape{index}": {"type": "structure"}
                for index in range(shape_count)
            },
        }
    )
    selection = select_type_shapes(model)
    settings = TypesSettings(
        package,
        "1.0.0",
        None,
        schema_partition_size=1,
        stub_partition_size=1,
    )
    symbols = SymbolProvider(model, selection, package=package)
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
    TypesGenerator().generate(context)
    context.files.commit(output)


@pytest.mark.parametrize(
    ("shape_count", "width"), [(10, 1), (11, 2), (100, 2), (101, 3)]
)
def test_partition_filenames_sort_numerically_and_facades_resolve_them(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    shape_count: int,
    width: int,
) -> None:
    package = f"generated_partitions_{shape_count}"
    output = tmp_path / "output"
    _generate(output, shape_count, package)
    source = output / "src" / package
    private = source / "_private"

    for prefix, extension in (("schemas", "py"), ("models", "pyi")):
        filenames = sorted(
            path.name for path in private.glob(f"{prefix}_*.{extension}")
        )
        assert filenames == [
            f"{prefix}_{index:0{width}d}.{extension}" for index in range(shape_count)
        ]
        assert filenames == sorted(
            filenames, key=lambda name: int(name.split("_")[1].split(".")[0])
        )

    monkeypatch.syspath_prepend(  # pyright: ignore[reportUnknownMemberType]
        str(output / "src")
    )
    facade = importlib.import_module(f"{package}._private.schemas")
    assert not any(
        name.startswith(f"{package}._private.schemas_") for name in sys.modules
    )
    assert str(hydrate(facade.SHAPE0).id) == "example#Shape0"
    last = f"SHAPE{shape_count - 1}"
    assert str(hydrate(getattr(facade, last)).id) == f"example#Shape{shape_count - 1}"
    assert f"{package}._private.schemas_{shape_count - 1:0{width}d}" in sys.modules
    models = importlib.import_module(f"{package}.models")
    assert models.Shape0().__class__.__name__ == "Shape0"
    assert (
        getattr(models, f"Shape{shape_count - 1}")().__class__.__name__
        == f"Shape{shape_count - 1}"
    )

    if shape_count in (11, 101):
        checked = subprocess.run(
            [sys.executable, "-m", "pyright", "src"],
            cwd=output,
            capture_output=True,
            text=True,
            check=False,
        )
        assert checked.returncode == 0, checked.stdout + checked.stderr


def test_regeneration_removes_partitions_with_obsolete_padding(tmp_path: Path) -> None:
    output = tmp_path / "output"
    package = "generated_partition_cleanup"
    private = output / "src" / package / "_private"
    for shape_count, width in ((10, 1), (11, 2), (101, 3), (10, 1)):
        _generate(output, shape_count, package)
        for prefix, extension in (("schemas", "py"), ("models", "pyi")):
            assert {path.name for path in private.glob(f"{prefix}_*.{extension}")} == {
                f"{prefix}_{index:0{width}d}.{extension}"
                for index in range(shape_count)
            }
