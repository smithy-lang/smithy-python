#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""The JMESPath subset that operationContextParams paths use."""

from dataclasses import dataclass
from types import ModuleType
from typing import Any

import pytest
from smithy_core._dynamic_models import ModelRegistry
from smithy_core._jmespath import compile
from smithy_core.shapes import ShapeType

INPUT: dict[str, Any] = {
    "RequestItems": {"t1": {"Keys": []}, "t2": {}},
    "TableCreationParameters": {"TableName": "created"},
    "TransactItems": [
        {"Get": {"TableName": "g1"}},
        {"Put": {"TableName": "p1"}},
        {"Get": {"TableName": "g2"}, "Update": {"TableName": "u2"}},
        {"Delete": {}},
    ],
}


@pytest.mark.parametrize(
    "expression, expected",
    [
        ("keys(RequestItems)", ["t1", "t2"]),
        ("TableCreationParameters.TableName", "created"),
        ("TableCreationParameters.*", ["created"]),
        ("TransactItems[*].Get.TableName", ["g1", "g2"]),
        (
            "TransactItems[*].[ConditionCheck.TableName, Put.TableName, "
            "Delete.TableName, Update.TableName][]",
            ["p1", "u2"],
        ),
        ("Missing[*].Get", None),
        ("Missing.TableName", None),
        ("keys(Missing)", None),
    ],
)
def test_paths(expression: str, expected: Any) -> None:
    assert compile(expression)(INPUT) == expected


# Generated shapes are dataclasses whose attribute names come from member_field_name.


@dataclass(kw_only=True)
class _Get:
    table_name: str | None = None


@dataclass(kw_only=True)
class _TransactItem:
    get: _Get | None = None
    put: _Get | None = None


@dataclass(kw_only=True)
class _Input:
    transact_items: list[_TransactItem] | None = None
    request_items: dict[str, Any] | None = None


def test_paths_over_shapes() -> None:
    value = _Input(
        transact_items=[
            _TransactItem(get=_Get(table_name="g1")),
            _TransactItem(put=_Get(table_name="p1")),
        ],
        request_items={"a": 1, "b": 2},
    )
    assert compile("TransactItems[*].[Get.TableName, Put.TableName][]")(value) == [
        "g1",
        "p1",
    ]
    assert compile("keys(RequestItems)")(value) == ["a", "b"]
    assert compile("Unknown")(value) is None


def _dynamic_models() -> ModelRegistry:
    ns = "ns.example"
    get = (ShapeType.STRUCTURE.value, ns, "Get", 0, ("TableName",), ((3, 0),))
    item = (ShapeType.STRUCTURE.value, ns, "TransactItem", 0, ("Get",), ((get, 0),))
    items = (ShapeType.LIST.value, ns, "TransactItems", 0, ("member",), ((item, 0),))
    tables = (ShapeType.MAP.value, ns, "Tables", 0, ("key", "value"), ((3, 0), (3, 0)))
    request = (
        ShapeType.STRUCTURE.value,
        ns,
        "Request",
        0,
        ("TransactItems", "RequestItems"),
        ((items, 0), (tables, 0)),
    )
    module = ModuleType("ns.example._private.schemas")
    for name, schema in [("GET", get), ("ITEM", item), ("REQUEST", request)]:
        setattr(module, name, schema)
    return ModelRegistry(
        module,
        index={"Get": "GET", "TransactItem": "ITEM", "Request": "REQUEST"},
        shape_names={"Get", "TransactItem", "Request"},
    )


def test_paths_over_dynamic_models() -> None:
    registry = _dynamic_models()
    get, item, request = (registry.build(n) for n in ("Get", "TransactItem", "Request"))
    value = request(
        transact_items=[item(get=get(table_name="a")), item(), item(get=get())],
        request_items={"x": "1"},
    )
    assert compile("TransactItems[*].Get.TableName")(value) == ["a"]
    assert compile("keys(RequestItems)")(value) == ["x"]
