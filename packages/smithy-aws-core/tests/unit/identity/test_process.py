#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest
from smithy_aws_core.identity.components import (
    AWSCredentialsIdentity,
    AWSIdentityProperties,
)
from smithy_aws_core.identity.process import (
    ProcessCredentialsConfig,
    ProcessCredentialsResolver,
)
from smithy_core.aio.identity import ChainedIdentityResolver
from smithy_core.exceptions import SmithyIdentityError

ISO8601 = "%Y-%m-%dT%H:%M:%SZ"

DEFAULT_RESPONSE_DATA = {
    "Version": 1,
    "AccessKeyId": "akid123",
    "SecretAccessKey": "s3cr3t",
    "SessionToken": "session_token",
}


def test_config_default_values():
    config = ProcessCredentialsConfig()
    assert config.timeout == 30


def test_config_custom_values():
    config = ProcessCredentialsConfig(timeout=60)
    assert config.timeout == 60


def test_resolver_empty_command():
    with pytest.raises(ValueError, match="command must be a non-empty string or list"):
        ProcessCredentialsResolver([])


def test_resolver_none_command():
    with pytest.raises(ValueError, match="command must be a non-empty string or list"):
        ProcessCredentialsResolver(None)  # type: ignore[arg-type]


def test_resolver_empty_command_string():
    with pytest.raises(ValueError, match="command must be a non-empty string or list"):
        ProcessCredentialsResolver("")


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

    assert identity.access_key_id == "akid123"
    assert identity.secret_access_key == "s3cr3t"
    assert identity.session_token == "session_token"
    assert identity.expiration is None
    assert identity.account_id is None


@pytest.mark.asyncio
async def test_valid_credentials_without_session_token():
    resp_data = {
        "Version": 1,
        "AccessKeyId": "akid456",
        "SecretAccessKey": "s3cr3t456",
    }
    resp_body = json.dumps(resp_data)
    process = mock_subprocess(0, resp_body.encode("utf-8"))

    with patch("asyncio.create_subprocess_exec", return_value=process):
        resolver = ProcessCredentialsResolver(["mock-process"])
        identity = await resolver.get_identity(properties={})

    assert identity.access_key_id == "akid456"
    assert identity.secret_access_key == "s3cr3t456"
    assert identity.session_token is None


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
        "SecretAccessKey": "s3cr3t",
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
        "AccessKeyId": "akid123",
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
        "AccessKeyId": "akid123",
        "SecretAccessKey": "s3cr3t",
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
        with pytest.raises(json.JSONDecodeError):
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
async def test_process_startup_failure_allows_chained_fallback():
    class SuccessfulResolver:
        async def get_identity(
            self, *, properties: AWSIdentityProperties
        ) -> AWSCredentialsIdentity:
            return AWSCredentialsIdentity(
                access_key_id="fallback-akid",
                secret_access_key="fallback-secret",
            )

    with patch(
        "asyncio.create_subprocess_exec",
        side_effect=FileNotFoundError("No such file or directory"),
    ):
        resolver = ChainedIdentityResolver(
            [
                ProcessCredentialsResolver(["missing-process"]),
                SuccessfulResolver(),
            ]
        )
        identity = await resolver.get_identity(properties={})

    assert identity.access_key_id == "fallback-akid"
    assert identity.secret_access_key == "fallback-secret"


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
    resp_data = dict(DEFAULT_RESPONSE_DATA)
    resp_data["Expiration"] = expired_time.strftime(ISO8601)

    resp_body = json.dumps(resp_data)
    process = mock_subprocess(0, resp_body.encode("utf-8"))

    with patch("asyncio.create_subprocess_exec", return_value=process) as mock_exec:
        resolver = ProcessCredentialsResolver(["mock-process"])
        identity_one = await resolver.get_identity(properties={})
        identity_two = await resolver.get_identity(properties={})

    # Process should be called twice (once for initial, once for refresh)
    assert mock_exec.call_count == 2
    # Should be different instances
    assert identity_one is not identity_two
    # But have the same values
    assert identity_one.access_key_id == identity_two.access_key_id
    assert identity_one.secret_access_key == identity_two.secret_access_key


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
