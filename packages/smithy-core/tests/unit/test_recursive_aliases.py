# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Public recursive aliases stay named runtime aliases for customer annotations."""

import pickle
from collections.abc import Callable
from typing import Any, get_args, get_type_hints

import pytest
import smithy_core.documents
import smithy_core.types
from smithy_core.documents import DocumentValue as CustomerDocumentValue
from smithy_core.types import Document as CustomerDocument


def _renamed_document_value(value: CustomerDocumentValue) -> None: ...
def _qualified_document_value(value: smithy_core.documents.DocumentValue) -> None: ...
def _renamed_document(value: CustomerDocument) -> None: ...
def _qualified_document(value: smithy_core.types.Document) -> None: ...


_ALIASES = [
    pytest.param(
        smithy_core.documents.DocumentValue,
        "smithy_core.documents",
        "DocumentValue",
        [_renamed_document_value, _qualified_document_value],
        id="DocumentValue",
    ),
    pytest.param(
        smithy_core.types.Document,
        "smithy_core.types",
        "Document",
        [_renamed_document, _qualified_document],
        id="Document",
    ),
]


@pytest.mark.parametrize("alias, module, name, annotated", _ALIASES)
def test_alias_is_named_at_runtime(
    alias: Any, module: str, name: str, annotated: list[Callable[..., None]]
) -> None:
    assert alias.__name__ == name
    assert alias.__module__ == module
    assert alias.__type_params__ == ()
    assert {str, int, float, bool, type(None)} <= set(get_args(alias.__value__))
    assert pickle.loads(pickle.dumps(alias)) is alias


@pytest.mark.parametrize("alias, module, name, annotated", _ALIASES)
def test_renamed_and_qualified_annotations_resolve(
    alias: Any, module: str, name: str, annotated: list[Callable[..., None]]
) -> None:
    for function in annotated:
        assert get_type_hints(function)["value"] is alias


@pytest.mark.parametrize("alias, module, name, annotated", _ALIASES)
def test_customer_global_with_alias_name_is_ignored(
    alias: Any, module: str, name: str, annotated: list[Callable[..., None]]
) -> None:
    # A customer module that also defines a global with the alias's own name.
    namespace = {**globals(), name: int}
    for function in annotated:
        assert get_type_hints(function, globalns=namespace)["value"] is alias
