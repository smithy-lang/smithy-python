# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from types import SimpleNamespace

import pytest
from smithy_core import URI
from smithy_core.endpoints import resolve_static_uri
from smithy_core.exceptions import EndpointResolutionError
from smithy_core.types import TypedProperties


def _resolve(endpoint_uri: str | URI | None) -> object:
    config = SimpleNamespace(endpoint_uri=endpoint_uri)
    return resolve_static_uri(TypedProperties({"config": config}))


def test_rejects_invalid_uris() -> None:
    with pytest.raises(EndpointResolutionError, match="Invalid endpoint URI"):
        _resolve("example.com")
