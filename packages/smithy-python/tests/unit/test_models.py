# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
# pyright: reportPrivateUsage=false

from __future__ import annotations

import importlib
import json
import pickle
import subprocess
import sys
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import pytest
from smithy_core.types import UnknownEnumMixin
from smithy_json import JSONCodec
from smithy_python.dependencies import SMITHY_CORE, DependencySet
from smithy_python.files import FileManifest
from smithy_python.generation import GenerationContext, GenerationPlan, TypesSettings
from smithy_python.model import load_model
from smithy_python.models import ModelGenerator, _model_reserved_member_names
from smithy_python.schemas import SchemaGenerator
from smithy_python.selection import select_type_shapes
from smithy_python.symbols import SymbolProvider

_PACKAGE = "generated_types"


def _run_tool(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", *args],
        capture_output=True,
        text=True,
        check=False,
    )


def _context(
    model_data: Mapping[str, object],
    *,
    service_id: str | None = "example#Service",
    package: str = _PACKAGE,
) -> GenerationContext[TypesSettings]:
    model = load_model(model_data)
    selection = select_type_shapes(
        model,
        service_id=service_id,
        generate_inputs_and_outputs=True,
    )
    settings = TypesSettings(package, "1.0.0", None)
    symbols = SymbolProvider(
        model,
        selection,
        package=settings.package,
        reserved_member_names=_model_reserved_member_names(model),
    )
    dependencies = DependencySet()
    return GenerationContext(
        model=model,
        selection=selection,
        settings=settings,
        symbols=symbols,
        plan=GenerationPlan.from_selection(model, selection, symbols),
        dependencies=dependencies,
        files=FileManifest(dependencies),
    )


def _model() -> dict[str, object]:
    return {
        "smithy": "2.0",
        "shapes": {
            "example#Service": {
                "type": "service",
                "version": "1",
                "operations": [{"target": "example#Operation"}],
                "rename": {
                    "example#Original": "Renamed",
                    "example#Choice": "Selection",
                    "example#Color": "Tone",
                },
            },
            "example#Operation": {
                "type": "operation",
                "input": {"target": "example#Input"},
                "output": {"target": "example#Output"},
                "errors": [{"target": "example#Problem"}],
            },
            "example#Input": {
                "type": "structure",
                "traits": {"smithy.api#documentation": "Input docs."},
                "members": {
                    "required": {
                        "target": "smithy.api#String",
                        "traits": {"smithy.api#required": {}},
                    },
                    "list": {"target": "smithy.api#String"},
                    "renamed": {"target": "example#Original"},
                    "choice": {"target": "example#Choice"},
                    "color": {"target": "example#Color"},
                },
            },
            "example#Output": {
                "type": "structure",
                "members": {
                    "responseMetadata": {"target": "smithy.api#String"},
                    "code": {"target": "example#Code"},
                },
            },
            "example#Problem": {
                "type": "structure",
                "traits": {
                    "smithy.api#error": "client",
                    "smithy.api#documentation": "Problem docs.",
                },
                "members": {
                    "message": {
                        "target": "smithy.api#String",
                        "traits": {"smithy.api#sensitive": {}},
                    },
                    "fault": {"target": "smithy.api#String"},
                    "detail": {"target": "example#Original"},
                },
            },
            "example#Original": {
                "type": "structure",
                "traits": {"smithy.api#documentation": "Renamed structure."},
                "members": {
                    "value": {
                        "target": "smithy.api#String",
                        "traits": {
                            "smithy.api#required": {},
                            "smithy.api#documentation": "Value docs.",
                        },
                    },
                    "count": {
                        "target": "smithy.api#PrimitiveInteger",
                        "traits": {"smithy.api#required": {}},
                    },
                },
            },
            "example#Choice": {
                "type": "union",
                "traits": {"smithy.api#documentation": "Choice docs."},
                "members": {
                    "text": {
                        "target": "smithy.api#String",
                        "traits": {"smithy.api#documentation": "Text docs."},
                    },
                    "item": {"target": "example#Original"},
                },
            },
            "example#Color": {
                "type": "enum",
                "traits": {"smithy.api#documentation": "Color docs."},
                "members": {
                    "RED": {
                        "target": "smithy.api#Unit",
                        "traits": {
                            "smithy.api#enumValue": "red",
                            "smithy.api#documentation": "Red docs.",
                        },
                    }
                },
            },
            "example#Code": {
                "type": "intEnum",
                "members": {
                    "OK": {
                        "target": "smithy.api#Unit",
                        "traits": {"smithy.api#enumValue": 200},
                    }
                },
            },
        },
    }


def _generate(tmp_path: Path) -> tuple[GenerationContext[TypesSettings], Path]:
    context = _context(_model())
    SchemaGenerator().generate(context)
    ModelGenerator().generate(context)
    context.files.text_file(f"src/{_PACKAGE}/__init__.py", "")
    context.files.text_file(f"src/{_PACKAGE}/_private/__init__.py", "")
    context.files.commit(tmp_path)
    return context, tmp_path / "src"


def _generate_custom(
    tmp_path: Path,
    model: Mapping[str, object],
    package: str,
) -> Path:
    context = _context(model, service_id=None, package=package)
    SchemaGenerator().generate(context)
    ModelGenerator().generate(context)
    context.files.text_file(f"src/{package}/__init__.py", "")
    context.files.text_file(f"src/{package}/_private/__init__.py", "")
    context.files.commit(tmp_path)
    return tmp_path / "src"


def test_model_plan_precomputes_registry_metadata() -> None:
    plan = _context(_model()).plan.models

    assert plan.renames == {
        "Renamed": "RENAMED",
        "Selection": "SELECTION",
        "Tone": "TONE",
    }
    assert "Original" not in plan.registry_index
    assert plan.registry_index["SelectionText"] == "SELECTION"
    assert plan.registry_index["SelectionUnknown"] == "SELECTION"
    assert plan.target_names["example#Original"] == "Renamed"
    assert plan.target_names["example#Choice"] == "Selection"
    assert plan.target_names["example#Color"] == "Tone"
    assert tuple(plan.registry_index) == (
        "Input",
        "Output",
        "Problem",
        "Renamed",
        "Selection",
        "SelectionText",
        "SelectionItem",
        "SelectionUnknown",
        "Tone",
        "Code",
    )
    assert plan.shape_names == {
        "Input",
        "Output",
        "Problem",
        "Renamed",
        "Selection",
        "Tone",
        "Code",
    }


def test_model_generator_emits_runtime_and_stub(tmp_path: Path) -> None:
    context, source_root = _generate(tmp_path)

    runtime = (source_root / _PACKAGE / "models.py").read_text()
    stub = (source_root / _PACKAGE / "models.pyi").read_text()
    assert "from smithy_core._dynamic_models import ModelRegistry" in runtime
    service_error_doc = (
        "class ServiceError(ModeledError):\n"
        '    """\n'
        "    Base error for all errors in the service.\n"
        "\n"
        "    Some exceptions do not extend from this class, including synthetic,\n"
        "    implicit, and shared exception types.\n"
        '    """'
    )
    assert service_error_doc in runtime
    assert '"Renamed": "RENAMED"' in runtime
    assert '"Original": "RENAMED"' not in runtime
    assert "_MODEL_NAMES = tuple(_MODEL_INDEX)" in runtime
    assert '__all__ = ("ServiceError", *_MODEL_NAMES)' in runtime
    assert "globals()[name] = value" in runtime
    assert "def __dir__() -> list[str]:" in runtime

    assert "class Input(_SerdeShape):" in stub
    assert service_error_doc in stub
    assert '"Input docs."' in stub
    assert "required: str | None = ..." in stub
    assert "list_: str | None = ..." in stub
    assert "class Problem(ServiceError, _SerdeShape):" in stub
    assert "message:" not in stub
    assert "fault_: str | None = ..." in stub
    assert "class Renamed(_SerdeShape):" in stub
    assert '"Value docs."' in stub
    assert "count: int | None = ..." in stub
    assert "class SelectionText(_SerdeShape):" in stub
    assert "Selection = SelectionText | SelectionItem | SelectionUnknown" in stub
    assert "class Tone(UnknownEnumMixin, StrEnum):" in stub
    assert 'RED = "red"' in stub
    assert "class Code(UnknownEnumMixin, IntEnum):" in stub
    assert "OK = 200" in stub
    assert "response_metadata_: str | None = ..." in stub
    assert "response_metadata: ResponseMetadata = ..." in stub
    assert SMITHY_CORE in context.dependencies


def test_generated_models_are_lazy_and_runtime_compatible(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, source_root = _generate(tmp_path)
    monkeypatch.syspath_prepend(  # pyright: ignore[reportUnknownMemberType]
        str(source_root)
    )
    models = importlib.import_module(f"{_PACKAGE}.models")

    assert "Renamed" not in vars(models)
    assert "Renamed" in dir(models)
    renamed = models.Renamed
    assert vars(models)["Renamed"] is renamed
    assert models.Renamed is renamed
    assert renamed.__module__ == f"{_PACKAGE}.models"
    value = renamed(value="hello")
    assert value.value == "hello"
    assert value.count == 0
    assert pickle.loads(pickle.dumps(value)) == value

    def get_input(_: int) -> type[Any]:
        return models.Input

    with ThreadPoolExecutor(max_workers=8) as executor:
        inputs = tuple(executor.map(get_input, range(32)))
    assert len({id(model) for model in inputs}) == 1
    input_ = inputs[0](
        required="yes",
        list_="value",
        renamed=value,
        choice=models.SelectionText(value="selected"),
        color=models.Tone.RED,
    )
    assert input_.list_ == "value"
    assert input_.renamed is value
    decoded = JSONCodec().deserialize(
        (
            b'{"required":"yes","renamed":{"value":"hello"},'
            b'"choice":{"text":"selected"},"color":"red"}'
        ),
        inputs[0],
    )
    assert type(decoded.renamed) is renamed
    assert decoded.renamed.value == "hello"
    assert type(decoded.choice) is models.SelectionText
    assert decoded.choice.value == "selected"
    assert decoded.color is models.Tone.RED
    assert json.loads(JSONCodec().serialize(input_)) == {
        "required": "yes",
        "list": "value",
        "renamed": {"value": "hello", "count": 0},
        "choice": {"text": "selected"},
        "color": "red",
    }

    assert issubclass(models.Problem, models.ServiceError)
    problem = models.Problem("bad", fault_="client", detail=value)
    assert problem.message == "bad"
    assert problem.fault_ == "client"
    assert "bad" not in repr(problem)
    assert models.Problem().message == ""

    assert models.Tone.RED == "red"
    assert issubclass(models.Tone, UnknownEnumMixin)
    assert models.Code.OK == 200
    assert models.SelectionText(value="text").value == "text"
    assert models.SelectionItem(value=value).value is value
    assert models.SelectionUnknown(tag="future").tag == "future"

    namespace: dict[str, object] = {}
    exec(f"from {_PACKAGE}.models import *", namespace)
    assert tuple(name for name in models.__all__ if name not in namespace) == ()
    assert "Original" not in models.__all__
    with pytest.raises(AttributeError):
        models.Original


def test_generated_model_names_do_not_shadow_runtime_helpers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package = "generated_collisions"
    source_root = _generate_custom(
        tmp_path,
        {
            "smithy": "2.0",
            "shapes": {
                f"example#{name}": {"type": "structure"}
                for name in ("ServiceError", "ModelRegistry", "ModeledError")
            },
        },
        package,
    )
    monkeypatch.syspath_prepend(  # pyright: ignore[reportUnknownMemberType]
        str(source_root)
    )
    models = importlib.import_module(f"{package}.models")

    assert models.ServiceError_.__name__ == "ServiceError_"
    assert models.ModelRegistry.__name__ == "ModelRegistry"
    assert models.ModeledError.__name__ == "ModeledError"
    assert models.ServiceError is not models.ServiceError_
    assert {"ServiceError_", "ModelRegistry", "ModeledError"} <= set(models.__all__)


def test_explicit_input_and_output_traits_match_runtime_and_stub(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package = "generated_io_traits"
    source_root = _generate_custom(
        tmp_path,
        {
            "smithy": "2.0",
            "shapes": {
                "example#Input": {
                    "type": "structure",
                    "traits": {"smithy.api#input": {}},
                    "members": {
                        "required": {
                            "target": "smithy.api#String",
                            "traits": {"smithy.api#required": {}},
                        }
                    },
                },
                "example#Output": {
                    "type": "structure",
                    "traits": {"smithy.api#output": {}},
                    "members": {"responseMetadata": {"target": "smithy.api#String"}},
                },
            },
        },
        package,
    )
    stub = (source_root / package / "models.pyi").read_text()
    assert "required: str | None = ..." in stub
    assert "response_metadata_: str | None = ..." in stub
    assert "response_metadata: ResponseMetadata = ..." in stub

    monkeypatch.syspath_prepend(  # pyright: ignore[reportUnknownMemberType]
        str(source_root)
    )
    models = importlib.import_module(f"{package}.models")
    assert models.Input().required is None
    output = models.Output(response_metadata_="modeled")
    assert output.response_metadata_ == "modeled"
    assert output.response_metadata is not None


def test_stub_and_runtime_use_the_same_member_names(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package = "generated_member_names"
    source_root = _generate_custom(
        tmp_path,
        {
            "smithy": "2.0",
            "shapes": {
                "example#Leading": {
                    "type": "structure",
                    "members": {"_value": {"target": "smithy.api#String"}},
                },
                "example#Trailing": {
                    "type": "structure",
                    "members": {"value_": {"target": "smithy.api#String"}},
                },
                "example#Repeated": {
                    "type": "structure",
                    "members": {"some__value": {"target": "smithy.api#String"}},
                },
                "example#Digits": {
                    "type": "structure",
                    "members": {
                        "_1": {"target": "smithy.api#String"},
                        "_2HTTPServer": {"target": "smithy.api#String"},
                    },
                },
                "example#RuntimeMethods": {
                    "type": "structure",
                    "members": {
                        "serialize": {"target": "smithy.api#String"},
                        "serializeMembers": {"target": "smithy.api#String"},
                        "deserialize": {"target": "smithy.api#String"},
                        "__init__": {"target": "smithy.api#String"},
                        "__post_init__": {"target": "smithy.api#String"},
                        "_smithy_default": {"target": "smithy.api#String"},
                        "__repr__": {"target": "smithy.api#String"},
                    },
                },
                "example#Keywords": {
                    "type": "enum",
                    "members": {
                        name: {
                            "target": "smithy.api#Unit",
                            "traits": {"smithy.api#enumValue": name.lower()},
                        }
                        for name in ("LIST", "CLASS")
                    },
                },
                "example#SunderString": {
                    "type": "enum",
                    "members": {
                        "_VALUE_": {
                            "target": "smithy.api#Unit",
                            "traits": {"smithy.api#enumValue": "value"},
                        },
                        "__DUNDER__": {
                            "target": "smithy.api#Unit",
                            "traits": {"smithy.api#enumValue": "dunder"},
                        },
                    },
                },
                "example#SunderInt": {
                    "type": "intEnum",
                    "members": {
                        "_VALUE_": {
                            "target": "smithy.api#Unit",
                            "traits": {"smithy.api#enumValue": 1},
                        },
                        "__DUNDER__": {
                            "target": "smithy.api#Unit",
                            "traits": {"smithy.api#enumValue": 2},
                        },
                    },
                },
                "example#EnumContainer": {
                    "type": "structure",
                    "members": {
                        "stringValue": {"target": "example#SunderString"},
                        "intValue": {"target": "example#SunderInt"},
                    },
                },
            },
        },
        package,
    )
    stub = (source_root / package / "models.pyi").read_text()
    assert "_value: str | None = ..." in stub
    assert "value_: str | None = ..." in stub
    assert "some__value: str | None = ..." in stub
    assert "_1: str | None = ..." in stub
    assert "_2_http_server: str | None = ..." in stub
    assert "serialize_: str | None = ..." in stub
    assert "serialize_members_: str | None = ..." in stub
    assert "deserialize_: str | None = ..." in stub
    assert "__init___: str | None = ..." in stub
    assert "__post_init___: str | None = ..." in stub
    assert "_smithy_default_: str | None = ..." in stub
    assert "__repr___: str | None = ..." in stub
    assert 'LIST_ = "list"' in stub
    assert 'CLASS_ = "class"' in stub
    assert (
        'class SunderString(UnknownEnumMixin, StrEnum):\n    _VALUE__ = "value"' in stub
    )
    assert "class SunderInt(UnknownEnumMixin, IntEnum):\n    _VALUE__ = 1" in stub
    assert '__DUNDER___ = "dunder"' in stub
    assert "__DUNDER___ = 2" in stub

    monkeypatch.syspath_prepend(  # pyright: ignore[reportUnknownMemberType]
        str(source_root)
    )
    models = importlib.import_module(f"{package}.models")
    assert models.Leading(_value="leading")._value == "leading"
    assert models.Trailing(value_="trailing").value_ == "trailing"
    assert models.Repeated(some__value="repeated").some__value == "repeated"
    digits = models.Digits(_1="one", _2_http_server="two")
    assert digits._1 == "one"
    assert digits._2_http_server == "two"
    methods = models.RuntimeMethods(
        serialize_="serialize",
        serialize_members_="members",
        deserialize_="deserialize",
        __init___="init",
        __post_init___="post_init",
        _smithy_default_="default",
        __repr___="repr",
    )
    assert callable(methods.serialize)
    assert callable(methods.serialize_members)
    assert callable(methods.deserialize)
    assert methods.__init___ == "init"
    assert methods.__post_init___ == "post_init"
    assert methods._smithy_default_ == "default"
    assert methods.__repr___ == "repr"
    assert isinstance(methods._smithy_default(), models.RuntimeMethods)
    assert "RuntimeMethods(" in repr(methods)
    assert json.loads(JSONCodec().serialize(methods)) == {
        "serialize": "serialize",
        "serializeMembers": "members",
        "deserialize": "deserialize",
        "__init__": "init",
        "__post_init__": "post_init",
        "_smithy_default": "default",
        "__repr__": "repr",
    }
    assert models.Keywords.LIST_ == "list"
    assert models.Keywords.CLASS_ == "class"
    assert models.SunderString._VALUE__ == "value"
    assert models.SunderInt._VALUE__ == 1
    assert "__DUNDER___" in models.SunderString.__members__
    assert "__DUNDER___" in models.SunderInt.__members__
    value = models.EnumContainer(
        string_value=models.SunderString.__DUNDER___,
        int_value=models.SunderInt.__DUNDER___,
    )
    encoded = JSONCodec().serialize(value)
    decoded = JSONCodec().deserialize(encoded, models.EnumContainer)
    assert decoded.string_value is models.SunderString.__DUNDER___
    assert decoded.int_value is models.SunderInt.__DUNDER___


def test_unit_union_members_round_trip_as_empty_structures(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package = "generated_unit_union"
    source_root = _generate_custom(
        tmp_path,
        {
            "smithy": "2.0",
            "shapes": {
                "example#Action": {
                    "type": "union",
                    "members": {"quit": {"target": "smithy.api#Unit"}},
                },
                "example#Container": {
                    "type": "structure",
                    "members": {"action": {"target": "example#Action"}},
                },
            },
        },
        package,
    )
    runtime = (source_root / package / "models.py").read_text()
    stub = (source_root / package / "models.pyi").read_text()
    assert '_MODEL_NAMES = (*tuple(_MODEL_INDEX), "Unit")' in runtime
    assert "class ActionQuit(_SerdeShape):\n    value: Unit" in stub
    assert "class Unit(_SerdeShape):" in stub

    monkeypatch.syspath_prepend(  # pyright: ignore[reportUnknownMemberType]
        str(source_root)
    )
    models = importlib.import_module(f"{package}.models")
    value = models.Container(action=models.ActionQuit(value=models.Unit()))
    assert json.loads(JSONCodec().serialize(value)) == {"action": {"quit": {}}}
    decoded = JSONCodec().deserialize(b'{"action":{"quit":{}}}', models.Container)
    assert isinstance(decoded.action, models.ActionQuit)
    assert isinstance(decoded.action.value, models.Unit)
    assert "Unit" in models.__all__


def test_modeled_unit_does_not_shadow_prelude_unit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package = "generated_unit_collision"
    source_root = _generate_custom(
        tmp_path,
        {
            "smithy": "2.0",
            "shapes": {
                "example#Unit": {
                    "type": "structure",
                    "members": {"value": {"target": "smithy.api#String"}},
                },
                "example#Action": {
                    "type": "union",
                    "members": {"quit": {"target": "smithy.api#Unit"}},
                },
                "example#Container": {
                    "type": "structure",
                    "members": {"action": {"target": "example#Action"}},
                },
            },
        },
        package,
    )
    stub = (source_root / package / "models.pyi").read_text()
    assert "class Unit_(_SerdeShape):" in stub
    assert "class Unit(_SerdeShape):" in stub

    monkeypatch.syspath_prepend(  # pyright: ignore[reportUnknownMemberType]
        str(source_root)
    )
    models = importlib.import_module(f"{package}.models")
    assert models.Unit_ is not models.Unit
    decoded = JSONCodec().deserialize(
        b'{"action":{"quit":{}}}',
        models.Container,
    )
    assert isinstance(decoded.action.value, models.Unit)


def test_generated_stub_passes_strict_pyright(
    tmp_path: Path,
) -> None:
    _, source_root = _generate(tmp_path)
    (tmp_path / "check.py").write_text(
        (
            f"from {_PACKAGE}.models import Input, Problem, Renamed, SelectionText, Tone\n\n"
            "renamed = Renamed(value='value')\n"
            "Input(required='required', renamed=renamed, "
            "choice=SelectionText(value='x'), color=Tone.RED)\n"
            "problem = Problem('bad')\n"
            "message: str = problem.message\n"
        ),
        encoding="utf-8",
    )
    (tmp_path / "pyrightconfig.json").write_text(
        json.dumps(
            {
                "include": ["check.py"],
                "extraPaths": [str(source_root)],
                "typeCheckingMode": "strict",
            }
        ),
        encoding="utf-8",
    )
    result = _run_tool(
        "pyright",
        "--project",
        str(tmp_path / "pyrightconfig.json"),
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_generated_models_pass_ruff(tmp_path: Path) -> None:
    _, source_root = _generate(tmp_path)
    models = source_root / _PACKAGE / "models.py"
    stub = source_root / _PACKAGE / "models.pyi"
    for command in (("check",), ("format", "--check")):
        result = _run_tool(
            "ruff",
            *command,
            str(models),
            str(stub),
            "--config",
            str(Path(__file__).resolve().parents[4] / "pyproject.toml"),
        )
        assert result.returncode == 0, result.stdout + result.stderr


def test_stub_star_exports_and_private_member_names(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package = "generated_private_names"
    source_root = _generate_custom(
        tmp_path,
        {
            "smithy": "2.0",
            "shapes": {
                "example#_2HTTPServer": {
                    "type": "structure",
                    "members": {
                        "__value": {"target": "smithy.api#String"},
                        "__annotations__": {"target": "smithy.api#String"},
                    },
                }
            },
        },
        package,
    )
    stub = (source_root / package / "models.pyi").read_text()
    assert '"_2HTTPServer",' in stub
    assert "__value___: str | None = ..." in stub
    assert "__annotations___: str | None = ..." in stub

    monkeypatch.syspath_prepend(  # pyright: ignore[reportUnknownMemberType]
        str(source_root)
    )
    models = importlib.import_module(f"{package}.models")
    namespace: dict[str, object] = {}
    exec(f"from {package}.models import *", namespace)
    assert namespace["_2HTTPServer"] is models._2HTTPServer
    value = models._2HTTPServer(
        __value___="value",
        __annotations___="annotations",
    )
    assert value.__value___ == "value"
    assert value.__annotations___ == "annotations"

    (tmp_path / "check.py").write_text(
        (
            f"from {package}.models import *\n\n"
            "value = _2HTTPServer(\n"
            "    __value___='value',\n"
            "    __annotations___='annotations',\n"
            ")\n"
            "member: str | None = value.__value___\n"
        ),
        encoding="utf-8",
    )
    (tmp_path / "pyrightconfig.json").write_text(
        json.dumps(
            {
                "include": ["check.py"],
                "extraPaths": [str(source_root)],
                "typeCheckingMode": "strict",
            }
        ),
        encoding="utf-8",
    )
    result = _run_tool(
        "pyright",
        "--project",
        str(tmp_path / "pyrightconfig.json"),
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_model_output_is_deterministic(tmp_path: Path) -> None:
    outputs: list[tuple[str, str]] = []
    for index in range(2):
        _, source_root = _generate(tmp_path / str(index))
        package = source_root / _PACKAGE
        outputs.append(
            (
                (package / "models.py").read_text(),
                (package / "models.pyi").read_text(),
            )
        )
    assert outputs[0] == outputs[1]


def test_model_generation_without_service(tmp_path: Path) -> None:
    context = _context(
        {
            "smithy": "2.0",
            "shapes": {
                "example#Standalone": {
                    "type": "structure",
                    "members": {"value": {"target": "smithy.api#String"}},
                }
            },
        },
        service_id=None,
    )
    SchemaGenerator().generate(context)
    ModelGenerator().generate(context)
    context.files.commit(tmp_path)

    runtime = (tmp_path / "src" / _PACKAGE / "models.py").read_text()
    stub = (tmp_path / "src" / _PACKAGE / "models.pyi").read_text()
    assert '"Standalone": "STANDALONE"' in runtime
    assert "class Standalone(_SerdeShape):" in stub


def teardown_module() -> None:
    for name in tuple(sys.modules):
        if name == _PACKAGE or name.startswith(f"{_PACKAGE}."):
            del sys.modules[name]
