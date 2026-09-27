# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any

import pytest
from smithy_python.model import (
    EnumShape,
    ListShape,
    Model,
    ModelError,
    OperationShape,
    ResourceShape,
    ServiceShape,
    ShapeId,
    StructureShape,
    load_model,
)

NS = "com.example"
MIXIN: dict[str, Any] = {"smithy.api#mixin": {}}
STRING = {"target": "smithy.api#String"}


def _id(name: str) -> ShapeId:
    return ShapeId.from_string(name, default_namespace=NS)


def _load(shapes: dict[str, Any]) -> Model:
    return load_model({"smithy": "2.0", "shapes": shapes})


def _trait_names(traits: Any) -> list[str]:
    return [str(k) for k in traits]


def test_single_mixin_members_first_and_rooted_at_container() -> None:
    model = _load(
        {
            f"{NS}#Thing": {
                "type": "structure",
                "mixins": [{"target": f"{NS}#Base"}],
                "members": {"zLocal": STRING, "aLocal": STRING},
            },
            f"{NS}#Base": {
                "type": "structure",
                "members": {
                    "zBase": {
                        "target": "smithy.api#String",
                        "traits": {"smithy.api#required": {}},
                    },
                    "aBase": STRING,
                },
                "traits": {**MIXIN, "smithy.api#documentation": "base"},
            },
        }
    )
    thing = model.expect_shape(_id("Thing"), StructureShape)
    assert list(thing.members) == ["zBase", "aBase", "zLocal", "aLocal"]
    assert thing.members["zBase"].id == _id("Thing$zBase")
    assert thing.members["zBase"].has_trait("smithy.api#required")
    assert model.get_shape(_id("Thing$zBase")) is thing.members["zBase"]
    # Inherited traits, minus smithy.api#mixin.
    assert _trait_names(thing.traits) == ["smithy.api#documentation"]
    assert not thing.is_mixin
    assert thing.mixins == (_id("Base"),)

    base = model.expect_shape(_id("Base"), StructureShape)
    assert base.is_mixin
    assert base.members["zBase"].id == _id("Base$zBase")
    # Mixins remain iterable but can be filtered.
    assert [s.id for s in model.iter_shapes() if s.is_mixin] == [_id("Base")]


def test_nested_and_multiple_mixins() -> None:
    model = _load(
        {
            f"{NS}#A": {
                "type": "structure",
                "members": {"a": STRING},
                "traits": {**MIXIN, f"{NS}#fromA": "A", f"{NS}#shared": "A"},
            },
            f"{NS}#B": {
                "type": "structure",
                "mixins": [{"target": f"{NS}#A"}],
                "members": {"b": STRING},
                "traits": {**MIXIN, f"{NS}#fromB": "B"},
            },
            f"{NS}#C": {
                "type": "structure",
                "members": {"c": STRING},
                "traits": {**MIXIN, f"{NS}#shared": "C"},
            },
            f"{NS}#D": {
                "type": "structure",
                "mixins": [{"target": f"{NS}#B"}, {"target": f"{NS}#C"}],
                "members": {"d": STRING},
                "traits": {f"{NS}#local": "D"},
            },
        }
    )
    b = model.expect_shape(_id("B"), StructureShape)
    assert list(b.members) == ["a", "b"]
    assert _trait_names(b.traits) == [
        f"{NS}#fromA",
        f"{NS}#shared",
        "smithy.api#mixin",
        f"{NS}#fromB",
    ]
    d = model.expect_shape(_id("D"), StructureShape)
    assert list(d.members) == ["a", "b", "c", "d"]
    assert [m.id for m in d.members.values()] == [
        _id("D$a"),
        _id("D$b"),
        _id("D$c"),
        _id("D$d"),
    ]
    # Later mixins override earlier ones; positions of first definition kept.
    assert dict(d.traits) == {
        _id("fromA"): "A",
        _id("shared"): "C",
        _id("fromB"): "B",
        _id("local"): "D",
    }
    assert _trait_names(d.traits) == [
        f"{NS}#fromA",
        f"{NS}#shared",
        f"{NS}#fromB",
        f"{NS}#local",
    ]


def test_local_traits_are_not_inherited() -> None:
    model = _load(
        {
            f"{NS}#Base": {
                "type": "structure",
                "members": {},
                "traits": {
                    "smithy.api#internal": {},
                    "smithy.api#documentation": "doc",
                    "smithy.api#mixin": {"localTraits": ["smithy.api#internal"]},
                },
            },
            f"{NS}#Mid": {
                "type": "structure",
                "mixins": [{"target": f"{NS}#Base"}],
                "members": {},
                "traits": {
                    "smithy.api#mixin": {"localTraits": ["smithy.api#documentation"]}
                },
            },
            f"{NS}#Leaf": {
                "type": "structure",
                "mixins": [{"target": f"{NS}#Base"}],
                "members": {},
            },
            f"{NS}#Leaf2": {
                "type": "structure",
                "mixins": [{"target": f"{NS}#Mid"}],
                "members": {},
            },
        }
    )
    leaf = model.get_shape(_id("Leaf"))
    assert _trait_names(leaf.traits) == ["smithy.api#documentation"]
    mid = model.get_shape(_id("Mid"))
    assert _trait_names(mid.traits) == [
        "smithy.api#documentation",
        "smithy.api#mixin",
    ]
    assert dict(model.get_shape(_id("Leaf2")).traits) == {}


def test_local_member_override_merges_traits() -> None:
    model = _load(
        {
            f"{NS}#Base": {
                "type": "structure",
                "members": {
                    "id": {
                        "target": "smithy.api#String",
                        "traits": {
                            "smithy.api#documentation": "base",
                            "smithy.api#required": {},
                        },
                    },
                    "other": STRING,
                },
                "traits": MIXIN,
            },
            f"{NS}#Thing": {
                "type": "structure",
                "mixins": [{"target": f"{NS}#Base"}],
                "members": {
                    "local": STRING,
                    "id": {
                        "target": "smithy.api#String",
                        "traits": {
                            "smithy.api#documentation": "local",
                            "smithy.api#sensitive": {},
                        },
                    },
                },
            },
        }
    )
    thing = model.expect_shape(_id("Thing"), StructureShape)
    assert list(thing.members) == ["id", "other", "local"]
    member = thing.members["id"]
    assert member.id == _id("Thing$id")
    assert _trait_names(member.traits) == [
        "smithy.api#documentation",
        "smithy.api#required",
        "smithy.api#sensitive",
    ]
    assert member.get_trait("smithy.api#documentation") == "local"
    # The mixin itself is untouched.
    base = model.expect_shape(_id("Base"), StructureShape)
    assert base.members["id"].get_trait("smithy.api#documentation") == "base"
    assert not base.members["id"].has_trait("smithy.api#sensitive")


def test_apply_onto_inherited_member_and_mixin_member() -> None:
    model = _load(
        {
            f"{NS}#Base": {
                "type": "structure",
                "members": {
                    "id": {
                        "target": "smithy.api#String",
                        "traits": {"smithy.api#documentation": "base"},
                    },
                    "tag": STRING,
                },
                "traits": MIXIN,
            },
            f"{NS}#Thing": {
                "type": "structure",
                "mixins": [{"target": f"{NS}#Base"}],
                "members": {},
            },
            f"{NS}#Thing$id": {
                "type": "apply",
                "traits": {"smithy.api#documentation": "applied"},
            },
            f"{NS}#Base$tag": {
                "type": "apply",
                "traits": {"smithy.api#length": {"min": 1}},
            },
        }
    )
    thing = model.expect_shape(_id("Thing"), StructureShape)
    assert thing.members["id"].get_trait("smithy.api#documentation") == "applied"
    # Applying to a mixin member propagates to shapes that use the mixin.
    assert thing.members["tag"].get_trait("smithy.api#length") == {"min": 1}
    base = model.expect_shape(_id("Base"), StructureShape)
    assert base.members["id"].get_trait("smithy.api#documentation") == "base"
    assert base.members["tag"].get_trait("smithy.api#length") == {"min": 1}
    # Apply entries are not shapes.
    assert _id("Thing$id") not in {s.id for s in model.iter_shapes()}


def test_apply_entry_preceding_target_shape() -> None:
    # Smithy sorts shape keys, so "ns#Zed$member" can precede "ns#Zed". Apply
    # resolution must not depend on key order.
    model = _load(
        {
            f"{NS}#Zed$member": {
                "type": "apply",
                "traits": {"smithy.api#required": {}},
            },
            f"{NS}#Zed": {
                "type": "structure",
                "members": {"member": STRING},
            },
        }
    )
    zed = model.expect_shape(_id("Zed"), StructureShape)
    assert zed.members["member"].get_trait("smithy.api#required") == {}


def test_apply_onto_member_inherited_through_nested_mixins() -> None:
    # Verified against Smithy 1.73 flattenAndRemoveMixins: an apply onto a
    # member that a mixin itself inherited reaches shapes using that mixin.
    model = _load(
        {
            f"{NS}#Base": {
                "type": "structure",
                "members": {
                    "id": {
                        "target": "smithy.api#String",
                        "traits": {"smithy.api#documentation": "base"},
                    }
                },
                "traits": MIXIN,
            },
            f"{NS}#Mid": {
                "type": "structure",
                "mixins": [{"target": f"{NS}#Base"}],
                "members": {"x": STRING},
                "traits": MIXIN,
            },
            f"{NS}#Mid$id": {
                "type": "apply",
                "traits": {
                    "smithy.api#documentation": "mid",
                    "smithy.api#pattern": "^a$",
                },
            },
            f"{NS}#Leaf": {
                "type": "structure",
                "mixins": [{"target": f"{NS}#Mid"}],
                "members": {},
            },
            f"{NS}#Leaf$x": {
                "type": "apply",
                "traits": {"smithy.api#documentation": "leafx"},
            },
        }
    )
    leaf = model.expect_shape(_id("Leaf"), StructureShape)
    assert list(leaf.members) == ["id", "x"]
    assert dict(leaf.members["id"].traits) == {
        ShapeId.from_string("smithy.api#documentation"): "mid",
        ShapeId.from_string("smithy.api#pattern"): "^a$",
    }
    assert leaf.members["x"].get_trait("documentation") == "leafx"


def test_apply_onto_non_mixin_shapes() -> None:
    model = _load(
        {
            f"{NS}#S": {
                "type": "structure",
                "members": {
                    "m": {
                        "target": "smithy.api#String",
                        "traits": {
                            f"{NS}#tags": ["a"],
                            "smithy.api#documentation": "old",
                        },
                    }
                },
            },
            f"{NS}#L": {"type": "list", "member": STRING},
            f"{NS}#S$m": {
                "type": "apply",
                "traits": {
                    f"{NS}#tags": ["b"],
                    "smithy.api#documentation": "new",
                    "smithy.api#required": {},
                },
            },
            f"{NS}#L$member": {
                "type": "apply",
                "traits": {"smithy.api#length": {"max": 3}},
            },
            "smithy.api#String": {
                "type": "apply",
                "traits": {"smithy.api#documentation": "prelude doc"},
            },
        }
    )
    member = model.expect_shape(_id("S"), StructureShape).members["m"]
    assert _trait_names(member.traits) == [
        f"{NS}#tags",
        "smithy.api#documentation",
        "smithy.api#required",
    ]
    # Array trait values are concatenated per the apply spec.
    assert member.get_trait(f"{NS}#tags") == ["a", "b"]
    assert member.get_trait("smithy.api#documentation") == "new"
    lst = model.expect_shape(_id("L"), ListShape)
    assert lst.member.get_trait("smithy.api#length") == {"max": 3}
    string = model.get_shape(ShapeId("smithy.api", "String"))
    assert string.get_trait("smithy.api#documentation") == "prelude doc"


def test_enum_and_list_mixins() -> None:
    model = _load(
        {
            f"{NS}#BaseEnum": {
                "type": "enum",
                "members": {
                    "Z": {
                        "target": "smithy.api#Unit",
                        "traits": {"smithy.api#enumValue": "z"},
                    }
                },
                "traits": MIXIN,
            },
            f"{NS}#E": {
                "type": "enum",
                "mixins": [{"target": f"{NS}#BaseEnum"}],
                "members": {
                    "A": {
                        "target": "smithy.api#Unit",
                        "traits": {"smithy.api#enumValue": "a"},
                    }
                },
            },
            f"{NS}#BaseList": {
                "type": "list",
                "member": {"target": "smithy.api#String"},
                "traits": {**MIXIN, "smithy.api#length": {"min": 1}},
            },
            f"{NS}#L": {
                "type": "list",
                "mixins": [{"target": f"{NS}#BaseList"}],
            },
            f"{NS}#BaseStr": {"type": "string", "traits": {**MIXIN, "x#y": 1}},
            f"{NS}#Str": {"type": "string", "mixins": [{"target": f"{NS}#BaseStr"}]},
        }
    )
    enum = model.expect_shape(_id("E"), EnumShape)
    assert list(enum.members) == ["Z", "A"]
    assert enum.members["Z"].id == _id("E$Z")
    lst = model.expect_shape(_id("L"), ListShape)
    assert lst.member.id == _id("L$member")
    assert lst.member.target == ShapeId("smithy.api", "String")
    assert lst.get_trait("smithy.api#length") == {"min": 1}
    assert dict(model.get_shape(_id("Str")).traits) == {ShapeId("x", "y"): 1}


def test_service_resource_operation_mixins() -> None:
    model = _load(
        {
            f"{NS}#BaseSvc": {
                "type": "service",
                "version": "1",
                "operations": [{"target": f"{NS}#Op1"}],
                "errors": [{"target": f"{NS}#Err"}],
                "rename": {f"{NS}#Err": "E1", f"{NS}#Op1": "O1"},
                "traits": MIXIN,
            },
            f"{NS}#Svc": {
                "type": "service",
                "mixins": [{"target": f"{NS}#BaseSvc"}],
                "operations": [{"target": f"{NS}#Op2"}],
                "rename": {f"{NS}#Err": "E2"},
            },
            f"{NS}#BaseRes": {
                "type": "resource",
                "identifiers": {"id": STRING},
                "read": {"target": f"{NS}#Op1"},
                "operations": [{"target": f"{NS}#Op1"}],
                "traits": MIXIN,
            },
            f"{NS}#Res": {
                "type": "resource",
                "mixins": [{"target": f"{NS}#BaseRes"}],
                "properties": {"p": STRING},
                "operations": [{"target": f"{NS}#Op2"}],
            },
            f"{NS}#BaseOp": {
                "type": "operation",
                "input": {"target": f"{NS}#In"},
                "errors": [{"target": f"{NS}#Err"}],
                "traits": MIXIN,
            },
            f"{NS}#Op1": {
                "type": "operation",
                "mixins": [{"target": f"{NS}#BaseOp"}],
            },
            f"{NS}#Op2": {"type": "operation"},
            f"{NS}#In": {"type": "structure", "members": {}},
            f"{NS}#Err": {"type": "structure", "members": {}},
        }
    )
    svc = model.expect_shape(_id("Svc"), ServiceShape)
    assert svc.version == "1"
    assert svc.operations == (_id("Op1"), _id("Op2"))
    assert svc.errors == (_id("Err"),)
    assert list(svc.rename.items()) == [(_id("Err"), "E2"), (_id("Op1"), "O1")]
    assert [s.id for s in model.services()] == [_id("Svc")]

    res = model.expect_shape(_id("Res"), ResourceShape)
    assert list(res.identifiers) == ["id"]
    assert list(res.properties) == ["p"]
    assert res.read == _id("Op1")
    assert res.operations == (_id("Op1"), _id("Op2"))

    op = model.expect_shape(_id("Op1"), OperationShape)
    assert op.input == _id("In")
    assert op.output == ShapeId("smithy.api", "Unit")
    assert op.errors == (_id("Err"),)


def test_mixin_errors() -> None:
    with pytest.raises(ModelError, match="cycle"):
        _load(
            {
                f"{NS}#A": {
                    "type": "structure",
                    "mixins": [{"target": f"{NS}#B"}],
                    "traits": MIXIN,
                },
                f"{NS}#B": {
                    "type": "structure",
                    "mixins": [{"target": f"{NS}#A"}],
                    "traits": MIXIN,
                },
            }
        )
    with pytest.raises(ModelError, match=f"{NS}#S.*{NS}#L"):
        _load(
            {
                f"{NS}#L": {"type": "list", "member": STRING, "traits": MIXIN},
                f"{NS}#S": {
                    "type": "structure",
                    "mixins": [{"target": f"{NS}#L"}],
                },
            }
        )
