#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest
from smithy_aws_core.identity.process import (
    ProcessCredentialsConfig,
    ProcessCredentialsResolver,
)
from smithy_core.exceptions import SmithyIdentityError

ISO8601 = "%Y-%m-%dT%H:%M:%SZ"

DEFAULT_RESPONSE_DATA = {
    "Version": 1,
    "AccessKeyId": "foo",
    "SecretAccessKey": "bar",
    "SessionToken": "baz",
}


def test_config_default_values():
    config = ProcessCredentialsConfig()
    assert config.timeout == 30


def test_config_custom_values():
    config = ProcessCredentialsConfig(timeout=60)
    assert config.timeout == 60


@pytest.mark.parametrize("command", [[], "", None])
def test_resolver_invalid_command(command: object):
    with pytest.raises(ValueError, match="command must be a non-empty string or list"):
        ProcessCredentialsResolver(command)  # type: ignore[arg-type]


def mock_subprocess(returncode: int, stdout: bytes, stderr: bytes = b""):
    """Helper to mock asyncio.create_subprocess_exec"""
    process = AsyncMock()
    process.returncode = returncode
    process.communicate.return_value = (stdout, stderr)
    return process


@pytest.mark.asyncio
async def test_valid_credentials_with_session_token():
    resp_body = json.dumps(DEFAULT_RESPONSE_DATA)
    process = mock_subprocess(0, resp_body.encode("utf-8"))

    with patch("asyncio.create_subprocess_exec", return_value=process):
        resolver = ProcessCredentialsResolver(["mock-process"])
        identity = await resolver.get_identity(properties={})

    assert identity.access_key_id == "foo"
    assert identity.secret_access_key == "bar"
    assert identity.session_token == "baz"
    assert identity.expiration is None
    assert identity.account_id is None


@pytest.mark.asyncio
async def test_valid_credentials_without_session_token():
    resp_data = {
        "Version": 1,
        "AccessKeyId": "foo",
        "SecretAccessKey": "bar",
    }
    resp_body = json.dumps(resp_data)
    process = mock_subprocess(0, resp_body.encode("utf-8"))

    with patch("asyncio.create_subprocess_exec", return_value=process):
        resolver = ProcessCredentialsResolver(["mock-process"])
        identity = await resolver.get_identity(properties={})

    assert identity.access_key_id == "foo"
    assert identity.secret_access_key == "bar"
    assert identity.session_token is None


@pytest.mark.asyncio
async def test_missing_expiration():
    resp_body = json.dumps(DEFAULT_RESPONSE_DATA)
    process = mock_subprocess(0, resp_body.encode("utf-8"))

    with patch("asyncio.create_subprocess_exec", return_value=process):
        resolver = ProcessCredentialsResolver(["mock-process"])
        identity = await resolver.get_identity(properties={})

    assert identity.access_key_id == "foo"
    assert identity.secret_access_key == "bar"
    assert identity.session_token == "baz"
    assert identity.expiration is None


@pytest.mark.asyncio
async def test_missing_expiration_and_session_token():
    resp_data = {
        "Version": 1,
        "AccessKeyId": "foo",
        "SecretAccessKey": "bar",
    }
    resp_body = json.dumps(resp_data)
    process = mock_subprocess(0, resp_body.encode("utf-8"))

    with patch("asyncio.create_subprocess_exec", return_value=process):
        resolver = ProcessCredentialsResolver(["mock-process"])
        identity = await resolver.get_identity(properties={})

    assert identity.access_key_id == "foo"
    assert identity.secret_access_key == "bar"
    assert identity.session_token is None
    assert identity.expiration is None


@pytest.mark.asyncio
async def test_credentials_with_expiration():
    current_time = datetime.now(UTC) + timedelta(minutes=10)
    resp_data = dict(DEFAULT_RESPONSE_DATA)
    resp_data["Expiration"] = current_time.strftime(ISO8601)

    resp_body = json.dumps(resp_data)
    process = mock_subprocess(0, resp_body.encode("utf-8"))

    with patch("asyncio.create_subprocess_exec", return_value=process):
        resolver = ProcessCredentialsResolver(["mock-process"])
        identity = await resolver.get_identity(properties={})

    assert identity.expiration is not None
    assert identity.expiration.tzinfo == UTC


@pytest.mark.asyncio
async def test_credentials_with_non_utc_expiration():
    """Test that non-UTC expiration timestamps are correctly converted to UTC."""
    # 2026-03-16T10:00:00+05:00 should become 2026-03-16T05:00:00 UTC
    resp_data = dict(DEFAULT_RESPONSE_DATA)
    resp_data["Expiration"] = "2026-03-16T10:00:00+05:00"

    resp_body = json.dumps(resp_data)
    process = mock_subprocess(0, resp_body.encode("utf-8"))

    with patch("asyncio.create_subprocess_exec", return_value=process):
        resolver = ProcessCredentialsResolver(["mock-process"])
        identity = await resolver.get_identity(properties={})

    assert identity.expiration is not None
    assert identity.expiration.tzinfo == UTC
    assert identity.expiration == datetime(2026, 3, 16, 5, 0, 0, tzinfo=UTC)


@pytest.mark.asyncio
async def test_credentials_with_account_id():
    resp_data = dict(DEFAULT_RESPONSE_DATA)
    resp_data["AccountId"] = "123456789012"

    resp_body = json.dumps(resp_data)
    process = mock_subprocess(0, resp_body.encode("utf-8"))

    with patch("asyncio.create_subprocess_exec", return_value=process):
        resolver = ProcessCredentialsResolver(["mock-process"])
        identity = await resolver.get_identity(properties={})

    assert identity.account_id == "123456789012"


@pytest.mark.asyncio
async def test_non_zero_exit_code():
    process = mock_subprocess(1, b"", b"Process error message")

    with patch("asyncio.create_subprocess_exec", return_value=process):
        resolver = ProcessCredentialsResolver(["mock-process"])
        with pytest.raises(SmithyIdentityError, match="non-zero exit code"):
            await resolver.get_identity(properties={})


@pytest.mark.asyncio
async def test_missing_access_key_id():
    resp_data = {
        "Version": 1,
        "SecretAccessKey": "bar",
    }
    resp_body = json.dumps(resp_data)
    process = mock_subprocess(0, resp_body.encode("utf-8"))

    with patch("asyncio.create_subprocess_exec", return_value=process):
        resolver = ProcessCredentialsResolver(["mock-process"])
        with pytest.raises(
            SmithyIdentityError,
            match="AccessKeyId and SecretAccessKey are required",
        ):
            await resolver.get_identity(properties={})


@pytest.mark.asyncio
async def test_missing_secret_access_key():
    resp_data = {
        "Version": 1,
        "AccessKeyId": "foo",
    }
    resp_body = json.dumps(resp_data)
    process = mock_subprocess(0, resp_body.encode("utf-8"))

    with patch("asyncio.create_subprocess_exec", return_value=process):
        resolver = ProcessCredentialsResolver(["mock-process"])
        with pytest.raises(
            SmithyIdentityError,
            match="AccessKeyId and SecretAccessKey are required",
        ):
            await resolver.get_identity(properties={})


@pytest.mark.asyncio
async def test_invalid_version():
    resp_data = dict(DEFAULT_RESPONSE_DATA)
    resp_data["Version"] = 2

    resp_body = json.dumps(resp_data)
    process = mock_subprocess(0, resp_body.encode("utf-8"))

    with patch("asyncio.create_subprocess_exec", return_value=process):
        resolver = ProcessCredentialsResolver(["mock-process"])
        with pytest.raises(SmithyIdentityError, match="Unsupported version '2'"):
            await resolver.get_identity(properties={})


@pytest.mark.asyncio
async def test_missing_version():
    resp_data = {
        "AccessKeyId": "foo",
        "SecretAccessKey": "bar",
    }
    resp_body = json.dumps(resp_data)
    process = mock_subprocess(0, resp_body.encode("utf-8"))

    with patch("asyncio.create_subprocess_exec", return_value=process):
        resolver = ProcessCredentialsResolver(["mock-process"])
        with pytest.raises(SmithyIdentityError, match="Unsupported version 'None'"):
            await resolver.get_identity(properties={})


@pytest.mark.asyncio
async def test_invalid_json():
    process = mock_subprocess(0, b"not valid json")

    with patch("asyncio.create_subprocess_exec", return_value=process):
        resolver = ProcessCredentialsResolver(["mock-process"])
        with pytest.raises(SmithyIdentityError, match="Failed to parse"):
            await resolver.get_identity(properties={})


@pytest.mark.asyncio
async def test_process_timeout():
    process = AsyncMock()
    process.returncode = None
    process.communicate = AsyncMock(side_effect=TimeoutError)
    process.kill = Mock()
    process.wait = AsyncMock()

    config = ProcessCredentialsConfig(timeout=1)

    with patch("asyncio.create_subprocess_exec", return_value=process):
        resolver = ProcessCredentialsResolver(["mock-process"], config=config)
        with pytest.raises(SmithyIdentityError, match="timed out after 1 seconds"):
            await resolver.get_identity(properties={})

    process.kill.assert_called_once_with()
    process.wait.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_process_startup_failure_raises_smithy_identity_error():
    with patch(
        "asyncio.create_subprocess_exec",
        side_effect=FileNotFoundError("No such file or directory"),
    ):
        resolver = ProcessCredentialsResolver(["missing-process"])
        with pytest.raises(SmithyIdentityError, match="failed to start"):
            await resolver.get_identity(properties={})


@pytest.mark.asyncio
async def test_long_term_credentials_cached():
    """Test that credentials without expiration are cached indefinitely."""
    resp_body = json.dumps(DEFAULT_RESPONSE_DATA)
    process = mock_subprocess(0, resp_body.encode("utf-8"))

    with patch("asyncio.create_subprocess_exec", return_value=process) as mock_exec:
        resolver = ProcessCredentialsResolver(["mock-process"])
        identity_one = await resolver.get_identity(properties={})
        identity_two = await resolver.get_identity(properties={})

    # Process should only be called once
    assert mock_exec.call_count == 1
    # Should return the same identity instance
    assert identity_one is identity_two


@pytest.mark.asyncio
async def test_temporary_credentials_cached_when_valid():
    """Test that temporary credentials are cached when not expired."""
    current_time = datetime.now(UTC) + timedelta(minutes=10)
    resp_data = dict(DEFAULT_RESPONSE_DATA)
    resp_data["Expiration"] = current_time.strftime(ISO8601)

    resp_body = json.dumps(resp_data)
    process = mock_subprocess(0, resp_body.encode("utf-8"))

    with patch("asyncio.create_subprocess_exec", return_value=process) as mock_exec:
        resolver = ProcessCredentialsResolver(["mock-process"])
        identity_one = await resolver.get_identity(properties={})
        identity_two = await resolver.get_identity(properties={})

    # Process should only be called once
    assert mock_exec.call_count == 1
    # Should return the same identity instance
    assert identity_one is identity_two


@pytest.mark.asyncio
async def test_expired_credentials_refreshed():
    """Test that expired credentials are refreshed."""
    expired_time = datetime.now(UTC) - timedelta(minutes=10)
    initial_data = dict(DEFAULT_RESPONSE_DATA)
    initial_data["Expiration"] = expired_time.strftime(ISO8601)

    refreshed_time = datetime.now(UTC) + timedelta(minutes=10)
    refreshed_data = {
        "Version": 1,
        "AccessKeyId": "foo-refreshed",
        "SecretAccessKey": "bar-refreshed",
        "SessionToken": "baz-refreshed",
        "Expiration": refreshed_time.strftime(ISO8601),
    }

    first_process = mock_subprocess(0, json.dumps(initial_data).encode("utf-8"))
    second_process = mock_subprocess(0, json.dumps(refreshed_data).encode("utf-8"))

    with patch(
        "asyncio.create_subprocess_exec",
        side_effect=[first_process, second_process],
    ) as mock_exec:
        resolver = ProcessCredentialsResolver(["mock-process"])
        identity_one = await resolver.get_identity(properties={})
        identity_two = await resolver.get_identity(properties={})

    # Process should be called twice (once for initial, once for refresh)
    assert mock_exec.call_count == 2
    # Should be different instances
    assert identity_one is not identity_two
    assert identity_one.access_key_id == "foo"
    assert identity_one.secret_access_key == "bar"
    assert identity_one.session_token == "baz"
    assert identity_two.access_key_id == "foo-refreshed"
    assert identity_two.secret_access_key == "bar-refreshed"
    assert identity_two.session_token == "baz-refreshed"


@pytest.mark.asyncio
async def test_command_with_multiple_args():
    """Test that commands with multiple arguments are passed correctly."""
    resp_body = json.dumps(DEFAULT_RESPONSE_DATA)
    process = mock_subprocess(0, resp_body.encode("utf-8"))

    with patch("asyncio.create_subprocess_exec", return_value=process) as mock_exec:
        resolver = ProcessCredentialsResolver(
            ["aws-credential-helper", "--profile", "test", "--format", "json"]
        )
        await resolver.get_identity(properties={})

    # Verify the command was called with all arguments
    mock_exec.assert_called_once_with(
        "aws-credential-helper",
        "--profile",
        "test",
        "--format",
        "json",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )


@pytest.mark.asyncio
async def test_string_command_with_multiple_args():
    resp_body = json.dumps(DEFAULT_RESPONSE_DATA)
    process = mock_subprocess(0, resp_body.encode("utf-8"))

    with patch("asyncio.create_subprocess_exec", return_value=process) as mock_exec:
        resolver = ProcessCredentialsResolver(
            'aws-credential-helper --profile "test profile" --format json'
        )
        await resolver.get_identity(properties={})

    mock_exec.assert_called_once_with(
        "aws-credential-helper",
        "--profile",
        "test profile",
        "--format",
        "json",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
