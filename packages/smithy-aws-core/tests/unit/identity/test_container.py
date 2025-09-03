#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json
import os
import typing
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from smithy_aws_core.identity import AWSCredentialsIdentity
from smithy_aws_core.identity.container import (
    ContainerCredentialsConfig,
    ContainerCredentialsResolver,
    ContainerMetadataClient,
)
from smithy_core import URI
from smithy_core.exceptions import SmithyIdentityError
from smithy_http import Fields

if typing.TYPE_CHECKING:
    import pathlib

DEFAULT_RESPONSE_DATA = {
    "AccessKeyId": "akid123",
    "SecretAccessKey": "s3cr3t",
    "Token": "session_token",
}

ISO8601 = "%Y-%m-%dT%H:%M:%SZ"


def test_config_custom_values():
    config = ContainerCredentialsConfig(timeout=10, retries=5)
    assert config.timeout == 10
    assert config.retries == 5


def mock_http_client_response(status: int, body: bytes):
    http_client = AsyncMock()
    response = AsyncMock()
    response.status = status
    response.consume_body_async.return_value = body
    http_client.send.return_value = response
    return http_client


def _assert_expected_credentials(
    creds: dict[str, str], access_key_id: str, secret_key_id: str, token: str
) -> None:
    assert creds["AccessKeyId"] == access_key_id
    assert creds["SecretAccessKey"] == secret_key_id
    assert creds["Token"] == token


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "host",
    ["169.254.170.2", "169.254.170.23", "fd00:ec2::23", "localhost", "127.0.0.2"],
)
async def test_metadata_client_valid_host(host: str):
    resp_body = json.dumps(DEFAULT_RESPONSE_DATA)
    http_client = mock_http_client_response(200, resp_body.encode("utf-8"))
    config = ContainerCredentialsConfig()
    client = ContainerMetadataClient(http_client, config)

    # Valid Host
    uri = URI(scheme="http", host=host)

    creds = await client.get_credentials(uri, Fields())
    _assert_expected_credentials(creds, "akid123", "s3cr3t", "session_token")


@pytest.mark.asyncio
async def test_metadata_client_https_host():
    resp_body = json.dumps(DEFAULT_RESPONSE_DATA)
    http_client = mock_http_client_response(200, resp_body.encode("utf-8"))
    config = ContainerCredentialsConfig()
    client = ContainerMetadataClient(http_client, config)

    # Valid HTTPS Host
    uri = URI(scheme="https", host="169.254.170.2")

    creds = await client.get_credentials(uri, Fields())
    _assert_expected_credentials(creds, "akid123", "s3cr3t", "session_token")


@pytest.mark.asyncio
async def test_metadata_client_invalid_host():
    resp_body = json.dumps(DEFAULT_RESPONSE_DATA)
    http_client = mock_http_client_response(200, resp_body.encode("utf-8"))
    config = ContainerCredentialsConfig(retries=0)
    client = ContainerMetadataClient(http_client, config)

    # Invalid Host
    uri = URI(scheme="http", host="169.254.169.254")

    with pytest.raises(SmithyIdentityError):
        await client.get_credentials(uri, Fields())


@pytest.mark.asyncio
async def test_metadata_client_non_200_response():
    http_client = mock_http_client_response(404, b"not found")
    config = ContainerCredentialsConfig(retries=1)
    client = ContainerMetadataClient(http_client, config)

    uri = URI(scheme="http", host="169.254.170.2")
    with pytest.raises(SmithyIdentityError) as e:
        await client.get_credentials(uri, Fields())

    # Ensure both the received retry error and underlying error are what we expect.
    assert "Container metadata service returned 404" in str(e.value.__cause__)
    assert "Failed to retrieve container metadata after 1 attempt(s)" in str(e.value)


@pytest.mark.asyncio
async def test_metadata_client_invalid_json():
    http_client = mock_http_client_response(
        200, b"<!DOCTYPE html><head><title>proxy</title>"
    )
    config = ContainerCredentialsConfig(retries=1)
    client = ContainerMetadataClient(http_client, config)

    uri = URI(scheme="http", host="169.254.170.2")
    with pytest.raises(SmithyIdentityError):
        await client.get_credentials(uri, Fields())


def _assert_expected_identity(identity: AWSCredentialsIdentity) -> None:
    assert identity.access_key_id == DEFAULT_RESPONSE_DATA["AccessKeyId"]
    assert identity.secret_access_key == DEFAULT_RESPONSE_DATA["SecretAccessKey"]
    assert identity.session_token == DEFAULT_RESPONSE_DATA["Token"]


@pytest.mark.asyncio
async def test_metadata_client_retries():
    http_client = AsyncMock()
    config = ContainerCredentialsConfig(retries=2)
    client = ContainerMetadataClient(http_client, config)
    uri = URI(scheme="http", host="169.254.170.2", path="/task")
    http_client.send.side_effect = Exception()

    with pytest.raises(SmithyIdentityError):
        await client.get_credentials(uri, Fields())
    assert http_client.send.call_count == 2


@pytest.mark.asyncio
async def test_resolver_env_relative():
    resp_body = json.dumps(DEFAULT_RESPONSE_DATA)
    http_client = mock_http_client_response(200, resp_body.encode("utf-8"))

    with patch.dict(
        os.environ, {ContainerCredentialsResolver.ENV_VAR: "/test"}, clear=True
    ):
        resolver = ContainerCredentialsResolver(http_client)
        identity = await resolver.get_identity(properties={})

    # Ensure we derive the correct destination
    expected_url = URI(
        scheme="http",
        host="169.254.170.2",
        path="/test",
    )
    http_request = http_client.send.call_args_list[0].args[0]
    assert http_request.destination == expected_url

    _assert_expected_identity(identity)


@pytest.mark.asyncio
async def test_resolver_env_full():
    resp_body = json.dumps(DEFAULT_RESPONSE_DATA)
    http_client = mock_http_client_response(200, resp_body.encode("utf-8"))

    with patch.dict(
        os.environ,
        {ContainerCredentialsResolver.ENV_VAR_FULL: "http://169.254.170.23/full"},
        clear=True,
    ):
        resolver = ContainerCredentialsResolver(http_client)
        identity = await resolver.get_identity(properties={})

    # Ensure we derive the correct destination
    expected_url = URI(
        scheme="http",
        host="169.254.170.23",
        path="/full",
    )
    http_request = http_client.send.call_args_list[0].args[0]
    assert http_request.destination == expected_url

    _assert_expected_identity(identity)


@pytest.mark.asyncio
async def test_resolver_env_token():
    resp_body = json.dumps(DEFAULT_RESPONSE_DATA)
    http_client = mock_http_client_response(200, resp_body.encode("utf-8"))

    with patch.dict(
        os.environ,
        {
            ContainerCredentialsResolver.ENV_VAR_FULL: "http://169.254.170.23/full",
            ContainerCredentialsResolver.ENV_VAR_AUTH_TOKEN: "Bearer foobar",
        },
        clear=True,
    ):
        resolver = ContainerCredentialsResolver(http_client)
        identity = await resolver.get_identity(properties={})

    # Ensure we derive the correct destination and fields
    expected_url = URI(
        scheme="http",
        host="169.254.170.23",
        path="/full",
    )
    http_request = http_client.send.call_args_list[0].args[0]
    assert http_request.destination == expected_url

    assert "Authorization" in http_request.fields
    auth_field = http_request.fields.get("Authorization")
    assert auth_field.as_string() == "Bearer foobar"

    _assert_expected_identity(identity)


@pytest.mark.asyncio
async def test_resolver_env_token_file(tmp_path: pathlib.Path):
    resp_body = json.dumps(DEFAULT_RESPONSE_DATA)
    http_client = mock_http_client_response(200, resp_body.encode("utf-8"))

    token_file = tmp_path / "token_file"
    token_file.write_text("Bearer barfoo")

    with patch.dict(
        os.environ,
        {
            ContainerCredentialsResolver.ENV_VAR_FULL: "http://169.254.170.23/full",
            ContainerCredentialsResolver.ENV_VAR_AUTH_TOKEN_FILE: str(token_file),
        },
        clear=True,
    ):
        resolver = ContainerCredentialsResolver(http_client)
        identity = await resolver.get_identity(properties={})

    # Ensure we derive the correct destination and fields
    expected_url = URI(
        scheme="http",
        host="169.254.170.23",
        path="/full",
    )
    http_request = http_client.send.call_args_list[0].args[0]
    assert http_request.destination == expected_url

    assert "Authorization" in http_request.fields
    auth_field = http_request.fields.get("Authorization")
    assert auth_field.as_string() == "Bearer barfoo"

    _assert_expected_identity(identity)


@pytest.mark.asyncio
async def test_resolver_env_token_file_invalid_bytes(tmp_path: pathlib.Path):
    resp_body = json.dumps(DEFAULT_RESPONSE_DATA)
    http_client = mock_http_client_response(200, resp_body.encode("utf-8"))

    token_file = tmp_path / "token_file"
    token_file.write_bytes(b"Bearer bar\xff\xfe\xfafoo")

    with patch.dict(
        os.environ,
        {
            ContainerCredentialsResolver.ENV_VAR_FULL: "http://169.254.170.23/full",
            ContainerCredentialsResolver.ENV_VAR_AUTH_TOKEN_FILE: str(token_file),
        },
        clear=True,
    ):
        resolver = ContainerCredentialsResolver(http_client)
        with pytest.raises(SmithyIdentityError) as e:
            await resolver.get_identity(properties={})
        assert "Unable to read valid utf-8 bytes from " in str(e.value)


@pytest.mark.asyncio
async def test_resolver_env_token_file_precedence(tmp_path: pathlib.Path):
    """Validate the token file is used over the explicit value if both are set."""
    resp_body = json.dumps(DEFAULT_RESPONSE_DATA)
    http_client = mock_http_client_response(200, resp_body.encode("utf-8"))

    token_file = tmp_path / "token_file"
    token_file.write_text("Bearer barfoo")

    with patch.dict(
        os.environ,
        {
            ContainerCredentialsResolver.ENV_VAR_FULL: "http://169.254.170.23/full",
            ContainerCredentialsResolver.ENV_VAR_AUTH_TOKEN_FILE: str(token_file),
            ContainerCredentialsResolver.ENV_VAR_AUTH_TOKEN: "Bearer foobar",
        },
        clear=True,
    ):
        resolver = ContainerCredentialsResolver(http_client)
        identity = await resolver.get_identity(properties={})

    # Ensure we derive the correct destination and fields
    expected_url = URI(
        scheme="http",
        host="169.254.170.23",
        path="/full",
    )
    http_request = http_client.send.call_args_list[0].args[0]
    assert http_request.destination == expected_url

    assert "Authorization" in http_request.fields
    auth_field = http_request.fields.get("Authorization")
    assert auth_field.as_string() == "Bearer barfoo"

    _assert_expected_identity(identity)


@pytest.mark.asyncio
async def test_resolver_valid_credentials_reused():
    custom_resp_data = dict(DEFAULT_RESPONSE_DATA)
    current_time = datetime.now(UTC) + timedelta(minutes=10)
    custom_resp_data["Expiration"] = current_time.strftime(ISO8601)

    resp_body = json.dumps(custom_resp_data)
    http_client = mock_http_client_response(200, resp_body.encode("utf-8"))

    with patch.dict(
        os.environ, {ContainerCredentialsResolver.ENV_VAR: "/test"}, clear=True
    ):
        resolver = ContainerCredentialsResolver(http_client)
        identity_one = await resolver.get_identity(properties={})
        identity_two = await resolver.get_identity(properties={})

    _assert_expected_identity(identity_one)
    # Validate we got the same unexpired identity instance from both calls
    assert identity_one is identity_two


@pytest.mark.asyncio
async def test_resolver_expired_credentials_refreshed():
    custom_resp_data = dict(DEFAULT_RESPONSE_DATA)
    current_time = datetime.now(UTC) - timedelta(minutes=10)
    custom_resp_data["Expiration"] = current_time.strftime(ISO8601)

    resp_body = json.dumps(custom_resp_data)
    http_client = mock_http_client_response(200, resp_body.encode("utf-8"))

    with patch.dict(
        os.environ, {ContainerCredentialsResolver.ENV_VAR: "/test"}, clear=True
    ):
        resolver = ContainerCredentialsResolver(http_client)
        identity_one = await resolver.get_identity(properties={})
        identity_two = await resolver.get_identity(properties={})

    _assert_expected_identity(identity_one)

    # Validate we got new credentials after we received an expired instance
    assert identity_one.access_key_id == identity_two.access_key_id
    assert identity_one.secret_access_key == identity_two.secret_access_key
    assert identity_one.session_token == identity_two.session_token
    assert identity_one is not identity_two


@pytest.mark.asyncio
async def test_resolver_missing_env():
    resp_body = json.dumps(DEFAULT_RESPONSE_DATA)
    http_client = mock_http_client_response(200, resp_body.encode("utf-8"))

    with patch.dict(
        os.environ,
        {},
        clear=True,
    ):
        resolver = ContainerCredentialsResolver(http_client)
        with pytest.raises(SmithyIdentityError):
            await resolver.get_identity(properties={})
