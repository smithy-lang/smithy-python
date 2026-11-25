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


# Waiters also compare, filter, and count.
WAITER_OUTPUT: dict[str, Any] = {
    "Status": "ACTIVE",
    "Count": 2,
    "Zero": 0,
    "Flag": False,
    "Empty": [],
    "Groups": [
        {"Min": 2, "Instances": [{"State": "InService"}, {"State": "InService"}]},
        {"Min": 2, "Instances": [{"State": "InService"}, {"State": "Pending"}]},
    ],
    "Destinations": [
        {"Status": "DISABLED"},
        {"Status": "ENABLE_FAILED"},
    ],
    "Services": [
        {"Deployments": [1], "Running": 3, "Desired": 3},
        {"Deployments": [1, 2], "Running": 3, "Desired": 3},
    ],
}


@pytest.mark.parametrize(
    "expression, expected",
    [
        ("Status == 'ACTIVE'", True),
        ("Status != 'ACTIVE'", False),
        ('Status == `"ACTIVE"`', True),
        ("Count > `1`", True),
        ("Count >= `3`", False),
        ("Count < `3` && Count <= `2`", True),
        # Ordering is only defined for numbers.
        ("Status > `1`", None),
        # Booleans are never numbers.
        ("Flag == `0`", False),
        ("Zero == `false`", False),
        ("length(Groups) == `2`", True),
        ("length(Status)", 6),
        ("length(Missing)", None),
        ("length(Empty) == `0`", True),
        ("Groups[0].Min", 2),
        ("Groups[-1].Instances[1].State", "Pending"),
        ("Groups[5]", None),
        ("Groups[].Instances[?State == 'Pending'][].State", ["Pending"]),
        (
            "contains(Groups[].[length(Instances[?State=='InService']) >= Min][], "
            "`false`)",
            True,
        ),
        (
            "length(Destinations) > `0` && length(Destinations[?Status == "
            "'DISABLED' || Status == 'ENABLE_FAILED']) == length(Destinations)",
            True,
        ),
        (
            "length(Services[?!(length(Deployments) == `1` && Running == Desired)])"
            " == `0`",
            False,
        ),
        ("contains(Status, 'TIV')", True),
        ("contains(Count, 'x')", None),
        # Zero and non-empty values are true. Null, false, and empty values aren't.
        ("Zero || 'other'", 0),
        ("Empty || Flag || 'last'", "last"),
        ("Empty && 'never'", []),
        ("!Empty", True),
        ("Groups[*].Min | [0]", 2),
        ("Groups[?@.Min == `2`] | length(@)", 2),
    ],
)
def test_waiter_paths(expression: str, expected: Any) -> None:
    assert compile(expression)(WAITER_OUTPUT) == expected


def test_raw_strings_unescape_quotes() -> None:
    assert compile("'it\\'s'")({}) == "it's"


@pytest.mark.parametrize(
    "expression",
    [
        "length(a, b)",
        "contains(a)",
        "sort_by(a, &b)",
        "a[?b",
        "a[1:2]",
        "{a: b}",
        "`not json`",
        "a ==",
        "a[*]b",
        "'a''b'",
    ],
)
def test_unsupported_waiter_paths(expression: str) -> None:
    with pytest.raises(ValueError, match="Unsupported JMESPath expression"):
        compile(expression)


def test_waiter_paths_over_shapes() -> None:
    value = _Input(
        transact_items=[_TransactItem(get=_Get(table_name="g1")), _TransactItem()],
    )
    assert compile("length(TransactItems[?Get.TableName == 'g1'])")(value) == 1
    # A member path into a scalar is null, not one of the scalar's attributes.
    assert compile("TransactItems[0].Get.TableName.upper")(value) is None
