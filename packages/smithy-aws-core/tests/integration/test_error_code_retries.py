#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""Retries of known service errors through the generated ec2Query client.

EC2 models none of its errors, so its throttling errors are only known by code.
"""

import inspect
import os
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("ec2query")

from ec2query.aio.client import AsyncEC2ProtocolClient
from ec2query.aio.config import AsyncEC2ProtocolConfig
from ec2query.client import EC2ProtocolClient
from ec2query.config import EC2ProtocolConfig
from smithy_core.exceptions import CallError
from smithy_core.retries import (
    ExponentialRetryBackoffStrategy,
    StandardRetryQuota,
    StandardRetryStrategy,
)
from smithy_http import HTTPResponse, tuples_to_fields


class _Transport:
    """Answers each request with the next canned response, then with a success."""

    TIMEOUT_EXCEPTIONS = ()

    def __init__(self, responses: list[tuple[int, str | None]]) -> None:
        self.attempts = 0
        self._responses = responses

    def send(self, request: Any, *, request_config: Any = None) -> HTTPResponse:
        self.attempts += 1
        if not self._responses:
            return HTTPResponse(status=200, fields=tuples_to_fields([]), body=b"")
        status, code = self._responses.pop(0)
        body = (
            f"<Response><Errors><Error><Code>{code}</Code></Error></Errors>"
            "<RequestID>request-id</RequestID></Response>"
            if code is not None
            else ""
        )
        return HTTPResponse(
            status=status,
            fields=tuples_to_fields([("content-type", "text/xml")]),
            body=body.encode(),
        )


class _AsyncTransport(_Transport):
    async def send(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, request: Any, *, request_config: Any = None
    ) -> HTTPResponse:
        return super().send(request, request_config=request_config)


@pytest.fixture(params=[True, False], ids=["sync", "async"])
def sync(request: pytest.FixtureRequest) -> bool:
    return request.param


@pytest.fixture(autouse=True)
def _clean_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    # Keep the host's AWS settings out of the client's config.
    for name in list(os.environ):
        if name.startswith("AWS_"):
            monkeypatch.delenv(name)


async def _call(
    sync: bool,
    tmp_path: Path,
    responses: list[tuple[int, str | None]],
    *,
    max_attempts: int = 3,
) -> tuple[_Transport, StandardRetryQuota, Exception | None]:
    """Make a call, returning its transport, retry quota and error, if it failed."""
    quota = StandardRetryQuota()
    no_backoff = ExponentialRetryBackoffStrategy(backoff_scale_value=0)
    missing = str(tmp_path / "missing")
    config: dict[str, Any] = {
        "config_file_path": missing,
        "credentials_file_path": missing,
        "region": "us-west-2",
        "endpoint_uri": "https://example.com",
        "aws_access_key_id": "AKID",
        "aws_secret_access_key": "secret",
        "retry_strategy": StandardRetryStrategy(
            backoff_strategy=no_backoff,
            throttling_backoff_strategy=no_backoff,
            max_attempts=max_attempts,
            retry_quota=quota,
        ),
    }
    if sync:
        transport = _Transport(responses)
        client: Any = EC2ProtocolClient(
            config=EC2ProtocolConfig.resolve(transport=transport, **config)
        )
    else:
        transport = _AsyncTransport(responses)
        client = AsyncEC2ProtocolClient(
            config=await AsyncEC2ProtocolConfig.resolve(transport=transport, **config)
        )

    try:
        result = client.empty_input_and_empty_output()
        if inspect.isawaitable(result):
            await result
    except Exception as e:
        return transport, quota, e
    return transport, quota, None


@pytest.mark.parametrize(
    ("status", "code"), [(503, "RequestLimitExceeded"), (502, "EC2ThrottledException")]
)
async def test_throttling_error_is_retried_as_a_throttling_error(
    sync: bool, tmp_path: Path, status: int, code: str
) -> None:
    transport, quota, error = await _call(
        sync, tmp_path, [(status, code)] * 2, max_attempts=2
    )

    assert isinstance(error, CallError)
    assert error.is_throttling_error is True
    assert transport.attempts == 2
    # The retry was charged as a throttling error.
    assert quota.available_capacity == 500 - StandardRetryQuota.THROTTLING_RETRY_COST


@pytest.mark.parametrize(
    ("status", "code"), [(500, "InternalError"), (503, "Unavailable"), (504, None)]
)
async def test_transient_error_is_retried(
    sync: bool, tmp_path: Path, status: int, code: str | None
) -> None:
    transport, quota, error = await _call(
        sync, tmp_path, [(status, code)] * 2, max_attempts=2
    )

    assert isinstance(error, CallError)
    assert error.is_throttling_error is False
    assert transport.attempts == 2
    assert quota.available_capacity == 500 - StandardRetryQuota.RETRY_COST


async def test_retried_error_can_succeed(sync: bool, tmp_path: Path) -> None:
    transport, _, error = await _call(sync, tmp_path, [(400, "RequestLimitExceeded")])

    assert error is None
    assert transport.attempts == 2


@pytest.mark.parametrize(
    ("status", "code"), [(400, "InvalidInstanceID.NotFound"), (501, None)]
)
async def test_other_errors_are_not_retried(
    sync: bool, tmp_path: Path, status: int, code: str | None
) -> None:
    transport, _, error = await _call(sync, tmp_path, [(status, code)])

    assert isinstance(error, CallError)
    assert transport.attempts == 1


@pytest.mark.parametrize(
    ("responses", "expected"),
    [
        ([(400, "InvalidInstanceID.NotFound")], "InvalidInstanceID.NotFound"),
        ([(503, "RequestLimitExceeded"), (504, None)], None),
    ],
    ids=["single-attempt", "retried"],
)
async def test_last_attempts_error_code_is_reported(
    sync: bool,
    tmp_path: Path,
    responses: list[tuple[int, str | None]],
    expected: str | None,
) -> None:
    # Copied because the transport pops from it and both runs share it.
    _, _, error = await _call(sync, tmp_path, list(responses), max_attempts=2)

    assert isinstance(error, CallError)
    assert error.response_metadata.error_code == expected
