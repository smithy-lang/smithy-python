#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pyright: reportPrivateUsage=false
import json
import time
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from smithy_aws_core.identity.imds import (
    Config,
    EC2Metadata,
    IMDSCredentialsResolver,
    Token,
    TokenCache,
)
from smithy_core import URI
from smithy_core.retries import SimpleRetryStrategy
from smithy_http.aio import HTTPRequest


def test_config_defaults():
    config = Config()
    assert isinstance(config.retry_strategy, SimpleRetryStrategy)
    assert config.endpoint_uri == URI(
        scheme="http", host=Config._HOST_MAPPING["IPv4"], port=80
    )
    assert config.endpoint_mode == "IPv4"
    assert config.token_ttl == 21600


def test_endpoint_resolution():
    config_ipv4 = Config(endpoint_mode="IPv4")
    config_ipv6 = Config(endpoint_mode="IPv6")
    assert config_ipv4.endpoint_uri.host == Config._HOST_MAPPING["IPv4"]
    assert config_ipv6.endpoint_uri.host == Config._HOST_MAPPING["IPv6"]


def test_config_uses_custom_endpoint():
    # The custom endpoint should take precedence over IPv4 endpoint resolution.
    config = Config(
        endpoint_uri=URI(scheme="https", host="test.host", port=123),
        endpoint_mode="IPv4",
    )
    assert config.endpoint_uri == URI(scheme="https", host="test.host", port=123)

    # The custom endpoint takes precedence over IPv6 endpoint resolution.
    config = Config(
        endpoint_uri=URI(scheme="https", host="test.host", port=123),
        endpoint_mode="IPv6",
    )
    assert config.endpoint_uri == URI(scheme="https", host="test.host", port=123)


def test_config_ttl_validation():
    # TTL values < _MIN_TTL should throw a ValueError
    with pytest.raises(ValueError):
        Config(token_ttl=Config._MIN_TTL - 1)
    # TTL values > _MAX_TTL should throw a ValueError
    with pytest.raises(ValueError):
        Config(token_ttl=Config._MAX_TTL + 1)


def test_token_creation():
    token = Token(value="test-token", ttl=100)
    assert token._value == "test-token"
    assert token._ttl == 100
    assert not token.is_expired()


def test_token_expiration():
    token = Token(value="test-token", ttl=1)
    assert not token.is_expired()
    time.sleep(1.1)
    assert token.is_expired()


async def test_token_cache_should_refresh():
    http_client = AsyncMock()
    config = MagicMock()
    # A new token cache needs a refresh
    token_cache = TokenCache(http_client, config)
    assert token_cache._should_refresh()
    # A token cache with an unexpired token doesn't need a refresh
    token_cache._token = MagicMock()
    token_cache._token.is_expired.return_value = False
    assert not token_cache._should_refresh()
    # A token cache with an expired token needs a refresh
    token_cache._token.is_expired.return_value = True
    assert token_cache._should_refresh()


async def test_token_cache_refresh():
    # Test that TokenCache correctly refreshes the token when needed
    http_client = AsyncMock()
    config = MagicMock()
    config.token_ttl = 100
    config.endpoint_uri.scheme = "http"
    config.endpoint_uri.host = "169.254.169.254"
    response_mock = AsyncMock()
    response_mock.consume_body_async.return_value = b"new-token-value"
    http_client.send.return_value = response_mock
    token_cache = TokenCache(http_client, config)
    assert token_cache._should_refresh()
    await token_cache._refresh()
    assert token_cache._token is not None
    assert token_cache._token.value == "new-token-value"
    assert token_cache._token._ttl == 100


async def test_token_cache_get_token():
    # Test that TokenCache correctly returns an existing token or refreshes if expired
    http_client = AsyncMock()
    config = MagicMock()
    token_cache = TokenCache(http_client, config)
    token_cache._refresh = AsyncMock()
    token_cache._token = MagicMock()
    token_cache._token.is_expired.return_value = False
    token = await token_cache.get_token()
    assert token == token_cache._token
    token_cache._refresh.assert_not_awaited()
    token_cache._token.is_expired.return_value = True
    await token_cache.get_token()
    token_cache._refresh.assert_awaited()


async def test_ec2_metadata_get():
    # Test EC2Metadata.get() method to retrieve metadata from IMDS
    http_client = AsyncMock()
    config = Config()
    response = AsyncMock()
    response.consume_body_async.return_value = b"metadata-response"
    http_client.send.return_value = response

    ec2_metadata = EC2Metadata(http_client, config)
    ec2_metadata._token_cache.get_token = AsyncMock(
        return_value=Token("mocked-token", config.token_ttl)
    )

    result = await ec2_metadata.get(path="/test-path")
    assert result == "metadata-response"

    request = http_client.send.call_args.kwargs["request"]
    assert isinstance(request, HTTPRequest)
    assert request.destination.path == "/test-path"
    assert request.method == "GET"
    assert request.fields["x-aws-ec2-metadata-token"].values == ["mocked-token"]


async def test_imds_credentials_resolver():
    # Test IMDSCredentialsResolver retrieving credentials
    http_client = AsyncMock()
    config = Config()
    ec2_metadata = AsyncMock()
    resolver = IMDSCredentialsResolver(http_client, config)
    resolver._ec2_metadata_client = ec2_metadata

    # Mock EC2Metadata client get responses
    ec2_metadata.get.side_effect = [
        "test-profile",
        json.dumps(
            {
                "AccessKeyId": "test-access-key",
                "SecretAccessKey": "test-secret-key",
                "Token": "test-session-token",
                "AccountId": "test-account",
                "Expiration": "2025-03-13T07:28:47Z",
            }
        ),
    ]

    credentials = await resolver.get_identity(properties={})
    assert credentials.access_key_id == "test-access-key"
    assert credentials.secret_access_key == "test-secret-key"
    assert credentials.session_token == "test-session-token"
    assert credentials.account_id == "test-account"
    assert credentials.expiration == datetime(2025, 3, 13, 7, 28, 47, tzinfo=UTC)
    ec2_metadata.get.assert_awaited()
