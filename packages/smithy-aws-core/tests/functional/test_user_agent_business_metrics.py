#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""End-to-end User Agent 2.1 business metrics through a generated AWS client.

Drives the generated awsJson1.0 client (``codegen-output/aws-json-1-0``) and checks
the ``m/`` section of the User-Agent the SDK sends for the features each call uses.
"""

import os
import sys
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("awsjson10")

from awsjson10.aio.client import AsyncJSONRPC10Client
from awsjson10.aio.config import AsyncJSONRPC10Config
from awsjson10.client import JSONRPC10Client
from awsjson10.config import JSONRPC10Config
from awsjson10.models import EmptyInputAndEmptyOutputInput
from smithy_aws_core.aio.identity.process import AsyncProcessCredentialsResolver
from smithy_aws_core.identity.process import ProcessCredentialsResolver
from smithy_http import HTTPResponse, tuples_to_fields
from smithy_test import HTTPMockController, mock
from smithy_test.aio import mock_async

_JSON_CONTENT_TYPE = ("content-type", "application/x-amz-json-1.0")


# The mock replaces the credentials resolver, so tests of credential sources
# record requests with this transport instead.
class _RecordingTransport:
    """Returns empty responses and records the User-Agent of every request."""

    TIMEOUT_EXCEPTIONS = ()

    def __init__(self) -> None:
        self.user_agents: list[str] = []

    def send(self, request: Any, *, request_config: Any = None) -> HTTPResponse:
        self.user_agents.append(request.fields["User-Agent"].as_string())
        return HTTPResponse(
            status=200,
            fields=tuples_to_fields([_JSON_CONTENT_TYPE]),
            body=b"{}",
        )


class _AsyncRecordingTransport(_RecordingTransport):
    async def send(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, request: Any, *, request_config: Any = None
    ) -> HTTPResponse:
        return super().send(request, request_config=request_config)


@pytest.fixture(params=[True, False], ids=["sync", "async"])
def sync(request: pytest.FixtureRequest) -> bool:
    return request.param


def _transport(sync: bool) -> _RecordingTransport:
    return (_RecordingTransport if sync else _AsyncRecordingTransport)()


def _process_resolver(sync: bool, script: Path) -> Any:
    command = [sys.executable, str(script)]
    if sync:
        return ProcessCredentialsResolver(command)
    return AsyncProcessCredentialsResolver(command)


async def _invoke(sync: bool, calls: int, **config: Any) -> None:
    if sync:
        client = JSONRPC10Client(config=JSONRPC10Config.resolve(**config))
        for _ in range(calls):
            client.empty_input_and_empty_output(EmptyInputAndEmptyOutputInput())
        return
    async_client = AsyncJSONRPC10Client(
        config=await AsyncJSONRPC10Config.resolve(**config)
    )
    for _ in range(calls):
        await async_client.empty_input_and_empty_output(EmptyInputAndEmptyOutputInput())


def _business_metrics(user_agent: str) -> list[str]:
    return [part for part in user_agent.split() if part.startswith("m/")]


@pytest.fixture(autouse=True)
def _clean_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    # Keep the host's AWS settings from changing what each call reports.
    for name in list(os.environ):
        if name.startswith("AWS_"):
            monkeypatch.delenv(name)


def _write_credentials_script(tmp_path: Path) -> Path:
    """Write a credential process script that prints fixed credentials."""
    script = tmp_path / "credentials.py"
    script.write_text(
        "import json\n"
        "print(json.dumps("
        "{'Version': 1, 'AccessKeyId': 'AKID', 'SecretAccessKey': 'secret'}))\n"
    )
    return script


async def _call(
    sync: bool, tmp_path: Path, transport: _RecordingTransport, **config: Any
) -> list[str]:
    # In-code keys, unless the test supplies its own credentials resolver.
    if "aws_credentials_identity_resolver" not in config:
        config = {
            "aws_access_key_id": "AKID",
            "aws_secret_access_key": "secret",
            **config,
        }
    missing = str(tmp_path / "missing")
    await _invoke(
        sync,
        1,
        config_file_path=missing,
        credentials_file_path=missing,
        region="us-west-2",
        transport=transport,
        **config,
    )
    return transport.user_agents


async def _call_mocked(
    sync: bool,
    tmp_path: Path,
    metrics: str,
    *,
    throttle_first: bool = False,
    **config: Any,
) -> None:
    missing = str(tmp_path / "missing")
    config = {
        "config_file_path": missing,
        "credentials_file_path": missing,
        "region": "us-west-2",
        "aws_access_key_id": "AKID",
        "aws_secret_access_key": "secret",
        **config,
    }
    if sync:
        client = JSONRPC10Client(config=JSONRPC10Config.resolve(**config))
        with _expect_metrics(mock(client), metrics, throttle_first):
            client.empty_input_and_empty_output(EmptyInputAndEmptyOutputInput())
        return
    async_client = AsyncJSONRPC10Client(
        config=await AsyncJSONRPC10Config.resolve(**config)
    )
    with _expect_metrics(await mock_async(async_client), metrics, throttle_first):
        await async_client.empty_input_and_empty_output(EmptyInputAndEmptyOutputInput())


def _expect_metrics(
    controller: HTTPMockController, metrics: str, throttle_first: bool
) -> HTTPMockController:
    expectation = controller.expect_request(
        headers={"User-Agent": lambda ua: _business_metrics(ua) == [metrics]}
    )
    if throttle_first:
        expectation.times(2).respond_with(
            status_code=429,
            headers=dict([_JSON_CONTENT_TYPE]),
            body='{"__type":"ThrottlingException"}',
        )
    expectation.respond_with(headers=dict([_JSON_CONTENT_TYPE]), body="{}")
    return controller


async def test_reports_standard_retry_mode_by_default(
    sync: bool, tmp_path: Path
) -> None:
    await _call_mocked(sync, tmp_path, "m/E,e")


async def test_reports_adaptive_retry_mode(sync: bool, tmp_path: Path) -> None:
    await _call_mocked(sync, tmp_path, "m/F,e", retry_mode="adaptive")


async def test_reports_adaptive_retry_mode_from_environment(
    sync: bool, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AWS_RETRY_MODE", "adaptive")
    await _call_mocked(sync, tmp_path, "m/F,e")


async def test_reports_endpoint_override(sync: bool, tmp_path: Path) -> None:
    await _call_mocked(sync, tmp_path, "m/E,N,e", endpoint_uri="https://localhost:8443")


async def test_reports_endpoint_override_from_environment(
    sync: bool, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AWS_ENDPOINT_URL_JSON_RPC_10", "https://localhost:8443")
    await _call_mocked(sync, tmp_path, "m/E,N,e")


async def test_retried_call_sends_same_business_metrics_once(
    sync: bool, tmp_path: Path
) -> None:
    await _call_mocked(
        sync,
        tmp_path,
        "m/E,N,e",
        throttle_first=True,
        endpoint_uri="https://localhost:8443",
    )


async def test_reports_process_resolver_used_directly(
    sync: bool, tmp_path: Path
) -> None:
    script = _write_credentials_script(tmp_path)
    user_agents = await _call(
        sync,
        tmp_path,
        _transport(sync),
        aws_credentials_identity_resolver=_process_resolver(sync, script),
    )
    assert _business_metrics(user_agents[0]) == ["m/E,w"]


async def _call_with_credential_chain(
    sync: bool, tmp_path: Path, transport: _RecordingTransport, config_file: str = ""
) -> list[str]:
    # No credentials in code, so the client resolves them with its credential chain.
    config_path = tmp_path / "config"
    config_path.write_text(config_file)
    # The second call is served from cached credentials.
    await _invoke(
        sync,
        2,
        config_file_path=str(config_path),
        credentials_file_path=str(tmp_path / "missing"),
        region="us-west-2",
        transport=transport,
    )
    return transport.user_agents


async def test_reports_environment_credentials(
    sync: bool, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AKID")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")
    user_agents = await _call_with_credential_chain(sync, tmp_path, _transport(sync))
    assert [_business_metrics(ua) for ua in user_agents] == [["m/E,g"], ["m/E,g"]]


async def test_reports_resolved_account_id(
    sync: bool, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AKID")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")
    monkeypatch.setenv("AWS_ACCOUNT_ID", "123456789012")
    user_agents = await _call_with_credential_chain(sync, tmp_path, _transport(sync))
    assert _business_metrics(user_agents[0]) == ["m/E,g,T"]


@pytest.mark.parametrize(
    "config_file",
    [
        "[default]\naws_access_key_id = AKID\naws_secret_access_key = secret\n",
        "[default]\n"
        "aws_access_key_id = AKID\n"
        "aws_secret_access_key = secret\n"
        "aws_session_token = token\n",
    ],
    ids=["static_keys", "session_keys"],
)
async def test_reports_profile_credentials(
    sync: bool, tmp_path: Path, config_file: str
) -> None:
    user_agents = await _call_with_credential_chain(
        sync, tmp_path, _transport(sync), config_file
    )
    assert [_business_metrics(ua) for ua in user_agents] == [["m/E,n"], ["m/E,n"]]


async def test_reports_profile_credential_process(sync: bool, tmp_path: Path) -> None:
    script = _write_credentials_script(tmp_path)
    # Quoted so that paths with spaces stay one argument each.
    config_file = f'[default]\ncredential_process = "{sys.executable}" "{script}"\n'
    user_agents = await _call_with_credential_chain(
        sync, tmp_path, _transport(sync), config_file
    )
    assert _business_metrics(user_agents[0]) == ["m/E,v,w"]
