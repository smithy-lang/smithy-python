# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import importlib.util
import sys
from decimal import Decimal
from pathlib import Path
from types import ModuleType
from typing import get_type_hints

import pytest
from smithy_python.symbols import TypeReference
from smithy_python.writer import PythonWriter


def load_written_module(
    writer: PythonWriter, directory: Path, monkeypatch: pytest.MonkeyPatch
) -> ModuleType:
    path = directory / "written_models.py"
    path.write_text(writer.render(), encoding="utf-8")
    spec = importlib.util.spec_from_file_location("written_models", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)
    return module


def test_nested_forward_and_mutual_annotations(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    writer = PythonWriter("written_models", declarations=("Node", "_2HTTPServer"))
    writer.line("class Node:")
    with writer.indent():
        writer.line(
            "children: ",
            TypeReference(
                "dict",
                "builtins",
                (
                    TypeReference("str", "builtins"),
                    TypeReference(
                        "list",
                        "builtins",
                        (TypeReference("Node", "written_models", nullable=True),),
                        nullable=True,
                    ),
                ),
                nullable=True,
            ),
        )
        writer.line("server: ", TypeReference("_2HTTPServer", "written_models"))
        writer.line("amount: ", TypeReference("Decimal", "decimal"))
        writer.line("nothing: ", TypeReference("None"))
    writer.line()
    writer.line("class _2HTTPServer:")
    with writer.indent():
        writer.line("node: ", TypeReference("Node", "written_models"))
    source = writer.render()
    assert source.startswith("from __future__ import annotations\n")
    assert "from written_models" not in source
    assert "dict[str, list[Node | None] | None] | None" in source
    assert source == writer.render()
    assert source.endswith("\n")
    module = load_written_module(writer, tmp_path, monkeypatch)
    node = module.Node
    server = module._2HTTPServer
    assert get_type_hints(node) == {
        "children": dict[str, list[node | None] | None] | None,
        "server": server,
        "amount": Decimal,
        "nothing": type(None),
    }
    assert get_type_hints(server) == {"node": node}


@pytest.mark.parametrize(
    "name",
    [
        "PythonFinalizationError",  # Added in Python 3.13.
        "_IncompleteInputError",  # Added in Python 3.13.
        "ImportCycleError",  # Added in Python 3.15.
        "__lazy_import__",  # Added in Python 3.15.
        "frozendict",  # Added in Python 3.15.
        "sentinel",  # Added in Python 3.15.
        "WindowsError",  # Windows-only, present throughout Python 3.12-3.15.
    ],
)
def test_imports_reserve_builtins_across_supported_versions(
    name: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    external = ModuleType("external")
    setattr(external, name, str)
    monkeypatch.setitem(sys.modules, "external", external)
    writer = PythonWriter("written_models")
    writer.line("value: ", TypeReference(name, "external"))
    assert f"from external import {name} as _external_{name}" in writer.render()
    module = load_written_module(writer, tmp_path, monkeypatch)
    assert get_type_hints(module) == {"value": str}


def test_indentation_restored_after_exception() -> None:
    writer = PythonWriter("models")
    with pytest.raises(RuntimeError), writer.indent():
        writer.line("first")
        with writer.indent():
            writer.line("second")
            writer.line()
            raise RuntimeError
    writer.line("last")
    assert writer.render().endswith("    first\n        second\n\nlast\n")


@pytest.mark.parametrize("scope", ["declaration", "local"])
@pytest.mark.parametrize(
    "reserved",
    [
        ("Decimal", "list", "int"),
        (
            "\uff24\uff45\uff43\uff49\uff4d\uff41\uff4c",
            "\uff4c\uff49\uff53\uff54",
            "\uff49\uff4e\uff54",
        ),
    ],
)
def test_shadowed_references_load(
    scope: str,
    reserved: tuple[str, ...],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    writer = PythonWriter(
        "written_models",
        declarations=reserved if scope == "declaration" else ("Node",),
        local_names=reserved if scope == "local" else (),
    )
    if scope == "declaration":
        for name in reserved:
            writer.line(name, " = 'shadow'")
    writer.line("class Node:")
    with writer.indent():
        if scope == "local":
            for name in reserved:
                writer.line(name, " = 'shadow'")
        writer.line("amount: ", TypeReference("Decimal", "decimal"))
        writer.line(
            "items: ",
            TypeReference("list", "builtins", (TypeReference("int", "builtins"),)),
        )
    source = writer.render()
    assert "import builtins as _builtins" in source
    assert "from decimal import Decimal as _decimal_Decimal" in source
    module = load_written_module(writer, tmp_path, monkeypatch)
    node: type = module.Node
    assert get_type_hints(node, vars(module), dict(vars(node))) == {
        "amount": Decimal,
        "items": list[int],
    }


def test_all_colliding_imports_are_aliased() -> None:
    for modules in (("alpha.models", "beta.models"), ("beta.models", "alpha.models")):
        writer = PythonWriter("models")
        for module in modules:
            writer.line("value: ", TypeReference("Thing", module))
        source = writer.render()
        assert "from alpha.models import Thing as _alpha_models_Thing" in source
        assert "from beta.models import Thing as _beta_models_Thing" in source
        assert source.index("from alpha") < source.index("from beta")


@pytest.mark.parametrize("name", ["str", "list", "open", "Exception"])
def test_external_builtin_name_is_aliased(name: str) -> None:
    writer = PythonWriter("models")
    writer.line("value: ", TypeReference(name, "external"))
    assert f"from external import {name} as _external_{name}" in writer.render()


@pytest.mark.parametrize(
    "declarations,locals_,refs,conflict",
    [
        (
            ("Decimal", "_decimal_Decimal"),
            (),
            (TypeReference("Decimal", "decimal"),),
            "_decimal_Decimal",
        ),
        ((), ("list", "_builtins"), (TypeReference("list", "builtins"),), "_builtins"),
        (("Node",), ("Node",), (TypeReference("Node", "models"),), "Node"),
        (
            (),
            (),
            (TypeReference("Thing", "a.b"), TypeReference("Thing", "a_b")),
            "_a_b_Thing",
        ),
        (
            ("Decimal",),
            (),
            (
                TypeReference("Decimal", "decimal"),
                TypeReference("_decimal_Decimal", "other"),
            ),
            "_decimal_Decimal",
        ),
        (
            (),
            ("list",),
            (TypeReference("list", "builtins"), TypeReference("_builtins", "other")),
            "_builtins",
        ),
        (("Node", "Node"), (), (), "Node"),
        (("K", "\u212a"), (), (), "\u212a"),
        (
            ("Decimal", "_\uff44\uff45\uff43\uff49\uff4d\uff41\uff4c_Decimal"),
            (),
            (TypeReference("Decimal", "decimal"),),
            "_decimal_Decimal",
        ),
        (("K",), ("\u212a",), (TypeReference("K", "models"),), "K"),
    ],
)
def test_binding_conflicts(
    declarations: tuple[str, ...],
    locals_: tuple[str, ...],
    refs: tuple[TypeReference, ...],
    conflict: str,
) -> None:
    from smithy_python.exceptions import CodegenError

    with pytest.raises(CodegenError, match=conflict):
        writer = PythonWriter("models", declarations=declarations, local_names=locals_)
        for ref in refs:
            writer.line("value: ", ref)
        writer.render()


def test_equivalent_import_names_are_aliased() -> None:
    writer = PythonWriter("models")
    writer.line("first: ", TypeReference("K", "alpha"))
    writer.line("second: ", TypeReference("\u212a", "beta"))
    writer.line("text: ", TypeReference("\uff53\uff54\uff52", "external"))
    source = writer.render()
    assert "from alpha import K as _alpha_K" in source
    assert "from beta import \u212a as _beta_\u212a" in source
    assert (
        "from external import \uff53\uff54\uff52 as _external_\uff53\uff54\uff52"
        in source
    )


def test_current_module_reference_reserves_its_binding() -> None:
    writer = PythonWriter("models")
    writer.line("first: ", TypeReference("Decimal", "models"))
    writer.line("second: ", TypeReference("Decimal", "decimal"))
    assert "from decimal import Decimal as _decimal_Decimal" in writer.render()


def test_nullable_none_is_still_literal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    writer = PythonWriter("written_models")
    writer.line("value: ", TypeReference("None", nullable=True))
    module = load_written_module(writer, tmp_path, monkeypatch)
    assert get_type_hints(module) == {"value": type(None)}


def test_render_replans_without_changing_previous_lines() -> None:
    writer = PythonWriter("models")
    writer.line("first: ", TypeReference("Thing", "alpha"))
    assert "first: Thing" in writer.render()
    writer.line("second: ", TypeReference("Thing", "beta"))
    assert "first: _alpha_Thing" in writer.render()
    assert "second: _beta_Thing" in writer.render()
    assert writer.render() == writer.render()


def test_deep_collection_rendering() -> None:
    ref = TypeReference("str", "builtins")
    for _ in range(1200):
        ref = TypeReference("list", "builtins", (ref,))
    writer = PythonWriter("models")
    writer.line("value: ", ref)
    assert writer.render().endswith(
        "value: " + "list[" * 1200 + "str" + "]" * 1200 + "\n"
    )


def test_future_import_name_is_reserved() -> None:
    writer = PythonWriter("models")
    writer.line("value: ", TypeReference("annotations", "external"))
    assert (
        "from external import annotations as _external_annotations" in writer.render()
    )


@pytest.mark.parametrize(
    "reference",
    [
        TypeReference("Nope"),
        TypeReference("None", arguments=(TypeReference("str", "builtins"),)),
    ],
)
def test_only_none_literal_can_omit_module(reference: TypeReference) -> None:
    from smithy_python.exceptions import CodegenError

    writer = PythonWriter("models")
    writer.line("value: ", reference)
    with pytest.raises(CodegenError, match="module"):
        writer.render()


def test_generation_without_runtime_packages() -> None:
    import subprocess

    source_path = Path(__file__).resolve().parents[2] / "src"
    program = (
        "import sys, importlib.util\n"
        f"sys.path.insert(0, {str(source_path)!r})\n"
        "assert importlib.util.find_spec('smithy_core') is None\n"
        "from smithy_python.writer import PythonWriter\n"
        "from smithy_python.symbols import TypeReference\n"
        "writer = PythonWriter('models')\n"
        "writer.line('document: ', TypeReference('Document', 'smithy_core.documents'))\n"
        "assert 'from smithy_core.documents import Document' in writer.render()\n"
        "assert 'smithy_core' not in sys.modules\n"
    )
    result = subprocess.run(
        [sys.executable, "-I", "-S", "-c", program],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_empty_writer_and_trusted_text() -> None:
    writer = PythonWriter("models", local_names=("value", "value"))
    assert writer.render() == "from __future__ import annotations\n"
    writer.line("value = '$T {not_a_template}'")
    assert writer.render().endswith("value = '$T {not_a_template}'\n")


def test_import_identity_and_order() -> None:
    refs = (
        TypeReference("Decimal", "decimal"),
        TypeReference("datetime", "datetime"),
        TypeReference("Decimal", "decimal", nullable=True),
        TypeReference("list", "builtins", (TypeReference("Decimal", "decimal"),)),
    )
    prefixes: list[str] = []
    for order in (refs, tuple(reversed(refs))):
        writer = PythonWriter("models")
        for ref in order:
            writer.line("value: ", ref)
        prefix = writer.render().split("value:")[0]
        assert prefix.count("from decimal import Decimal") == 1
        assert prefix.index("from datetime") < prefix.index("from decimal")
        prefixes.append(prefix)
    assert prefixes[0] == prefixes[1]
