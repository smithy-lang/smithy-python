from __future__ import annotations

import json
import os
import typing
from unittest.mock import AsyncMock, patch

import pytest
from smithy_aws_core.credentials_resolvers.container import (
    ContainerCredentialConfig,
    ContainerCredentialResolver,
    ContainerMetadataClient,
)
from smithy_aws_core.identity import AWSCredentialsIdentity
from smithy_core import URI
from smithy_core.exceptions import SmithyIdentityException
from smithy_http import Fields

if typing.TYPE_CHECKING:
    import pathlib

DEFAULT_RESPONSE_DATA = {
    "AccessKeyId": "akid123",
    "SecretAccessKey": "s3cr3t",
    "Token": "session_token",
}


def test_config_custom_values():
    config = ContainerCredentialConfig(timeout=10, retries=5)
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
    config = ContainerCredentialConfig()
    client = ContainerMetadataClient(http_client, config)

    # Valid Host
    uri = URI(scheme="http", host=host)

    creds = await client.get_credentials(uri, Fields())
    _assert_expected_credentials(creds, "akid123", "s3cr3t", "session_token")


@pytest.mark.asyncio
async def test_metadata_client_https_host():
    resp_body = json.dumps(DEFAULT_RESPONSE_DATA)
    http_client = mock_http_client_response(200, resp_body.encode("utf-8"))
    config = ContainerCredentialConfig()
    client = ContainerMetadataClient(http_client, config)

    # Valid HTTPS Host
    uri = URI(scheme="https", host="169.254.170.2")

    creds = await client.get_credentials(uri, Fields())
    _assert_expected_credentials(creds, "akid123", "s3cr3t", "session_token")


@pytest.mark.asyncio
async def test_metadata_client_invalid_host():
    resp_body = json.dumps(DEFAULT_RESPONSE_DATA)
    http_client = mock_http_client_response(200, resp_body.encode("utf-8"))
    config = ContainerCredentialConfig(retries=0)
    client = ContainerMetadataClient(http_client, config)

    # Invalid Host
    uri = URI(scheme="http", host="169.254.169.254")

    with pytest.raises(SmithyIdentityException):
        await client.get_credentials(uri, Fields())


@pytest.mark.asyncio
async def test_metadata_client_non_200_response():
    http_client = mock_http_client_response(404, b"not found")
    config = ContainerCredentialConfig(retries=1)
    client = ContainerMetadataClient(http_client, config)

    uri = URI(scheme="http", host="169.254.170.2")
    with pytest.raises(SmithyIdentityException) as e:
        await client.get_credentials(uri, Fields())

    # Ensure both the received retry error and underlying error are what we expect.
    assert "Container metadata service returned 404" in str(e.value.__cause__)
    assert "Failed to retrieve container metadata after 1 attempt(s)" in str(e.value)


@pytest.mark.asyncio
async def test_metadata_client_invalid_json():
    http_client = mock_http_client_response(
        200, b"<!DOCTYPE html><head><title>proxy</title>"
    )
    config = ContainerCredentialConfig(retries=1)
    client = ContainerMetadataClient(http_client, config)

    uri = URI(scheme="http", host="169.254.170.2")
    with pytest.raises(SmithyIdentityException):
        await client.get_credentials(uri, Fields())


def _assert_expected_identity(identity: AWSCredentialsIdentity) -> None:
    assert identity.access_key_id == DEFAULT_RESPONSE_DATA["AccessKeyId"]
    assert identity.secret_access_key == DEFAULT_RESPONSE_DATA["SecretAccessKey"]
    assert identity.session_token == DEFAULT_RESPONSE_DATA["Token"]


@pytest.mark.asyncio
async def test_metadata_client_retries():
    http_client = AsyncMock()
    config = ContainerCredentialConfig(retries=2)
    client = ContainerMetadataClient(http_client, config)
    uri = URI(scheme="http", host="169.254.170.2", path="/task")
    http_client.send.side_effect = Exception()

    with pytest.raises(SmithyIdentityException):
        await client.get_credentials(uri, Fields())
    assert http_client.send.call_count == 2


@pytest.mark.asyncio
async def test_resolver_env_relative():
    resp_body = json.dumps(DEFAULT_RESPONSE_DATA)
    http_client = mock_http_client_response(200, resp_body.encode("utf-8"))

    with patch.dict(os.environ, {ContainerCredentialResolver.ENV_VAR: "/test"}):
        resolver = ContainerCredentialResolver(http_client)
        identity = await resolver.get_identity(identity_properties={})

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
        {ContainerCredentialResolver.ENV_VAR_FULL: "http://169.254.170.23/full"},
    ):
        resolver = ContainerCredentialResolver(http_client)
        identity = await resolver.get_identity(identity_properties={})

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
            ContainerCredentialResolver.ENV_VAR_FULL: "http://169.254.170.23/full",
            ContainerCredentialResolver.ENV_VAR_AUTH_TOKEN: "Bearer foobar",
        },
    ):
        resolver = ContainerCredentialResolver(http_client)
        identity = await resolver.get_identity(identity_properties={})

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
            ContainerCredentialResolver.ENV_VAR_FULL: "http://169.254.170.23/full",
            ContainerCredentialResolver.ENV_VAR_AUTH_TOKEN_FILE: str(token_file),
        },
    ):
        resolver = ContainerCredentialResolver(http_client)
        identity = await resolver.get_identity(identity_properties={})

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
            ContainerCredentialResolver.ENV_VAR_FULL: "http://169.254.170.23/full",
            ContainerCredentialResolver.ENV_VAR_AUTH_TOKEN_FILE: str(token_file),
        },
    ):
        resolver = ContainerCredentialResolver(http_client)
        with pytest.raises(SmithyIdentityException) as e:
            await resolver.get_identity(identity_properties={})
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
            ContainerCredentialResolver.ENV_VAR_FULL: "http://169.254.170.23/full",
            ContainerCredentialResolver.ENV_VAR_AUTH_TOKEN_FILE: str(token_file),
            ContainerCredentialResolver.ENV_VAR_AUTH_TOKEN: "Bearer foobar",
        },
    ):
        resolver = ContainerCredentialResolver(http_client)
        identity = await resolver.get_identity(identity_properties={})

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
async def test_resolver_missing_env():
    resp_body = json.dumps(DEFAULT_RESPONSE_DATA)
    http_client = mock_http_client_response(200, resp_body.encode("utf-8"))

    with patch.dict(os.environ, {}):
        resolver = ContainerCredentialResolver(http_client)
        with pytest.raises(SmithyIdentityException):
            await resolver.get_identity(identity_properties={})
