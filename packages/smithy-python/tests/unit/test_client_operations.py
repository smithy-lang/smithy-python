# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import importlib
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from smithy_core._schema_compact import hydrate
from smithy_core.schemas import APIOperation
from smithy_core.shapes import ShapeID, ShapeType
from smithy_python.clients import ClientPlan
from smithy_python.dependencies import DependencySet
from smithy_python.files import FileManifest
from smithy_python.generation import ClientSettings, GenerationContext, GenerationPlan
from smithy_python.model import load_model
from smithy_python.models import ModelGenerator
from smithy_python.schemas import SchemaGenerator

_SIGV4 = "aws.auth#sigv4"


def _shapes() -> dict[str, object]:
    return {
        "example#Service": {
            "type": "service",
            "version": "2026-01-01",
            "operations": [
                {"target": "example#GetThing"},
                {"target": "example#PutThing"},
                {"target": "example#Ping"},
            ],
            "errors": [{"target": "example#ServiceFault"}],
            "rename": {"other#Thing": "OtherThing", "other#Missing": "OtherMissing"},
            "traits": {
                "smithy.protocols#rpcv2Cbor": {},
                _SIGV4: {"name": "example"},
                "smithy.api#httpBearerAuth": {},
                "smithy.api#auth": [_SIGV4, "smithy.api#httpBearerAuth"],
            },
        },
        "smithy.protocols#rpcv2Cbor": {
            "type": "structure",
            "traits": {"smithy.api#trait": {}, "smithy.api#protocolDefinition": {}},
        },
        _SIGV4: {
            "type": "structure",
            "members": {"name": {"target": "smithy.api#String"}},
            "traits": {"smithy.api#trait": {}, "smithy.api#authDefinition": {}},
        },
        "example#GetThing": {
            "type": "operation",
            "input": {"target": "example#GetThingInput"},
            "output": {"target": "example#GetThingOutput"},
            "errors": [{"target": "example#Missing"}, {"target": "other#Missing"}],
            "traits": {"smithy.api#readonly": {}, "smithy.api#optionalAuth": {}},
        },
        "example#GetThingInput": {
            "type": "structure",
            "members": {"id": {"target": "smithy.api#String"}},
            "traits": {"smithy.api#input": {}},
        },
        "example#GetThingOutput": {
            "type": "structure",
            "members": {
                "thing": {"target": "example#Thing"},
                "other": {"target": "other#Thing"},
            },
            "traits": {"smithy.api#output": {}},
        },
        "example#PutThing": {
            "type": "operation",
            "input": {"target": "example#Thing"},
            "output": {"target": "other#Thing"},
            "traits": {"smithy.api#auth": ["smithy.api#httpBearerAuth"]},
        },
        "example#Ping": {
            "type": "operation",
            "traits": {"smithy.api#auth": []},
        },
        "example#Thing": {
            "type": "structure",
            "members": {"name": {"target": "smithy.api#String"}},
        },
        "other#Thing": {
            "type": "structure",
            "members": {"count": {"target": "smithy.api#Integer"}},
        },
        "example#Missing": {
            "type": "structure",
            "traits": {"smithy.api#error": "client"},
        },
        "other#Missing": {
            "type": "structure",
            "members": {"code": {"target": "smithy.api#String"}},
            "traits": {"smithy.api#error": "client"},
        },
        "example#ServiceFault": {
            "type": "structure",
            "traits": {"smithy.api#error": "server"},
        },
    }


def _generate(
    output: Path, package: str, *, partition_size: int | None = None
) -> ClientPlan:
    settings = ClientSettings(
        package,
        "1.0.0",
        None,
        schema_partition_size=partition_size,
        stub_partition_size=partition_size,
    )
    plan = ClientPlan.from_model(
        load_model({"smithy": "2.0", "shapes": _shapes()}), settings
    )
    dependencies = DependencySet()
    context = GenerationContext(
        model=plan.model,
        selection=plan.selection,
        settings=settings,
        symbols=plan.symbols,
        plan=GenerationPlan(schemas=plan.schemas, models=plan.models),
        dependencies=dependencies,
        files=FileManifest(dependencies),
    )
    SchemaGenerator().generate(context)
    ModelGenerator().generate(context)
    directory = package.replace(".", "/")
    context.files.python_module(f"src/{directory}/__init__.py", package)
    context.files.python_module(
        f"src/{directory}/_private/__init__.py", f"{package}._private"
    )
    context.files.text_file(f"src/{directory}/py.typed", "")
    context.files.commit(output)
    return plan


def _import(
    monkeypatch: pytest.MonkeyPatch, output: Path, package: str
) -> tuple[ModuleType, ModuleType]:
    monkeypatch.syspath_prepend(  # pyright: ignore[reportUnknownMemberType]
        str(output / "src")
    )
    return (
        importlib.import_module(f"{package}._private.schemas"),
        importlib.import_module(f"{package}.models"),
    )


def test_operation_tuples_reference_dedicated_io_and_effective_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _generate(tmp_path, "client_operation_tuples")
    schemas, _ = _import(monkeypatch, tmp_path, "client_operation_tuples")

    get_thing = schemas.GET_THING
    assert get_thing[:3] == (ShapeType.OPERATION.value, "example", "GetThing")
    assert get_thing[4] is schemas.GET_THING_INPUT
    assert get_thing[5] is schemas.GET_THING_OUTPUT
    assert get_thing[6] == (
        schemas.MISSING,
        schemas.OTHER_MISSING,
        schemas.SERVICE_FAULT,
    )
    assert str(hydrate(get_thing).id) == "example#GetThing"

    ping = schemas.PING
    assert str(hydrate(ping[4]).id) == "example#PingInput"
    assert str(hydrate(ping[5]).id) == "example#PingOutput"
    assert ping[6] == (schemas.SERVICE_FAULT,)

    service = hydrate(schemas.SERVICE)
    assert service.shape_type is ShapeType.SERVICE
    assert {str(trait) for trait in service.traits} >= {
        "smithy.protocols#rpcv2Cbor",
        _SIGV4,
    }


def test_operation_exports_carry_effective_auth_and_resolve_renamed_types(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = _generate(tmp_path, "client_operation_exports")
    assert {
        operation.name: [str(scheme) for scheme in operation.auth_scheme_ids]
        for operation in plan.models.operations
    } == {
        "GET_THING": [_SIGV4, "smithy.api#httpBearerAuth", "smithy.api#noAuth"],
        "PUT_THING": ["smithy.api#httpBearerAuth"],
        "PING": ["smithy.api#noAuth"],
    }
    _, models = _import(monkeypatch, tmp_path, "client_operation_exports")

    assert {"GET_THING", "PUT_THING", "PING"} <= set(models.__all__)
    assert {"GET_THING", "PUT_THING", "PING"} <= set(dir(models))
    put_thing: APIOperation[Any, Any] = models.PUT_THING
    assert isinstance(put_thing, APIOperation)
    assert models.PUT_THING is put_thing
    assert put_thing.effective_auth_schemes == (ShapeID("smithy.api#httpBearerAuth"),)
    assert put_thing.input is models.PutThingInput
    assert put_thing.output is models.PutThingOutput

    get_thing = models.GET_THING
    assert get_thing.error_ids == (
        ShapeID("example#Missing"),
        ShapeID("other#Missing"),
        ShapeID("example#ServiceFault"),
    )
    # other#Missing shares its ID name with example#Missing. The service rename
    # gives it another declaration, which only its full shape ID identifies.
    registry = get_thing.error_registry
    assert registry[ShapeID("example#Missing")] is models.Missing
    assert registry[ShapeID("other#Missing")] is models.OtherMissing
    assert registry[ShapeID("example#ServiceFault")] is models.ServiceFault


def test_operation_exports_load_no_models_until_used(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    package = "client_operation_laziness"
    _generate(tmp_path, package, partition_size=2)
    _, models = _import(monkeypatch, tmp_path, package)
    registry: Any = models._registry  # pyright: ignore[reportPrivateUsage]
    loaded = {name for name in sys.modules if name.startswith(f"{package}._private.")}

    operation = models.GET_THING
    assert not registry._classes  # pyright: ignore[reportPrivateUsage]
    assert {
        name for name in sys.modules if name.startswith(f"{package}._private.")
    } == loaded | {_partition_of(models, "GET_THING")}

    assert operation.input.__name__ == "GetThingInput"
    assert "GetThingOutput" not in registry._classes  # pyright: ignore[reportPrivateUsage]


def _partition_of(models: ModuleType, name: str) -> str:
    package = models.__name__.rsplit(".", 1)[0]
    facade = importlib.import_module(f"{package}._private.schemas")
    partitions: dict[str, int] = facade._PARTITIONS  # pyright: ignore[reportPrivateUsage]
    return f"{package}._private.schemas_{partitions[name]}"


def test_operations_share_a_partition_with_their_dedicated_io(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    package = "client_operation_affinity"
    _generate(tmp_path, package, partition_size=2)
    schemas, _ = _import(monkeypatch, tmp_path, package)
    partitions: dict[str, int] = schemas._PARTITIONS  # pyright: ignore[reportPrivateUsage]
    assert len(set(partitions.values())) > 1
    for operation in ("GET_THING", "PUT_THING", "PING"):
        assert (
            partitions[operation]
            == partitions[f"{operation}_INPUT"]
            == partitions[f"{operation}_OUTPUT"]
        )


@pytest.mark.parametrize("partition_size", [None, 2])
def test_generated_operations_type_check_for_consumers(
    tmp_path: Path, partition_size: int | None
) -> None:
    package = f"client_operation_typing_{partition_size or 0}"
    _generate(tmp_path, package, partition_size=partition_size)
    (tmp_path / "src" / "consumer.py").write_text(
        f"from smithy_core.schemas import APIOperation\n"
        f"from {package} import models\n\n"
        f"operation: APIOperation[models.GetThingInput, models.GetThingOutput] = (\n"
        f"    models.GET_THING\n"
        f")\n"
        f"value: models.GetThingInput = operation.input(id='a')\n"
    )
    checked = subprocess.run(
        [sys.executable, "-m", "pyright", "src"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert checked.returncode == 0, checked.stdout + checked.stderr
