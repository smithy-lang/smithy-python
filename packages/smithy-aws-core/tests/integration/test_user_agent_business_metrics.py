#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""End-to-end User Agent 2.1 business metrics through a generated AWS client.

Drives the generated awsJson1.0 client (``codegen-output/aws-json-1-0``) with a stub
transport that records each request's User-Agent header, and checks the ``m/``
section the SDK sends for the features each call uses.
"""

import os
import sys
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("awsjson10")

from awsjson10.client import AsyncJSONRPC10Client
from awsjson10.config import AsyncJSONRPC10Config
from awsjson10.models import EmptyInputAndEmptyOutputInput
from smithy_aws_core.aio.identity.process import AsyncProcessCredentialsResolver
from smithy_http import tuples_to_fields
from smithy_http.aio import HTTPResponse

_JSON_CONTENT_TYPE = ("content-type", "application/x-amz-json-1.0")


class _RecordingTransport:
    """Returns canned responses and records the User-Agent of every request."""

    TIMEOUT_EXCEPTIONS = ()

    def __init__(self, *, throttle_first: bool = False) -> None:
        self.user_agents: list[str] = []
        self._throttle_first = throttle_first

    async def send(self, request: Any, *, request_config: Any = None) -> HTTPResponse:
        self.user_agents.append(request.fields["User-Agent"].as_string())
        if self._throttle_first and len(self.user_agents) == 1:
            return HTTPResponse(
                status=429,
                fields=tuples_to_fields([_JSON_CONTENT_TYPE]),
                body=b'{"__type":"ThrottlingException"}',
            )
        return HTTPResponse(
            status=200,
            fields=tuples_to_fields([_JSON_CONTENT_TYPE]),
            body=b"{}",
        )


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
    tmp_path: Path, transport: _RecordingTransport, **config: Any
) -> list[str]:
    # In-code keys, unless the test supplies its own credentials resolver.
    if "aws_credentials_identity_resolver" not in config:
        config = {
            "aws_access_key_id": "AKID",
            "aws_secret_access_key": "secret",
            **config,
        }
    missing = str(tmp_path / "missing")
    resolved = await AsyncJSONRPC10Config.resolve(
        config_file_path=missing,
        credentials_file_path=missing,
        region="us-west-2",
        transport=transport,
        **config,
    )
    client = AsyncJSONRPC10Client(config=resolved)
    await client.empty_input_and_empty_output(EmptyInputAndEmptyOutputInput())
    return transport.user_agents


async def test_reports_standard_retry_mode_by_default(tmp_path: Path) -> None:
    user_agents = await _call(tmp_path, _RecordingTransport())
    assert _business_metrics(user_agents[0]) == ["m/E,e"]


async def test_reports_adaptive_retry_mode(tmp_path: Path) -> None:
    user_agents = await _call(tmp_path, _RecordingTransport(), retry_mode="adaptive")
    assert _business_metrics(user_agents[0]) == ["m/F,e"]


async def test_reports_adaptive_retry_mode_from_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AWS_RETRY_MODE", "adaptive")
    user_agents = await _call(tmp_path, _RecordingTransport())
    assert _business_metrics(user_agents[0]) == ["m/F,e"]


async def test_reports_endpoint_override(tmp_path: Path) -> None:
    user_agents = await _call(
        tmp_path, _RecordingTransport(), endpoint_uri="https://localhost:8443"
    )
    assert _business_metrics(user_agents[0]) == ["m/E,N,e"]


async def test_reports_endpoint_override_from_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AWS_ENDPOINT_URL_JSON_RPC_10", "https://localhost:8443")
    user_agents = await _call(tmp_path, _RecordingTransport())
    assert _business_metrics(user_agents[0]) == ["m/E,N,e"]


async def test_retried_call_sends_same_business_metrics_once(tmp_path: Path) -> None:
    user_agents = await _call(
        tmp_path,
        _RecordingTransport(throttle_first=True),
        endpoint_uri="https://localhost:8443",
    )
    assert len(user_agents) == 2
    assert [_business_metrics(ua) for ua in user_agents] == [["m/E,N,e"], ["m/E,N,e"]]


async def test_reports_process_resolver_used_directly(tmp_path: Path) -> None:
    script = _write_credentials_script(tmp_path)
    user_agents = await _call(
        tmp_path,
        _RecordingTransport(),
        aws_credentials_identity_resolver=AsyncProcessCredentialsResolver(
            [sys.executable, str(script)]
        ),
    )
    assert _business_metrics(user_agents[0]) == ["m/E,w"]


async def _call_with_credential_chain(
    tmp_path: Path, transport: _RecordingTransport, config_file: str = ""
) -> list[str]:
    # No credentials in code, so the client resolves them with its credential chain.
    config_path = tmp_path / "config"
    config_path.write_text(config_file)
    resolved = await AsyncJSONRPC10Config.resolve(
        config_file_path=str(config_path),
        credentials_file_path=str(tmp_path / "missing"),
        region="us-west-2",
        transport=transport,
    )
    client = AsyncJSONRPC10Client(config=resolved)
    for _ in range(2):  # The second call is served from cached credentials.
        await client.empty_input_and_empty_output(EmptyInputAndEmptyOutputInput())
    return transport.user_agents


async def test_reports_environment_credentials(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AKID")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")
    user_agents = await _call_with_credential_chain(tmp_path, _RecordingTransport())
    assert [_business_metrics(ua) for ua in user_agents] == [["m/E,g"], ["m/E,g"]]


async def test_reports_resolved_account_id(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AKID")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")
    monkeypatch.setenv("AWS_ACCOUNT_ID", "123456789012")
    user_agents = await _call_with_credential_chain(tmp_path, _RecordingTransport())
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
async def test_reports_profile_credentials(tmp_path: Path, config_file: str) -> None:
    user_agents = await _call_with_credential_chain(
        tmp_path, _RecordingTransport(), config_file
    )
    assert [_business_metrics(ua) for ua in user_agents] == [["m/E,n"], ["m/E,n"]]


async def test_reports_profile_credential_process(tmp_path: Path) -> None:
    script = _write_credentials_script(tmp_path)
    # Quoted so that paths with spaces stay one argument each.
    config_file = f'[default]\ncredential_process = "{sys.executable}" "{script}"\n'
    user_agents = await _call_with_credential_chain(
        tmp_path, _RecordingTransport(), config_file
    )
    assert _business_metrics(user_agents[0]) == ["m/E,v,w"]
