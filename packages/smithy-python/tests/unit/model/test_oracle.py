# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Compare loaded models against Smithy's ``flattenAndRemoveMixins`` output."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from smithy_python.model import (
    ListShape,
    MapShape,
    MemberShape,
    Model,
    OperationShape,
    ResourceShape,
    ServiceShape,
    Shape,
    ShapeId,
    ShapeType,
    load_model,
)

FIXTURES = Path(__file__).parent / "fixtures"
UNIT = ShapeId("smithy.api", "Unit")


def _ref(shape_id: ShapeId) -> dict[str, str]:
    return {"target": str(shape_id)}


def _member(member: MemberShape) -> dict[str, Any]:
    node: dict[str, Any] = {"target": str(member.target)}
    if member.traits:
        node["traits"] = {str(k): v for k, v in member.traits.items()}
    return node


def _to_ast(shape: Shape) -> dict[str, Any]:
    """Serialize a shape into the JSON AST form Smithy emits."""
    node: dict[str, Any] = {"type": shape.type.value}
    match shape:
        case ListShape():
            node["member"] = _member(shape.member)
        case MapShape():
            node["key"] = _member(shape.key)
            node["value"] = _member(shape.value)
        case ServiceShape():
            if shape.version is not None:
                node["version"] = shape.version
            for key, ids in (
                ("operations", shape.operations),
                ("resources", shape.resources),
                ("errors", shape.errors),
            ):
                if ids:
                    node[key] = [_ref(i) for i in ids]
            if shape.rename:
                node["rename"] = {str(k): v for k, v in shape.rename.items()}
        case ResourceShape():
            for key, named in (
                ("identifiers", shape.identifiers),
                ("properties", shape.properties),
            ):
                if named:
                    node[key] = {k: _ref(v) for k, v in named.items()}
            for key, value in (
                ("create", shape.create),
                ("put", shape.put),
                ("read", shape.read),
                ("update", shape.update),
                ("delete", shape.delete),
                ("list", shape.list),
            ):
                if value is not None:
                    node[key] = _ref(value)
            for key, ids in (
                ("operations", shape.operations),
                ("collectionOperations", shape.collection_operations),
                ("resources", shape.resources),
            ):
                if ids:
                    node[key] = [_ref(i) for i in ids]
        case OperationShape():
            if shape.input != UNIT:
                node["input"] = _ref(shape.input)
            if shape.output != UNIT:
                node["output"] = _ref(shape.output)
            if shape.errors:
                node["errors"] = [_ref(i) for i in shape.errors]
        case _:
            if shape.type in (
                ShapeType.STRUCTURE,
                ShapeType.UNION,
                ShapeType.ENUM,
                ShapeType.INT_ENUM,
            ):
                node["members"] = {
                    name: _member(m) for name, m in shape.members.items()
                }
    if shape.traits:
        node["traits"] = {str(k): v for k, v in shape.traits.items()}
    return node


def _member_orders(node: dict[str, Any]) -> list[str]:
    return list(node.get("members", {}))


def _generated(model: Model) -> dict[str, Shape]:
    return {str(s.id): s for s in model.iter_shapes() if not s.is_mixin}


def _normalize_unit_io(node: dict[str, Any]) -> dict[str, Any]:
    """Drop explicit ``smithy.api#Unit`` operation input/output.

    The model always exposes input/output (defaulting to Unit), so an explicit
    Unit and an absent one are the same thing semantically.
    """
    if node["type"] != "operation":
        return node
    return {
        k: v
        for k, v in node.items()
        if not (k in ("input", "output") and v == _ref(UNIT))
    }


@pytest.mark.parametrize("name", ["mini", "weather"])
def test_matches_smithy_flattened_oracle(name: str) -> None:
    model = load_model((FIXTURES / f"{name}.json").read_bytes())
    oracle = json.loads((FIXTURES / f"{name}.flat.json").read_text())

    shapes = _generated(model)
    # Same shapes, in the same (input) order.
    assert list(shapes) == list(oracle["shapes"])
    assert model.metadata == oracle.get("metadata", {})

    for shape_id, expected in oracle["shapes"].items():
        expected = _normalize_unit_io(expected)
        actual = _to_ast(shapes[shape_id])
        assert actual == expected, shape_id
        # Dict equality ignores key order, so check member order and the
        # order-sensitive serialization of every trait value explicitly.
        assert _member_orders(actual) == _member_orders(expected), shape_id
        for path, want, got in _trait_values(expected, actual):
            assert json.dumps(got) == json.dumps(want), f"{shape_id} {path}"


def _trait_values(
    expected: dict[str, Any], actual: dict[str, Any]
) -> list[tuple[str, Any, Any]]:
    pairs = [
        (key, value, actual["traits"][key])
        for key, value in expected.get("traits", {}).items()
    ]
    for name, member in expected.get("members", {}).items():
        pairs.extend(
            (f"${name} {key}", value, actual["members"][name]["traits"][key])
            for key, value in member.get("traits", {}).items()
        )
    return pairs


def test_mini_trait_order_and_mixin_details() -> None:
    model = load_model((FIXTURES / "mini.json").read_text())
    thing = model.get_shape(ShapeId("example.mini", "Thing"))
    assert list(thing.members)[:3] == ["id", "tag", "created"]
    assert [str(k) for k in thing.members["id"].traits] == [
        "smithy.api#documentation",
        "smithy.api#required",
    ]
    # StampMixin's @internal is a local trait, so Thing does not inherit it.
    assert not thing.has_trait("smithy.api#internal")
    assert list(model.metadata) == ["alpha", "suppressions", "zeta"]
    mixins = [str(s.id) for s in model.iter_shapes() if s.is_mixin]
    assert mixins == ["example.mini#IdMixin", "example.mini#StampMixin"]


def test_weather_prelude_and_services() -> None:
    model = load_model((FIXTURES / "weather.json").read_bytes())
    assert [str(s.id) for s in model.services()] == ["example.weather#Weather"]
    assert not any(model.is_prelude(s) for s in model.iter_shapes())
