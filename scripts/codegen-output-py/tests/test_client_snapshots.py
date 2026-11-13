# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import ast
import asyncio
import importlib
import json
import sys
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from smithy_cbor import loads
from smithy_core.aio.types import AsyncBytesReader
from smithy_core.retries import SimpleRetryStrategy
from smithy_http import HTTPResponse, tuples_to_fields
from smithy_http.interfaces import HTTPRequest, HTTPRequestConfiguration
from smithy_python.model import OperationShape, load_model

_ROOT = Path(__file__).resolve().parents[3]
_INPUTS = _ROOT / "scripts/codegen-output-py"
_PROJECTIONS: dict[str, Any] = json.loads(
    (_INPUTS / "client-projections.json").read_text()
)
_CBOR = _PROJECTIONS["rpcv2-cbor-client"]
_SOURCE = _ROOT / "codegen-output-py/rpcv2-cbor-client/src"
_PACKAGE = _CBOR["package"]
_JAVA_CLIENT = _ROOT / "codegen-output/rpcv2-cbor/src/rpcv2cbor/client.py"


@pytest.fixture(scope="module")
def package() -> Iterator[ModuleType]:
    sys.path.insert(0, str(_SOURCE))
    try:
        yield importlib.import_module(_PACKAGE)
    finally:
        sys.path.remove(str(_SOURCE))
        for name in tuple(sys.modules):
            if name == _PACKAGE or name.startswith(_PACKAGE + "."):
                del sys.modules[name]


def _methods(path: Path, class_name: str) -> set[str]:
    tree = ast.parse(path.read_text())
    (cls,) = (
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == class_name
    )
    return {
        node.name
        for node in cls.body
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        and not node.name.startswith("_")
    }


def test_clients_have_a_method_per_operation_like_java() -> None:
    model = load_model(json.loads((_INPUTS / _CBOR["model"]).read_text()))
    operations = sum(1 for _ in model.iter_shapes(OperationShape))
    native = _SOURCE / _PACKAGE
    sync = _methods(native / "client.py", "RpcV2Protocol")
    assert len(sync) == operations == 14
    assert sync == _methods(native / "aio/client.py", "AsyncRpcV2Protocol")
    assert sync == _methods(_JAVA_CLIENT, "RpcV2Protocol")


class _Transport:
    TIMEOUT_EXCEPTIONS = ()

    def __init__(self, body: bytes) -> None:
        self.body = body
        self.requests: list[HTTPRequest] = []

    def __deepcopy__(self, memo: dict[int, Any]) -> _Transport:
        # Clients copy their config, transport included. Keep one recorder.
        return self

    def _respond(self, request: HTTPRequest, body: Any) -> HTTPResponse:
        self.requests.append(request)
        headers = [
            ("Content-Type", "application/cbor"),
            ("smithy-protocol", "rpc-v2-cbor"),
        ]
        return HTTPResponse(status=200, fields=tuples_to_fields(headers), body=body)

    def send(
        self,
        request: HTTPRequest,
        *,
        request_config: HTTPRequestConfiguration | None = None,
    ) -> HTTPResponse:
        return self._respond(request, self.body)


class _AsyncTransport(_Transport):
    async def send(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        request: HTTPRequest,
        *,
        request_config: HTTPRequestConfiguration | None = None,
    ) -> HTTPResponse:
        return self._respond(request, AsyncBytesReader(self.body))


@pytest.mark.parametrize("aio", [False, True])
def test_snapshot_client_round_trips_through_the_runtime(
    package: ModuleType, aio: bool
) -> None:
    # CBOR {"stringValue": "out"}.
    transport = (_AsyncTransport if aio else _Transport)(b"\xa1\x6bstringValue\x63out")
    config = (package.AsyncConfig if aio else package.Config)(
        endpoint_uri="https://example.com",
        transport=transport,
        retry_strategy=SimpleRetryStrategy(max_attempts=1),
    )
    client = (package.AsyncRpcV2Protocol if aio else package.RpcV2Protocol)(config)
    call = client.simple_scalar_properties(string_value="in", integer_value=3)
    output = asyncio.run(call) if aio else call

    assert output.string_value == "out"
    (request,) = transport.requests
    assert request.destination.path == (
        "/service/RpcV2Protocol/operation/SimpleScalarProperties"
    )
    body: Any = request.body
    if not isinstance(body, bytes):
        body = body.read()
        if asyncio.iscoroutine(body):
            body = asyncio.run(body)
    assert loads(body) == {"stringValue": "in", "integerValue": 3}
