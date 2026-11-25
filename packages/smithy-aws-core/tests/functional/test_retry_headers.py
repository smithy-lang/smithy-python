#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""The retry information headers through a generated AWS client.

Drives the generated awsJson1.0 client (``codegen-output/aws-json-1-0``) and checks
the headers of every attempt the sync and async clients send.
"""

from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("awsjson10")

from awsjson10.aio.client import AsyncJSONRPC10Client
from awsjson10.aio.config import AsyncJSONRPC10Config
from awsjson10.client import JSONRPC10Client
from awsjson10.config import JSONRPC10Config
from smithy_http import HTTPResponse, tuples_to_fields

_JSON_CONTENT_TYPE = ("content-type", "application/x-amz-json-1.0")


class _RecordingTransport:
    """Throttles the first ``throttles`` requests and records every request's headers."""

    TIMEOUT_EXCEPTIONS = ()

    def __init__(self, throttles: int = 0) -> None:
        self.headers: list[dict[str, str]] = []
        self._throttles = throttles

    def send(self, request: Any, *, request_config: Any = None) -> HTTPResponse:
        # Attempts can share one Fields object, so copy the values as they are sent.
        self.headers.append({f.name.lower(): f.as_string() for f in request.fields})
        if len(self.headers) <= self._throttles:
            return HTTPResponse(
                status=429,
                fields=tuples_to_fields([_JSON_CONTENT_TYPE]),
                body=b'{"__type":"ThrottlingException"}',
            )
        return HTTPResponse(
            status=200, fields=tuples_to_fields([_JSON_CONTENT_TYPE]), body=b"{}"
        )


class _AsyncRecordingTransport:
    """The async form: it sends through a ``_RecordingTransport`` that it holds."""

    TIMEOUT_EXCEPTIONS = ()

    def __init__(self, throttles: int = 0) -> None:
        self._transport = _RecordingTransport(throttles)
        self.headers = self._transport.headers

    async def send(self, request: Any, *, request_config: Any = None) -> HTTPResponse:
        return self._transport.send(request, request_config=request_config)


@pytest.fixture(params=[True, False], ids=["sync", "async"])
def sync(request: pytest.FixtureRequest) -> bool:
    return request.param


async def _call(sync: bool, tmp_path: Path, throttles: int = 0) -> list[dict[str, str]]:
    transport = (_RecordingTransport if sync else _AsyncRecordingTransport)(throttles)
    missing = str(tmp_path / "missing")
    config: dict[str, Any] = {
        "config_file_path": missing,
        "credentials_file_path": missing,
        "region": "us-west-2",
        "aws_access_key_id": "AKID",
        "aws_secret_access_key": "secret",
        "transport": transport,
    }
    if sync:
        JSONRPC10Client(
            config=JSONRPC10Config.resolve(**config)
        ).empty_input_and_empty_output()
    else:
        await AsyncJSONRPC10Client(
            config=await AsyncJSONRPC10Config.resolve(**config)
        ).empty_input_and_empty_output()
    return transport.headers


async def test_sends_same_invocation_id_on_every_attempt(
    sync: bool, tmp_path: Path
) -> None:
    attempts = await _call(sync, tmp_path, throttles=2)
    invocation_ids = {headers["amz-sdk-invocation-id"] for headers in attempts}
    assert len(attempts) == 3
    assert len(invocation_ids) == 1


async def test_sends_attempt_number_and_max_attempts(
    sync: bool, tmp_path: Path
) -> None:
    attempts = await _call(sync, tmp_path, throttles=2)
    assert [headers["amz-sdk-request"] for headers in attempts] == [
        "attempt=1; max=3",
        "attempt=2; max=3",
        "attempt=3; max=3",
    ]


async def test_signs_retry_headers(sync: bool, tmp_path: Path) -> None:
    (headers,) = await _call(sync, tmp_path)
    signed = headers["authorization"]
    assert "amz-sdk-invocation-id" in signed
    assert "amz-sdk-request" in signed
