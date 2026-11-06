# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
# pyright: reportPrivateUsage=false

from __future__ import annotations

import importlib
import runpy
import sys
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Any, cast

import pytest
from smithy_core import _schema_compact, prelude
from smithy_core.shapes import ShapeType as RuntimeShapeType
from smithy_core.traits import DefaultTrait, RequiredTrait, XMLNamespaceTrait
from smithy_python.dependencies import SMITHY_CORE, DependencySet
from smithy_python.exceptions import CodegenError
from smithy_python.files import FileManifest
from smithy_python.generation import GenerationContext, GenerationPlan, TypesSettings
from smithy_python.model import ShapeId, load_model
from smithy_python.schemas import (
    _ENCODING_VERSION,
    _PRELUDE_INTS,
    _TRAIT_BITS,
    _TYPE_INTS,
    _UNIT_INT,
    SchemaGenerator,
    _StringStore,
)
from smithy_python.selection import select_type_shapes
from smithy_python.symbols import SymbolProvider


def _context(
    model_data: Mapping[str, object],
    *,
    schema_partition_size: int | None = 250,
) -> GenerationContext[TypesSettings]:
    model = load_model(model_data)
    selection = select_type_shapes(model, generate_inputs_and_outputs=True)
    settings = TypesSettings(
        "example.types",
        "1.0.0",
        None,
        schema_partition_size=schema_partition_size,
    )
    symbols = SymbolProvider(model, selection, package=settings.package)
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


def test_compact_encoding_contract_matches_runtime() -> None:
    assert _ENCODING_VERSION == _schema_compact._ENCODING_VERSION
    assert tuple(map(str, _TRAIT_BITS)) == _schema_compact._TRAIT_BITS
    assert _UNIT_INT == _schema_compact.UNIT
    assert {*_PRELUDE_INTS.values(), _UNIT_INT} == set(_schema_compact._PRELUDE)
    for shape_type, integer in _TYPE_INTS.items():
        assert RuntimeShapeType[shape_type.name].value == integer


def test_schema_plan_filters_traits_and_synthesizes_input_output() -> None:
    context = _context(
        {
            "smithy": "2.0",
            "shapes": {
                "example#protocol": {
                    "type": "structure",
                    "traits": {
                        "smithy.api#trait": {},
                        "smithy.api#protocolDefinition": {
                            "traits": ["example#wireTrait"]
                        },
                    },
                },
                "example#wireTrait": {
                    "type": "structure",
                    "traits": {"smithy.api#trait": {}},
                },
                "example#Data": {
                    "type": "structure",
                    "traits": {
                        "example#protocol": {},
                        "example#wireTrait": {"enabled": True},
                        "example#ignored": "no",
                    },
                    "members": {
                        "emptyDocument": {
                            "target": "smithy.api#Document",
                            "traits": {"smithy.api#default": {}},
                        },
                        "nullDocument": {
                            "target": "smithy.api#Document",
                            "traits": {"smithy.api#default": None},
                        },
                        "required": {
                            "target": "smithy.api#String",
                            "traits": {"smithy.api#required": {}},
                        },
                    },
                },
                "example#Operation": {
                    "type": "operation",
                    "input": {"target": "example#Data"},
                    "output": {"target": "example#Data"},
                },
            },
        }
    )
    plan = context.plan.schemas
    data = ShapeId.from_string("example#Data")
    traits = plan.traits[data]
    assert not isinstance(traits, int)
    assert tuple(map(str, traits)) == (
        "example#protocol",
        "example#wireTrait",
        "smithy.api#input",
        "smithy.api#output",
    )
    assert traits[ShapeId.from_string("example#protocol")] is None
    assert traits[ShapeId.from_string("example#wireTrait")] == MappingProxyType(
        {"enabled": True}
    )
    assert traits[ShapeId.from_string("smithy.api#input")] is None
    assert traits[ShapeId.from_string("smithy.api#output")] is None

    empty_traits = plan.traits[ShapeId.from_string("example#Data$emptyDocument")]
    null_traits = plan.traits[ShapeId.from_string("example#Data$nullDocument")]
    required = plan.traits[ShapeId.from_string("example#Data$required")]
    assert not isinstance(empty_traits, int)
    assert not isinstance(null_traits, int)
    assert empty_traits[ShapeId.from_string("smithy.api#default")] == MappingProxyType(
        {}
    )
    assert null_traits[ShapeId.from_string("smithy.api#default")] is None
    assert required == 1
    assert "example#ignored" not in plan.strings


@pytest.mark.parametrize("value", [float("inf"), float("-inf"), float("nan")])
def test_schema_generator_rejects_non_finite_trait_values(value: float) -> None:
    context = _context(
        {
            "smithy": "2.0",
            "shapes": {
                "example#Value": {
                    "type": "structure",
                    "members": {
                        "value": {
                            "target": "smithy.api#String",
                            "traits": {"smithy.api#default": value},
                        }
                    },
                }
            },
        }
    )

    with pytest.raises(CodegenError, match="non-finite numeric trait value"):
        SchemaGenerator().generate(context)


def test_string_store_uses_short_monotonic_aliases() -> None:
    strings = _StringStore()

    assert strings.intern("example", preferred="n") == "n0"
    aliases = tuple(strings.intern(f"value{index}") for index in range(2_000))

    assert aliases[0] == "_s0"
    assert aliases[-1] == "_s1999"
    assert len(set(aliases)) == len(aliases)
    assert max(map(len, aliases)) == 6


def test_schema_generator_emits_lazy_hydratable_schemas(tmp_path: Path) -> None:
    context = _context(
        {
            "smithy": "2.0",
            "shapes": {
                "example#Name": {
                    "type": "string",
                    "traits": {"smithy.api#sensitive": {}},
                },
                "example#Choice": {
                    "type": "enum",
                    "members": {
                        "ONE": {
                            "target": "smithy.api#Unit",
                            "traits": {"smithy.api#enumValue": "one"},
                        }
                    },
                },
                "example#Node": {
                    "type": "structure",
                    "members": {
                        "name": {
                            "target": "example#Name",
                            "traits": {"smithy.api#required": {}},
                        },
                        "next": {"target": "example#Node"},
                        "choice": {"target": "example#Choice"},
                    },
                },
            },
        }
    )
    SchemaGenerator().generate(context)
    assert SMITHY_CORE in context.dependencies
    context.files.commit(tmp_path)

    path = tmp_path / "src/example/types/_private/schemas.py"
    source = path.read_text()
    assert "from smithy_core._schema_compact import StaticSchema" in source
    assert "lambda: NODE" in source
    assert "MappingProxyType" not in source

    values = runpy.run_path(str(path))
    static_name = cast(tuple[Any, ...], values["NAME"])
    static_node = cast(tuple[Any, ...], values["NODE"])
    static_choice = cast(tuple[Any, ...], values["CHOICE"])
    assert static_name == (RuntimeShapeType.STRING.value, "example", "Name", 1 << 2)
    assert static_node[5][0][1] == 1
    assert callable(static_node[5][1][0])
    assert static_choice[5][0][0] == _UNIT_INT

    node = _schema_compact.hydrate(static_node)
    assert str(node.id) == "example#Node"
    assert tuple(node.members) == ("name", "next", "choice")
    assert node.members_by_index[0].expect_member_index() == 0
    assert node.members_by_index[0].get_trait(RequiredTrait) is not None
    assert node.members_by_index[1].expect_member_target() is node
    assert str(node.members_by_index[2].expect_member_target().id) == "example#Choice"


def test_schema_generator_partitions_behind_lazy_facade(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _context(
        {
            "smithy": "2.0",
            "shapes": {
                "example#Leaf": {"type": "string"},
                "example#Node": {
                    "type": "structure",
                    "members": {"leaf": {"target": "example#Leaf"}},
                },
                "example#CycleA": {
                    "type": "structure",
                    "members": {"b": {"target": "example#CycleB"}},
                },
                "example#CycleB": {
                    "type": "structure",
                    "members": {"a": {"target": "example#CycleA"}},
                },
            },
        },
        schema_partition_size=1,
    )
    SchemaGenerator().generate(context)
    context.files.text_file("src/example/types/__init__.py", "")
    context.files.text_file("src/example/types/_private/__init__.py", "")
    context.files.commit(tmp_path)

    package = tmp_path / "src/example/types/_private"
    assert (package / "schemas.py").is_file()
    assert (package / "schemas_0.py").is_file()
    assert (package / "schemas_1.py").is_file()
    facade_source = (package / "schemas.py").read_text()
    assert "_PARTITION_NAMES: tuple[tuple[str, ...], ...]" in facade_source
    assert "name: index" in facade_source
    assert facade_source.count(".schemas_") == 1
    partitions = tuple(package.glob("schemas_*.py"))
    cycle = next(
        path.read_text() for path in partitions if "CYCLE_A:" in path.read_text()
    )
    assert "CYCLE_B:" in cycle

    monkeypatch.syspath_prepend(  # pyright: ignore[reportUnknownMemberType]
        str(tmp_path / "src")
    )
    facade = importlib.import_module("example.types._private.schemas")
    assert "example.types._private.schemas_0" not in sys.modules
    assert "example.types._private.schemas_1" not in sys.modules

    static_node = cast(tuple[Any, ...], facade.NODE)
    assert facade.NODE is static_node
    assert "NODE" in dir(facade)
    assert "example.types._private.schemas_1" in sys.modules
    assert "example.types._private.schemas_0" not in sys.modules
    with pytest.raises(AttributeError):
        facade.MISSING
    node = _schema_compact.hydrate(static_node)
    assert str(node.members["leaf"].expect_member_target().id) == "example#Leaf"
    assert "example.types._private.schemas_0" in sys.modules
    cycle_a = _schema_compact.hydrate(cast(tuple[Any, ...], facade.CYCLE_A))
    cycle_b = cycle_a.members["b"].expect_member_target()
    assert cycle_b.members["a"].expect_member_target() is cycle_a


@pytest.mark.parametrize(("shape_count", "partition_count"), [(250, 0), (251, 2)])
def test_schema_partition_threshold(
    tmp_path: Path,
    shape_count: int,
    partition_count: int,
) -> None:
    context = _context(
        {
            "smithy": "2.0",
            "shapes": {
                f"example#Shape{index}": {"type": "structure"}
                for index in range(shape_count)
            },
        },
    )
    SchemaGenerator().generate(context)
    context.files.commit(tmp_path)

    private = tmp_path / "src/example/types/_private"
    assert len(tuple(private.glob("schemas_*.py"))) == partition_count
    facade = (private / "schemas.py").read_text()
    assert ("_PARTITIONS" in facade) is bool(partition_count)


def test_schema_partitions_balance_emitted_size(tmp_path: Path) -> None:
    context = _context(
        {
            "smithy": "2.0",
            "shapes": {
                "example#AHeavy": {
                    "type": "structure",
                    "members": {
                        f"member{index}": {"target": "smithy.api#String"}
                        for index in range(20)
                    },
                },
                "example#BTiny": {"type": "structure"},
                "example#CTiny": {"type": "structure"},
                "example#DTiny": {"type": "structure"},
            },
        },
        schema_partition_size=2,
    )
    SchemaGenerator().generate(context)
    context.files.commit(tmp_path)
    private = tmp_path / "src/example/types/_private"

    first = (private / "schemas_0.py").read_text()
    second = (private / "schemas_1.py").read_text()
    assert "A_HEAVY:" in first
    assert "B_TINY:" not in first
    assert all(f"{name}:" in second for name in ("B_TINY", "C_TINY", "D_TINY"))


def test_schema_partition_weights_include_interned_strings(tmp_path: Path) -> None:
    context = _context(
        {
            "smithy": "2.0",
            "shapes": {
                "example#AHeavy": {
                    "type": "structure",
                    "members": {
                        "value": {
                            "target": "smithy.api#String",
                            "traits": {"smithy.api#default": "x" * 10_000},
                        }
                    },
                },
                "example#BTiny": {"type": "structure"},
                "example#CTiny": {"type": "structure"},
                "example#DTiny": {"type": "structure"},
            },
        },
        schema_partition_size=2,
    )
    SchemaGenerator().generate(context)
    context.files.commit(tmp_path)
    private = tmp_path / "src/example/types/_private"

    first = (private / "schemas_0.py").read_text()
    second = (private / "schemas_1.py").read_text()
    assert "A_HEAVY:" in first
    assert "B_TINY:" not in first
    assert all(f"{name}:" in second for name in ("B_TINY", "C_TINY", "D_TINY"))


def test_schema_generator_preserves_primitive_prelude_targets(tmp_path: Path) -> None:
    context = _context(
        {
            "smithy": "2.0",
            "shapes": {
                "example#Data": {
                    "type": "structure",
                    "members": {
                        "boolean": {"target": "smithy.api#PrimitiveBoolean"},
                        "byte": {"target": "smithy.api#PrimitiveByte"},
                        "short": {"target": "smithy.api#PrimitiveShort"},
                        "integer": {"target": "smithy.api#PrimitiveInteger"},
                        "long": {"target": "smithy.api#PrimitiveLong"},
                        "float": {"target": "smithy.api#PrimitiveFloat"},
                        "double": {"target": "smithy.api#PrimitiveDouble"},
                    },
                }
            },
        }
    )
    SchemaGenerator().generate(context)
    context.files.commit(tmp_path)
    values = runpy.run_path(str(tmp_path / "src/example/types/_private/schemas.py"))
    data = _schema_compact.hydrate(cast(tuple[Any, ...], values["DATA"]))
    expected = {
        "boolean": (prelude.PRIMITIVE_BOOLEAN, False),
        "byte": (prelude.PRIMITIVE_BYTE, 0),
        "short": (prelude.PRIMITIVE_SHORT, 0),
        "integer": (prelude.PRIMITIVE_INTEGER, 0),
        "long": (prelude.PRIMITIVE_LONG, 0),
        "float": (prelude.PRIMITIVE_FLOAT, 0),
        "double": (prelude.PRIMITIVE_DOUBLE, 0),
    }
    for name, (schema, default) in expected.items():
        target = data.members[name].expect_member_target()
        assert target is schema
        trait = target.get_trait(DefaultTrait)
        assert trait is not None
        assert trait.value == default


def test_schema_generator_emits_immutable_trait_documents(tmp_path: Path) -> None:
    context = _context(
        {
            "smithy": "2.0",
            "shapes": {
                "example#Data": {
                    "type": "structure",
                    "traits": {
                        "smithy.api#xmlNamespace": {
                            "uri": "https://example.com",
                            "values": [{"name": "one"}],
                        }
                    },
                    "members": {
                        "document": {
                            "target": "smithy.api#Document",
                            "traits": {"smithy.api#default": {}},
                        }
                    },
                }
            },
        }
    )
    SchemaGenerator().generate(context)
    context.files.commit(tmp_path)
    path = tmp_path / "src/example/types/_private/schemas.py"
    source = path.read_text()
    assert "from types import MappingProxyType" in source
    assert "MappingProxyType[str, object]({})" in source

    values = runpy.run_path(str(path))
    data = _schema_compact.hydrate(cast(tuple[Any, ...], values["DATA"]))
    namespace = data.get_trait(XMLNamespaceTrait)
    assert namespace is not None
    document = namespace.document_value
    assert isinstance(document, MappingProxyType)
    assert isinstance(cast(Mapping[str, object], document)["values"], tuple)


def test_schema_output_is_deterministic(tmp_path: Path) -> None:
    model = {
        "smithy": "2.0",
        "shapes": {
            "example#B": {"type": "string"},
            "example#A": {
                "type": "structure",
                "members": {"b": {"target": "example#B"}},
            },
        },
    }
    outputs: list[str] = []
    for index in range(2):
        context = _context(model)
        SchemaGenerator().generate(context)
        output = tmp_path / str(index)
        context.files.commit(output)
        outputs.append((output / "src/example/types/_private/schemas.py").read_text())
    assert outputs[0] == outputs[1]


def test_schema_names_are_deconflicted_for_private_dependencies(
    tmp_path: Path,
) -> None:
    context = _context(
        {
            "smithy": "2.0",
            "shapes": {
                "a#Name": {"type": "string"},
                "b#Name": {"type": "integer"},
                "a#First": {
                    "type": "structure",
                    "members": {"value": {"target": "a#Name"}},
                },
                "b#Second": {
                    "type": "structure",
                    "members": {"value": {"target": "b#Name"}},
                },
            },
        }
    )
    names = context.plan.schemas.names
    assert names[ShapeId.from_string("a#Name")] == "NAME"
    assert names[ShapeId.from_string("b#Name")] == "NAME_2"

    SchemaGenerator().generate(context)
    context.files.commit(tmp_path)
    values = runpy.run_path(str(tmp_path / "src/example/types/_private/schemas.py"))
    first = _schema_compact.hydrate(cast(tuple[Any, ...], values["FIRST"]))
    second = _schema_compact.hydrate(cast(tuple[Any, ...], values["SECOND"]))
    assert first.members["value"].shape_type is RuntimeShapeType.STRING
    assert second.members["value"].shape_type is RuntimeShapeType.INTEGER
