# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
from typing import Any

import pytest
from smithy_python.model import (
    EnumShape,
    IntEnumShape,
    ListShape,
    MapShape,
    MemberShape,
    Model,
    ModelError,
    OperationShape,
    ResourceShape,
    ServiceShape,
    Shape,
    ShapeId,
    ShapeNotFoundError,
    ShapeType,
    SimpleShape,
    StructureShape,
    UnionShape,
    load_model,
)

NS = "com.example"


def _id(name: str) -> ShapeId:
    return ShapeId.from_string(name, default_namespace=NS)


def _load(shapes: dict[str, Any], **extra: Any) -> Model:
    return load_model({"smithy": "2.0", **extra, "shapes": shapes})


SIMPLE_TYPES = [
    "blob",
    "boolean",
    "string",
    "byte",
    "short",
    "integer",
    "long",
    "float",
    "double",
    "bigInteger",
    "bigDecimal",
    "timestamp",
    "document",
]


@pytest.mark.parametrize("type_name", SIMPLE_TYPES)
def test_simple_shape_types(type_name: str) -> None:
    model = _load(
        {f"{NS}#S": {"type": type_name, "traits": {"smithy.api#documentation": "d"}}}
    )
    shape = model.expect_shape(_id("S"), SimpleShape)
    assert shape.type is ShapeType(type_name)
    assert shape.type.value == type_name
    assert shape.traits == {ShapeId.from_string("smithy.api#documentation"): "d"}
    assert shape.members == {}


def test_aggregate_shape_types() -> None:
    model = _load(
        {
            f"{NS}#L": {"type": "list", "member": {"target": "smithy.api#String"}},
            f"{NS}#M": {
                "type": "map",
                "key": {"target": "smithy.api#String"},
                "value": {
                    "target": f"{NS}#L",
                    "traits": {"smithy.api#documentation": "v"},
                },
            },
            f"{NS}#S": {
                "type": "structure",
                "members": {"a": {"target": f"{NS}#M"}},
            },
            f"{NS}#U": {
                "type": "union",
                "members": {"x": {"target": f"{NS}#S"}},
            },
            f"{NS}#E": {
                "type": "enum",
                "members": {
                    "A": {
                        "target": "smithy.api#Unit",
                        "traits": {"smithy.api#enumValue": "a"},
                    }
                },
            },
            f"{NS}#I": {
                "type": "intEnum",
                "members": {
                    "ONE": {
                        "target": "smithy.api#Unit",
                        "traits": {"smithy.api#enumValue": 1},
                    }
                },
            },
        }
    )
    lst = model.expect_shape(_id("L"), ListShape)
    assert lst.type is ShapeType.LIST
    assert lst.member.id == _id("L$member")
    assert lst.member.type is ShapeType.MEMBER
    assert lst.member.target == ShapeId("smithy.api", "String")
    assert lst.member.container == _id("L")
    assert lst.member.name == "member"
    assert list(lst.members) == ["member"]

    mp = model.expect_shape(_id("M"), MapShape)
    assert mp.key.id == _id("M$key")
    assert mp.value.target == _id("L")
    assert mp.value.has_trait("smithy.api#documentation")
    assert list(mp.members) == ["key", "value"]
    assert model.get_target(mp.value) is lst

    struct = model.expect_shape(_id("S"), StructureShape)
    assert struct.type is ShapeType.STRUCTURE
    member = struct.members["a"]
    assert isinstance(member, MemberShape)
    assert model.get_target(member) is mp
    assert model.get_shape(_id("S$a")) is member

    assert model.expect_shape(_id("U"), UnionShape).type is ShapeType.UNION
    enum = model.expect_shape(_id("E"), EnumShape)
    assert enum.members["A"].get_trait("smithy.api#enumValue") == "a"
    int_enum = model.expect_shape(_id("I"), IntEnumShape)
    assert int_enum.members["ONE"].get_trait("smithy.api#enumValue") == 1
    assert model.get_target(int_enum.members["ONE"]).id == ShapeId("smithy.api", "Unit")


def _service_model() -> dict[str, Any]:
    return {
        f"{NS}#Svc": {
            "type": "service",
            "version": "2020-01-01",
            "operations": [{"target": f"{NS}#Zop"}, {"target": f"{NS}#Aop"}],
            "resources": [{"target": f"{NS}#Res"}],
            "errors": [{"target": f"{NS}#Err2"}, {"target": f"{NS}#Err1"}],
            "rename": {f"{NS}#Zed": "Zed2", f"{NS}#Abc": "Abc2"},
        },
        f"{NS}#Res": {
            "type": "resource",
            "identifiers": {
                "zId": {"target": "smithy.api#String"},
                "aId": {"target": "smithy.api#String"},
            },
            "properties": {
                "zProp": {"target": "smithy.api#String"},
                "aProp": {"target": "smithy.api#Integer"},
            },
            "create": {"target": f"{NS}#Create"},
            "put": {"target": f"{NS}#Put"},
            "read": {"target": f"{NS}#Read"},
            "update": {"target": f"{NS}#Update"},
            "delete": {"target": f"{NS}#Delete"},
            "list": {"target": f"{NS}#List"},
            "operations": [{"target": f"{NS}#Zop2"}, {"target": f"{NS}#Aop2"}],
            "collectionOperations": [
                {"target": f"{NS}#Zcol"},
                {"target": f"{NS}#Acol"},
            ],
            "resources": [{"target": f"{NS}#Child"}],
        },
        f"{NS}#Child": {"type": "resource"},
        f"{NS}#Zed": {"type": "string"},
        f"{NS}#Abc": {"type": "string"},
        **{
            f"{NS}#{name}": {"type": "operation"}
            for name in (
                "Aop",
                "Create",
                "Put",
                "Read",
                "Update",
                "Delete",
                "List",
                "Zop2",
                "Aop2",
                "Zcol",
                "Acol",
            )
        },
        f"{NS}#Zop": {
            "type": "operation",
            "input": {"target": f"{NS}#In"},
            "output": {"target": f"{NS}#Out"},
            "errors": [{"target": f"{NS}#Err2"}, {"target": f"{NS}#Err1"}],
        },
        f"{NS}#In": {"type": "structure", "members": {}},
        f"{NS}#Out": {"type": "structure", "members": {}},
        f"{NS}#Err1": {
            "type": "structure",
            "members": {},
            "traits": {"smithy.api#error": "client"},
        },
        f"{NS}#Err2": {
            "type": "structure",
            "members": {},
            "traits": {"smithy.api#error": "server"},
        },
    }


def test_service_resource_operation_properties() -> None:
    model = _load(_service_model())
    svc = model.expect_shape(_id("Svc"), ServiceShape)
    assert svc.type is ShapeType.SERVICE
    assert svc.version == "2020-01-01"
    assert svc.operations == (_id("Zop"), _id("Aop"))
    assert svc.resources == (_id("Res"),)
    assert svc.errors == (_id("Err2"), _id("Err1"))
    assert list(svc.rename.items()) == [(_id("Zed"), "Zed2"), (_id("Abc"), "Abc2")]
    assert model.services() == (svc,)

    res = model.expect_shape(_id("Res"), ResourceShape)
    assert res.type is ShapeType.RESOURCE
    assert list(res.identifiers.items()) == [
        ("zId", ShapeId("smithy.api", "String")),
        ("aId", ShapeId("smithy.api", "String")),
    ]
    assert list(res.properties) == ["zProp", "aProp"]
    assert res.create == _id("Create")
    assert res.put == _id("Put")
    assert res.read == _id("Read")
    assert res.update == _id("Update")
    assert res.delete == _id("Delete")
    assert res.list == _id("List")
    assert res.operations == (_id("Zop2"), _id("Aop2"))
    assert res.collection_operations == (_id("Zcol"), _id("Acol"))
    assert res.resources == (_id("Child"),)

    child = model.expect_shape(_id("Child"), ResourceShape)
    assert child.identifiers == {}
    assert child.create is None
    assert child.operations == ()

    op = model.expect_shape(_id("Zop"), OperationShape)
    assert op.type is ShapeType.OPERATION
    assert op.input == _id("In")
    assert op.output == _id("Out")
    assert op.errors == (_id("Err2"), _id("Err1"))
    # Missing input/output default to smithy.api#Unit.
    aop = model.expect_shape(_id("Aop"), OperationShape)
    assert aop.input == ShapeId("smithy.api", "Unit")
    assert aop.output == ShapeId("smithy.api", "Unit")
    assert aop.errors == ()


def test_service_without_version() -> None:
    model = _load({f"{NS}#Svc": {"type": "service"}})
    svc = model.expect_shape(_id("Svc"), ServiceShape)
    assert svc.version is None
    assert svc.operations == ()
    assert svc.rename == {}


# --- Ordering -------------------------------------------------------------


def test_shape_iteration_follows_input_order() -> None:
    names = ["Zeta", "Alpha", "Mid", "Beta"]
    model = _load({f"{NS}#{n}": {"type": "string"} for n in names})
    assert [s.id.name for s in model.iter_shapes()] == names
    assert [k.name for k in model.shapes if not model.is_prelude(k)] == names


def test_member_trait_and_node_order_preserved() -> None:
    raw: dict[str, Any] = {
        "smithy": "2.0",
        "metadata": {"zeta": 1, "alpha": {"z": 1, "a": [3, 1, 2]}, "mid": None},
        "shapes": {
            f"{NS}#S": {
                "type": "structure",
                "members": {
                    "zulu": {
                        "target": "smithy.api#String",
                        "traits": {
                            "smithy.api#required": {},
                            "smithy.api#documentation": "z",
                        },
                    },
                    "alpha": {"target": "smithy.api#String"},
                    "mike": {"target": "smithy.api#String"},
                },
                "traits": {
                    "com.example#zTrait": {"y": 1, "b": [{"q": 1, "c": 2}], "a": 3},
                    "com.example#aTrait": [3, 2, 1],
                    "com.example#mTrait": True,
                },
            },
            f"{NS}#U": {
                "type": "union",
                "members": {
                    "z": {"target": "smithy.api#String"},
                    "a": {"target": "smithy.api#String"},
                },
            },
            f"{NS}#E": {
                "type": "enum",
                "members": {
                    "Z": {"target": "smithy.api#Unit"},
                    "A": {"target": "smithy.api#Unit"},
                },
            },
            f"{NS}#I": {
                "type": "intEnum",
                "members": {
                    "Z": {
                        "target": "smithy.api#Unit",
                        "traits": {"smithy.api#enumValue": 2},
                    },
                    "A": {
                        "target": "smithy.api#Unit",
                        "traits": {"smithy.api#enumValue": 1},
                    },
                },
            },
            **{f"{NS}#{t}Trait": {"type": "structure", "members": {}} for t in "zam"},
        },
    }
    model = load_model(json.dumps(raw))
    assert list(model.metadata) == ["zeta", "alpha", "mid"]
    alpha = model.metadata["alpha"]
    assert isinstance(alpha, dict)
    assert list(alpha) == ["z", "a"]
    assert alpha["a"] == [3, 1, 2]

    s = model.expect_shape(_id("S"), StructureShape)
    assert list(s.members) == ["zulu", "alpha", "mike"]
    assert [str(k) for k in s.members["zulu"].traits] == [
        "smithy.api#required",
        "smithy.api#documentation",
    ]
    assert [k.name for k in s.traits] == ["zTrait", "aTrait", "mTrait"]
    z_trait = s.get_trait("com.example#zTrait")
    assert isinstance(z_trait, dict)
    assert list(z_trait) == ["y", "b", "a"]
    assert z_trait["b"] == [{"q": 1, "c": 2}]
    assert list(z_trait["b"][0]) == ["q", "c"]  # type: ignore[index]
    assert s.get_trait("com.example#aTrait") == [3, 2, 1]

    assert list(model.expect_shape(_id("U"), UnionShape).members) == ["z", "a"]
    assert list(model.expect_shape(_id("E"), EnumShape).members) == ["Z", "A"]
    assert list(model.expect_shape(_id("I"), IntEnumShape).members) == ["Z", "A"]


def test_trait_values_are_not_coerced() -> None:
    model = _load(
        {
            f"{NS}#S": {
                "type": "string",
                "traits": {
                    "com.example#t": {
                        "float": 1.5,
                        "int": 10,
                        "big": 12345678901234567890123,
                        "null": None,
                        "bool": False,
                        "str": "1",
                    }
                },
            },
            f"{NS}#t": {"type": "structure", "members": {}},
        }
    )
    value = model.get_shape(_id("S")).get_trait("com.example#t")
    assert value == {
        "float": 1.5,
        "int": 10,
        "big": 12345678901234567890123,
        "null": None,
        "bool": False,
        "str": "1",
    }


def test_trait_helpers_accept_relative_prelude_names() -> None:
    model = _load(
        {f"{NS}#S": {"type": "string", "traits": {"smithy.api#documentation": "x"}}}
    )
    shape = model.get_shape(_id("S"))
    assert shape.has_trait("documentation")
    assert shape.get_trait("documentation") == "x"
    assert shape.get_trait(ShapeId("smithy.api", "documentation")) == "x"
    assert shape.get_trait("smithy.api#required") is None
    assert not shape.has_trait(ShapeId("smithy.api", "required"))


def test_relative_ids_in_ast_are_rejected() -> None:
    with pytest.raises(ModelError, match="documentation"):
        _load({f"{NS}#S": {"type": "string", "traits": {"documentation": "x"}}})


# --- Loading inputs -----------------------------------------------------------


@pytest.mark.parametrize("version", ["2.0", "2", "1.0", "1"])
def test_accepted_versions(version: str) -> None:
    model = load_model(json.dumps({"smithy": version, "shapes": {}}).encode())
    assert model.smithy_version == version


def test_loads_bytes_str_and_mapping() -> None:
    raw = {"smithy": "2.0", "shapes": {f"{NS}#S": {"type": "string"}}}
    for source in (json.dumps(raw), json.dumps(raw).encode(), raw):
        assert _id("S") in load_model(source)
    assert _id("S") in load_model(raw)
    assert "com.example#S" in load_model(raw)
    assert "not an id" not in load_model(raw)
    assert 42 not in load_model(raw)


def test_shapes_and_metadata_optional() -> None:
    model = load_model(b'{"smithy": "2.0"}')
    assert model.metadata == {}
    assert list(model.iter_shapes()) == []


# --- Prelude ------------------------------------------------------------------

PRELUDE_NAMES = [
    "String",
    "Blob",
    "BigInteger",
    "BigDecimal",
    "Timestamp",
    "Document",
    "Boolean",
    "Byte",
    "Short",
    "Integer",
    "Long",
    "Float",
    "Double",
    "PrimitiveBoolean",
    "PrimitiveByte",
    "PrimitiveShort",
    "PrimitiveInteger",
    "PrimitiveLong",
    "PrimitiveFloat",
    "PrimitiveDouble",
    "Unit",
]


@pytest.mark.parametrize("name", PRELUDE_NAMES)
def test_prelude_shapes_resolve_without_input(name: str) -> None:
    model = _load(
        {
            f"{NS}#S": {
                "type": "structure",
                "members": {"m": {"target": f"smithy.api#{name}"}},
            }
        }
    )
    target = model.get_target(model.expect_shape(_id("S"), StructureShape).members["m"])
    assert target.id == ShapeId("smithy.api", name)
    assert model.is_prelude(target)
    assert model.is_prelude(target.id)
    assert not model.is_prelude(_id("S"))


def test_prelude_shape_details() -> None:
    model = _load({})
    unit = model.expect_shape(ShapeId("smithy.api", "Unit"), StructureShape)
    assert unit.has_trait("smithy.api#unitType")
    assert unit.members == {}
    prim = model.get_shape(ShapeId("smithy.api", "PrimitiveInteger"))
    assert prim.type is ShapeType.INTEGER
    assert prim.get_trait("smithy.api#default") == 0
    assert (
        model.get_shape(ShapeId("smithy.api", "PrimitiveBoolean")).get_trait(
            "smithy.api#default"
        )
        is False
    )
    assert model.get_shape(ShapeId("smithy.api", "Document")).type is (
        ShapeType.DOCUMENT
    )
    # Prelude shapes are excluded from default iteration.
    assert list(model.iter_shapes()) == []
    assert any(
        s.id == ShapeId("smithy.api", "String")
        for s in model.iter_shapes(include_prelude=True)
    )


def test_input_prelude_shapes_win_and_are_not_duplicated() -> None:
    model = _load(
        {
            "smithy.api#String": {
                "type": "string",
                "traits": {"smithy.api#documentation": "from input"},
            },
            f"{NS}#S": {
                "type": "structure",
                "members": {"m": {"target": "smithy.api#String"}},
            },
        }
    )
    string = model.get_shape(ShapeId("smithy.api", "String"))
    assert string.get_trait("smithy.api#documentation") == "from input"
    assert model.is_prelude(string)
    all_ids = [s.id for s in model.iter_shapes(include_prelude=True)]
    assert all_ids.count(ShapeId("smithy.api", "String")) == 1
    assert len(all_ids) == len(set(all_ids))
    assert [s.id for s in model.iter_shapes()] == [_id("S")]


# --- Navigation ---------------------------------------------------------------


def test_navigation_api() -> None:
    model = _load(_service_model())
    with pytest.raises(ShapeNotFoundError, match=r"com\.example#Nope"):
        model.get_shape(_id("Nope"))
    assert model.find_shape(_id("Nope")) is None
    assert model.find_shape("com.example#Svc") is model.get_shape(_id("Svc"))
    with pytest.raises(ModelError, match="expected StructureShape"):
        model.expect_shape(_id("Svc"), StructureShape)
    ops = [s.id.name for s in model.iter_shapes(OperationShape)]
    assert ops[0] == "Aop"
    assert "Zop" in ops
    assert all(isinstance(s, Shape) for s in model.iter_shapes(include_prelude=True))
    assert [s.id for s in model.iter_shapes(ShapeType.SERVICE)] == [_id("Svc")]


# --- Errors -------------------------------------------------------------------


@pytest.mark.parametrize(
    ("source", "message"),
    [
        (b"{not json", "Invalid JSON"),
        (b"\xff\xfe", "Invalid JSON"),
        (b'{"smithy": "2.0", "metadata": {"x": NaN}}', "Invalid JSON"),
        (b'{"smithy": "2.0", "metadata": {"x": -Infinity}}', "Invalid JSON"),
        (b"[]", "must be a JSON object"),
        (b'{"shapes": {}}', "smithy"),
        (b'{"smithy": "3.0", "shapes": {}}', "Unsupported Smithy version"),
        (b'{"smithy": 2, "shapes": {}}', "smithy"),
        (b'{"smithy": "2.0", "shapes": []}', "shapes"),
        (b'{"smithy": "2.0", "metadata": [], "shapes": {}}', "metadata"),
        (b'{"smithy": "2.0", "shapes": {"a#B": {}}}', "a#B.*type"),
        (b'{"smithy": "2.0", "shapes": {"a#B": 1}}', "a#B"),
        (b'{"smithy": "2.0", "shapes": {"a#B": {"type": "wat"}}}', "wat"),
        (b'{"smithy": "2.0", "shapes": {"a#B": {"type": "member"}}}', "member"),
        (b'{"smithy": "2.0", "shapes": {"bad id": {"type": "string"}}}', "bad id"),
        (b'{"smithy": "2.0", "shapes": {"a#B$c": {"type": "string"}}}', "a#B\\$c"),
        (
            b'{"smithy": "2.0", "shapes": {"a#B": {"type": "list"}}}',
            "a#B.*member",
        ),
        (
            b'{"smithy": "2.0", "shapes": {"a#B": {"type": "structure",'
            b' "members": {"x": {}}}}}',
            "a#B\\$x.*target",
        ),
        (
            b'{"smithy": "2.0", "shapes": {"a#B": {"type": "structure",'
            b' "members": {"x": {"target": "not an id"}}}}}',
            "not an id",
        ),
        (
            b'{"smithy": "2.0", "shapes": {"a#B": {"type": "string", "traits": []}}}',
            "a#B.*traits",
        ),
    ],
)
def test_malformed_input(source: bytes, message: str) -> None:
    with pytest.raises(ModelError, match=message):
        load_model(source)


@pytest.mark.parametrize(
    ("shape", "referrer"),
    [
        (
            {"type": "structure", "members": {"m": {"target": "a#Missing"}}},
            "a#B\\$m",
        ),
        ({"type": "list", "member": {"target": "a#Missing"}}, "a#B\\$member"),
        ({"type": "service", "operations": [{"target": "a#Missing"}]}, "a#B"),
        ({"type": "service", "resources": [{"target": "a#Missing"}]}, "a#B"),
        ({"type": "service", "errors": [{"target": "a#Missing"}]}, "a#B"),
        ({"type": "service", "rename": {"a#Missing": "X"}}, "a#B"),
        ({"type": "operation", "input": {"target": "a#Missing"}}, "a#B"),
        ({"type": "operation", "output": {"target": "a#Missing"}}, "a#B"),
        ({"type": "operation", "errors": [{"target": "a#Missing"}]}, "a#B"),
        ({"type": "resource", "read": {"target": "a#Missing"}}, "a#B"),
        (
            {"type": "resource", "collectionOperations": [{"target": "a#Missing"}]},
            "a#B",
        ),
        (
            {"type": "resource", "identifiers": {"i": {"target": "a#Missing"}}},
            "a#B",
        ),
        (
            {"type": "resource", "properties": {"p": {"target": "a#Missing"}}},
            "a#B",
        ),
        ({"type": "structure", "mixins": [{"target": "a#Missing"}]}, "a#B"),
    ],
)
def test_dangling_references(shape: dict[str, Any], referrer: str) -> None:
    with pytest.raises(ModelError, match=f"{referrer}.*a#Missing"):
        load_model({"smithy": "2.0", "shapes": {"a#B": shape}})


def test_dangling_apply_target() -> None:
    with pytest.raises(ModelError, match=r"apply.*a#Missing"):
        load_model(
            {
                "smithy": "2.0",
                "shapes": {"a#Missing": {"type": "apply", "traits": {}}},
            }
        )
    with pytest.raises(ModelError, match=r"apply.*a#B\$nope"):
        load_model(
            {
                "smithy": "2.0",
                "shapes": {
                    "a#B": {"type": "structure", "members": {}},
                    "a#B$nope": {"type": "apply", "traits": {}},
                },
            }
        )


def test_model_error_is_a_codegen_error() -> None:
    from smithy_python.exceptions import CodegenError

    assert issubclass(ModelError, CodegenError)
