# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Public recursive aliases stay named runtime aliases for customer annotations."""

import pickle
from collections.abc import Callable
from typing import Any, get_args, get_type_hints

import pytest
import smithy_python.model
from smithy_python.model import JsonValue as CustomerJsonValue
from smithy_python.model import Node as CustomerNode


def _renamed_node(value: CustomerNode) -> None: ...
def _qualified_node(value: smithy_python.model.Node) -> None: ...
def _renamed_json_value(value: CustomerJsonValue) -> None: ...
def _qualified_json_value(value: smithy_python.model.JsonValue) -> None: ...


_ALIASES = [
    pytest.param(
        smithy_python.model.Node,
        "Node",
        [_renamed_node, _qualified_node],
        id="Node",
    ),
    pytest.param(
        smithy_python.model.JsonValue,
        "JsonValue",
        [_renamed_json_value, _qualified_json_value],
        id="JsonValue",
    ),
]


@pytest.mark.parametrize("alias, name, annotated", _ALIASES)
def test_alias_is_named_at_runtime(
    alias: Any, name: str, annotated: list[Callable[..., None]]
) -> None:
    assert alias.__name__ == name
    assert alias.__module__ == "smithy_python.model._shapes"
    assert alias.__type_params__ == ()
    assert {str, int, float, bool, type(None)} <= set(get_args(alias.__value__))
    assert pickle.loads(pickle.dumps(alias)) is alias


@pytest.mark.parametrize("alias, name, annotated", _ALIASES)
def test_renamed_and_qualified_annotations_resolve(
    alias: Any, name: str, annotated: list[Callable[..., None]]
) -> None:
    for function in annotated:
        assert get_type_hints(function)["value"] is alias


@pytest.mark.parametrize("alias, name, annotated", _ALIASES)
def test_customer_global_with_alias_name_is_ignored(
    alias: Any, name: str, annotated: list[Callable[..., None]]
) -> None:
    # A customer module that also defines a global with the alias's own name.
    namespace = {**globals(), name: int}
    for function in annotated:
        assert get_type_hints(function, globalns=namespace)["value"] is alias
