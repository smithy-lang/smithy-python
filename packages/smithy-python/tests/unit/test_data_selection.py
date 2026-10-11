# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import pytest
from smithy_python.exceptions import InvalidInvocationError, ModelError
from smithy_python.model import Model, load_model
from smithy_python.selection import select_shapes


def _model(shapes: dict[str, object]) -> Model:
    return load_model({"smithy": "2.0", "shapes": shapes})


@pytest.mark.parametrize("edge", ["operations", "resources", "errors"])
def test_service_edges(edge: str) -> None:
    target = {"operations": "Op", "resources": "Resource", "errors": "Data"}[edge]
    model = _model(
        {
            "a#Service": {"type": "service", edge: [{"target": f"a#{target}"}]},
            "a#Op": {"type": "operation", "output": {"target": "a#Data"}},
            "a#Resource": {
                "type": "resource",
                "properties": {"data": {"target": "a#Data"}},
            },
            "a#Data": {"type": "structure"},
        }
    )
    result = select_shapes(model, require_service=True)
    assert result.service is model.get_shape("a#Service")
    assert result.shapes == (model.get_shape("a#Data"),)
    assert result.excluded_count == 0


@pytest.mark.parametrize("edge", ["input", "output", "errors"])
def test_operation_edges(edge: str) -> None:
    reference = {"target": "a#Data"}
    model = _model(
        {
            "a#Service": {"type": "service", "operations": [{"target": "a#Op"}]},
            "a#Op": {
                "type": "operation",
                edge: [reference] if edge == "errors" else reference,
            },
            "a#Data": {"type": "structure"},
        }
    )
    assert select_shapes(model).shapes == (model.get_shape("a#Data"),)


@pytest.mark.parametrize(
    "edge",
    [
        "identifiers",
        "properties",
        "create",
        "put",
        "read",
        "update",
        "delete",
        "list",
        "operations",
        "collectionOperations",
        "resources",
    ],
)
def test_resource_edges(edge: str) -> None:
    value: object
    if edge in ("identifiers", "properties"):
        value = {"data": {"target": "a#Data"}}
    elif edge == "resources":
        value = [{"target": "a#Child"}]
    elif edge in ("operations", "collectionOperations"):
        value = [{"target": "a#Op"}]
    else:
        value = {"target": "a#Op"}
    model = _model(
        {
            "a#Service": {"type": "service", "resources": [{"target": "a#Resource"}]},
            "a#Resource": {"type": "resource", edge: value},
            "a#Child": {
                "type": "resource",
                "properties": {"data": {"target": "a#Data"}},
            },
            "a#Op": {"type": "operation", "output": {"target": "a#Data"}},
            "a#Data": {"type": "string"},
        }
    )
    result = select_shapes(model)
    assert result.shapes == (model.get_shape("a#Data"),)
    assert result.excluded_count == 0


def test_members_cycles_order_and_nonstructural_references() -> None:
    model = _model(
        {
            # Deliberately neither traversal nor lexicographic order.
            "a#Values": {"type": "list", "member": {"target": "a#Choice"}},
            "a#RenamedOnly": {"type": "string"},
            "a#Key": {"type": "string"},
            "a#TraitOnly": {"type": "string"},
            "a#Map": {
                "type": "map",
                "key": {"target": "a#Key"},
                "value": {"target": "a#Values"},
            },
            "a#Service": {
                "type": "service",
                "operations": [{"target": "a#Op"}],
                "resources": [{"target": "a#Resource"}],
                "rename": {"a#RenamedOnly": "Alias"},
                "traits": {"a#annotation": {"target": "a#TraitOnly"}},
            },
            "a#Resource": {"type": "resource", "resources": [{"target": "a#Resource"}]},
            "a#Choice": {"type": "union", "members": {"again": {"target": "a#Input"}}},
            "a#Input": {
                "type": "structure",
                "members": {
                    "map": {"target": "a#Map"},
                    "unit": {"target": "smithy.api#Unit"},
                    "trait": {"target": "a#Trait"},
                    "mixin": {"target": "a#Mixin"},
                },
            },
            "a#Trait": {"type": "structure", "traits": {"smithy.api#trait": {}}},
            "a#Mixin": {"type": "structure", "traits": {"smithy.api#mixin": {}}},
            "a#Op": {"type": "operation", "input": {"target": "a#Input"}},
        }
    )
    result = select_shapes(model)
    assert [str(shape.id) for shape in result.shapes] == [
        "a#Values",
        "a#Key",
        "a#Map",
        "a#Choice",
        "a#Input",
    ]
    assert result.excluded_count == 2


def test_flattened_relationships_and_members_are_selected() -> None:
    model = _model(
        {
            "a#ServiceBase": {
                "type": "service",
                "traits": {"smithy.api#mixin": {}},
                "operations": [{"target": "a#Op"}],
            },
            "a#Service": {"type": "service", "mixins": [{"target": "a#ServiceBase"}]},
            "a#Op": {"type": "operation", "input": {"target": "a#Input"}},
            "a#Base": {
                "type": "structure",
                "traits": {"smithy.api#mixin": {}},
                "members": {"data": {"target": "a#Data"}},
            },
            "a#Input": {"type": "structure", "mixins": [{"target": "a#Base"}]},
            "a#Data": {"type": "string"},
        }
    )
    result = select_shapes(model)
    assert result.service is model.get_shape("a#Service")
    assert [str(shape.id) for shape in result.shapes] == ["a#Input", "a#Data"]
    assert result.excluded_count == 0


@pytest.mark.parametrize("with_service", [False, True])
def test_all_data_kinds_and_exclusions(with_service: bool) -> None:
    simple = [
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
    shapes: dict[str, object] = {f"a#{kind}": {"type": kind} for kind in simple}
    shapes.update(
        {
            "a#Enum": {
                "type": "enum",
                "members": {
                    "A": {
                        "target": "smithy.api#Unit",
                        "traits": {"smithy.api#enumValue": "a"},
                    }
                },
            },
            "a#IntEnum": {
                "type": "intEnum",
                "members": {
                    "A": {
                        "target": "smithy.api#Unit",
                        "traits": {"smithy.api#enumValue": 1},
                    }
                },
            },
            "a#List": {"type": "list", "member": {"target": "smithy.api#String"}},
            "a#Map": {
                "type": "map",
                "key": {"target": "smithy.api#String"},
                "value": {"target": "smithy.api#String"},
            },
            "a#Union": {
                "type": "union",
                "members": {"s": {"target": "smithy.api#String"}},
            },
        }
    )
    expected = [*shapes, "a#Data"]
    shapes["a#Data"] = {
        "type": "structure",
        "members": {f"m{i}": {"target": shape_id} for i, shape_id in enumerate(shapes)},
    }
    shapes.update(
        {
            "a#Op": {"type": "operation", "input": {"target": "a#Data"}},
            "a#Resource": {"type": "resource"},
            "smithy.api#Unit": {"type": "structure"},
            "smithy.api#String": {"type": "string"},
            # Excluded names must not conflict with eligible names in types-only mode.
            "b#DATA": {"type": "structure", "traits": {"smithy.api#mixin": {}}},
            "c#data": {"type": "structure", "traits": {"smithy.api#trait": {}}},
            "d#Data": {"type": "resource"},
        }
    )
    if with_service:
        shapes["a#Service"] = {"type": "service", "operations": [{"target": "a#Op"}]}
    result = select_shapes(_model(shapes))
    assert [str(shape.id) for shape in result.shapes] == expected
    assert (result.service is not None) is with_service
    assert result.excluded_count == 0


def test_deep_graph_is_iterative() -> None:
    depth = 2000
    shapes: dict[str, object] = {
        f"a#Node{i}": {
            "type": "structure",
            "members": {"next": {"target": f"a#Node{(i + 1) % depth}"}},
        }
        for i in range(depth)
    }
    shapes.update(
        {
            "a#Service": {"type": "service", "operations": [{"target": "a#Op"}]},
            "a#Op": {"type": "operation", "input": {"target": "a#Node0"}},
        }
    )
    result = select_shapes(_model(shapes))
    assert [str(shape.id) for shape in result.shapes] == [
        f"a#Node{i}" for i in range(depth)
    ]
    assert result.excluded_count == 0


@pytest.mark.parametrize("explicit", [False, True])
def test_name_conflicts_not_checked_with_service(explicit: bool) -> None:
    model = _model(
        {
            "a#Service": {"type": "service", "operations": [{"target": "a#Op"}]},
            "a#Op": {
                "type": "operation",
                "input": {"target": "a#Data"},
                "output": {"target": "b#data"},
            },
            "a#Data": {"type": "structure"},
            "b#data": {"type": "structure"},
            "c#DATA": {"type": "string"},
        }
    )
    result = select_shapes(model, service_id="a#Service" if explicit else None)
    assert [str(shape.id) for shape in result.shapes] == ["a#Data", "b#data"]
    assert result.excluded_count == 1


def test_explicit_service_limits_the_closure() -> None:
    model = _model(
        {
            "a#First": {"type": "service", "errors": [{"target": "a#FirstError"}]},
            "a#Second": {"type": "service", "errors": [{"target": "a#SecondError"}]},
            "a#FirstError": {"type": "structure"},
            "a#SecondError": {"type": "structure"},
        }
    )
    result = select_shapes(model, service_id="a#Second")
    assert result.service is model.get_shape("a#Second")
    assert result.shapes == (model.get_shape("a#SecondError"),)
    assert result.excluded_count == 1


def test_direct_api_errors_and_empty_selection() -> None:
    model = _model({})
    result = select_shapes(model)
    assert result.service is None
    assert result.shapes == ()
    assert result.excluded_count == 0
    with pytest.raises(InvalidInvocationError):
        select_shapes(model, require_service=True)
    with pytest.raises(InvalidInvocationError):
        select_shapes(model, service_id="Missing")
    with pytest.raises(ModelError, match="a#Name, b#name"):
        select_shapes(
            _model({"a#Name": {"type": "string"}, "b#name": {"type": "string"}})
        )
