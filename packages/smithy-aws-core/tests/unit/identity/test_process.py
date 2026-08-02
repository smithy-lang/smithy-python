#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import asyncio
import json
import traceback
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest
from smithy_aws_core.identity.process import ProcessCredentialsResolver
from smithy_core.exceptions import SmithyIdentityError

ISO8601 = "%Y-%m-%dT%H:%M:%SZ"

DEFAULT_RESPONSE_DATA = {
    "Version": 1,
    "AccessKeyId": "foo",
    "SecretAccessKey": "bar",
    "SessionToken": "baz",
}


@pytest.mark.parametrize("command", [[], None, "mock-process", ["mock-process", 1]])
def test_resolver_invalid_command(command: object):
    with pytest.raises(ValueError, match="command must be a non-empty list"):
        ProcessCredentialsResolver(command)  # type: ignore[arg-type]


def mock_subprocess(returncode: int, stdout: bytes, stderr: bytes = b""):
    """Helper to mock asyncio.create_subprocess_exec"""
    process = AsyncMock()
    process.returncode = returncode
    process.communicate.return_value = (stdout, stderr)
    return process


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


async def test_invalid_expiration_string():
    resp_data = dict(DEFAULT_RESPONSE_DATA)
    resp_data["Expiration"] = "not-a-timestamp"

    resp_body = json.dumps(resp_data)
    process = mock_subprocess(0, resp_body.encode("utf-8"))

    with patch("asyncio.create_subprocess_exec", return_value=process):
        resolver = ProcessCredentialsResolver(["mock-process"])
        with pytest.raises(
            SmithyIdentityError,
            match="Invalid credential process Expiration; expected an ISO 8601 string",
        ):
            await resolver.get_identity(properties={})


async def test_non_string_expiration():
    resp_data = dict(DEFAULT_RESPONSE_DATA)
    resp_data["Expiration"] = 12345

    resp_body = json.dumps(resp_data)
    process = mock_subprocess(0, resp_body.encode("utf-8"))

    with patch("asyncio.create_subprocess_exec", return_value=process):
        resolver = ProcessCredentialsResolver(["mock-process"])
        with pytest.raises(
            SmithyIdentityError,
            match="Invalid credential process Expiration; expected an ISO 8601 string",
        ):
            await resolver.get_identity(properties={})


async def test_credentials_with_account_id():
    resp_data = dict(DEFAULT_RESPONSE_DATA)
    resp_data["AccountId"] = "123456789012"

    resp_body = json.dumps(resp_data)
    process = mock_subprocess(0, resp_body.encode("utf-8"))

    with patch("asyncio.create_subprocess_exec", return_value=process):
        resolver = ProcessCredentialsResolver(["mock-process"])
        identity = await resolver.get_identity(properties={})

    assert identity.account_id == "123456789012"


async def test_account_id_falls_back_to_configured_value():
    """The configured account_id is used when the process omits AccountId."""
    resp_body = json.dumps(DEFAULT_RESPONSE_DATA)
    process = mock_subprocess(0, resp_body.encode("utf-8"))

    with patch("asyncio.create_subprocess_exec", return_value=process):
        resolver = ProcessCredentialsResolver(
            ["mock-process"], account_id="123456789012"
        )
        identity = await resolver.get_identity(properties={})

    assert identity.account_id == "123456789012"


async def test_process_account_id_takes_precedence_over_configured_value():
    """The process output's AccountId wins over the configured fallback."""
    resp_data = dict(DEFAULT_RESPONSE_DATA)
    resp_data["AccountId"] = "111111111111"

    resp_body = json.dumps(resp_data)
    process = mock_subprocess(0, resp_body.encode("utf-8"))

    with patch("asyncio.create_subprocess_exec", return_value=process):
        resolver = ProcessCredentialsResolver(
            ["mock-process"], account_id="222222222222"
        )
        identity = await resolver.get_identity(properties={})

    assert identity.account_id == "111111111111"


async def test_non_zero_exit_code():
    process = mock_subprocess(1, b"", b"Process error message")

    with patch("asyncio.create_subprocess_exec", return_value=process):
        resolver = ProcessCredentialsResolver(["mock-process"])
        with pytest.raises(
            SmithyIdentityError,
            match="exit code 1: Process error message",
        ):
            await resolver.get_identity(properties={})


@pytest.mark.parametrize(
    "resp_data",
    [
        {"Version": 1, "SecretAccessKey": "bar"},
        {"Version": 1, "AccessKeyId": "foo"},
    ],
)
async def test_missing_required_credentials(resp_data: dict[str, object]):
    resp_body = json.dumps(resp_data)
    process = mock_subprocess(0, resp_body.encode("utf-8"))

    with patch("asyncio.create_subprocess_exec", return_value=process):
        resolver = ProcessCredentialsResolver(["mock-process"])
        with pytest.raises(
            SmithyIdentityError,
            match="AccessKeyId and SecretAccessKey are required",
        ):
            await resolver.get_identity(properties={})


async def test_invalid_version():
    resp_data = dict(DEFAULT_RESPONSE_DATA)
    resp_data["Version"] = 2

    resp_body = json.dumps(resp_data)
    process = mock_subprocess(0, resp_body.encode("utf-8"))

    with patch("asyncio.create_subprocess_exec", return_value=process):
        resolver = ProcessCredentialsResolver(["mock-process"])
        with pytest.raises(SmithyIdentityError, match="Unsupported version '2'"):
            await resolver.get_identity(properties={})


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


async def test_invalid_json():
    process = mock_subprocess(0, b'{"SecretAccessKey": "json-secret"')

    with patch("asyncio.create_subprocess_exec", return_value=process):
        resolver = ProcessCredentialsResolver(["mock-process"])
        with pytest.raises(
            SmithyIdentityError,
            match="Credential process output is not valid JSON at line 1, column",
        ) as exc_info:
            await resolver.get_identity(properties={})

    rendered = "".join(traceback.format_exception(exc_info.value))
    assert "json-secret" not in rendered


async def test_invalid_utf8():
    process = mock_subprocess(0, b'{"SecretAccessKey": "utf8-secret"}\xff')

    with patch("asyncio.create_subprocess_exec", return_value=process):
        resolver = ProcessCredentialsResolver(["mock-process"])
        with pytest.raises(
            SmithyIdentityError,
            match="Credential process output is not valid UTF-8 at byte",
        ) as exc_info:
            await resolver.get_identity(properties={})

    rendered = "".join(traceback.format_exception(exc_info.value))
    assert "utf8-secret" not in rendered


async def test_process_timeout():
    process = AsyncMock()
    process.returncode = None
    process.kill = Mock()
    process.wait = AsyncMock()

    with (
        patch("asyncio.create_subprocess_exec", return_value=process),
        patch("asyncio.wait_for", side_effect=TimeoutError),
    ):
        resolver = ProcessCredentialsResolver(["mock-process"], timeout=1)
        with pytest.raises(SmithyIdentityError, match="timed out after 1 seconds"):
            await resolver.get_identity(properties={})

    process.kill.assert_called_once_with()
    process.wait.assert_awaited_once_with()


async def test_process_startup_failure_raises_smithy_identity_error():
    with patch(
        "asyncio.create_subprocess_exec",
        side_effect=FileNotFoundError("No such file or directory"),
    ):
        resolver = ProcessCredentialsResolver(["missing-process"])
        with pytest.raises(SmithyIdentityError, match="failed to start"):
            await resolver.get_identity(properties={})


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


async def test_invalidate_clears_cached_credentials():
    resp_body = json.dumps(DEFAULT_RESPONSE_DATA)
    first_process = mock_subprocess(0, resp_body.encode("utf-8"))
    second_process = mock_subprocess(0, resp_body.encode("utf-8"))

    with patch(
        "asyncio.create_subprocess_exec",
        side_effect=[first_process, second_process],
    ) as mock_exec:
        resolver = ProcessCredentialsResolver(["mock-process"])
        identity_one = await resolver.get_identity(properties={})
        await resolver.invalidate()
        identity_two = await resolver.get_identity(properties={})

    assert mock_exec.call_count == 2
    assert identity_one is not identity_two


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
