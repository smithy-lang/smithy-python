#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import os
from collections.abc import Awaitable, Callable
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from smithy_aws_core.config.config import (
    SOURCE_CONFIG_FILE,
    SOURCE_CONSTRUCTOR,
    SOURCE_CREDENTIALS_FILE,
    SOURCE_DEFAULT,
    SOURCE_ENVIRONMENT,
    SOURCE_IN_CODE_UPDATE,
    AWSClientConfig,
)


@pytest.fixture
async def empty_loaders() -> dict[str, Callable[[], Awaitable[dict[str, Any]]]]:
    """Fixture providing empty loaders for testing defaults"""

    async def empty_env_loader() -> dict[str, Any]:
        return {}

    async def empty_config_loader() -> dict[str, Any]:
        return {}

    async def empty_credentials_loader() -> dict[str, Any]:
        return {}

    return {
        "environment_loader": empty_env_loader,
        "config_file_loader": empty_config_loader,
        "credentials_file_loader": empty_credentials_loader,
    }


class TestAWSClientConfig:
    @pytest.mark.asyncio
    async def test_basic_resolve(self):
        config = AWSClientConfig(region="us-east-1")
        await config.resolve()
        assert config.region == "us-east-1"
        assert config.get_config_value_object("region").source == SOURCE_CONSTRUCTOR

    @pytest.mark.asyncio
    async def test_resolve_with_defaults(
        self, empty_loaders: dict[str, Callable[[], Awaitable[dict[str, Any]]]]
    ):
        config = AWSClientConfig()
        await config.resolve(**empty_loaders)
        assert config.region is None

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "field_name,env_var,value",
        [
            ("aws_access_key_id", "AWS_ACCESS_KEY_ID", "AKIATEST"),
            ("aws_secret_access_key", "AWS_SECRET_ACCESS_KEY", "secret123"),
            ("aws_session_token", "AWS_SESSION_TOKEN", "token456"),
            ("region", "AWS_REGION", "us-west-2"),
            ("endpoint_uri", "AWS_ENDPOINT_URL", "https://example.com"),
        ],
    )
    async def test_environment_precedence(
        self, field_name: str, env_var: str, value: str
    ):
        with patch.dict(os.environ, {env_var: value}, clear=False):
            config = AWSClientConfig()
            await config.resolve()
            assert getattr(config, field_name) == value
            assert (
                config.get_config_value_object(field_name).source == SOURCE_ENVIRONMENT
            )

    @pytest.mark.asyncio
    async def test_config_file_precedence(self):
        async def mock_config_loader():
            return {"region": "us-central-1", "aws_access_key_id": "AKIACONFIG"}

        config = AWSClientConfig()
        await config.resolve(config_file_loader=mock_config_loader)
        assert config.region == "us-central-1"
        assert config.aws_access_key_id == "AKIACONFIG"
        assert config.get_config_value_object("region").source == SOURCE_CONFIG_FILE

    @pytest.mark.asyncio
    async def test_credentials_file_precedence(self):
        async def mock_credentials_loader():
            return {
                "aws_access_key_id": "AKIACREDS",
                "aws_secret_access_key": "credsecret",
            }

        config = AWSClientConfig()
        await config.resolve(credentials_file_loader=mock_credentials_loader)
        assert config.aws_access_key_id == "AKIACREDS"
        assert config.aws_secret_access_key == "credsecret"
        assert (
            config.get_config_value_object("aws_access_key_id").source
            == SOURCE_CREDENTIALS_FILE
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "constructor_value,env_value,config_value,creds_value,expected_value,expected_source",
        [
            (
                "CONSTRUCTOR",
                "ENV",
                "CONFIG",
                "CREDS",
                "CONSTRUCTOR",
                SOURCE_CONSTRUCTOR,
            ),
            (None, "ENV", "CONFIG", "CREDS", "ENV", SOURCE_ENVIRONMENT),
            (None, None, "CONFIG", "CREDS", "CONFIG", SOURCE_CONFIG_FILE),
            (None, None, None, "CREDS", "CREDS", SOURCE_CREDENTIALS_FILE),
            (None, None, None, None, None, SOURCE_DEFAULT),
        ],
    )
    async def test_precedence_chain(
        self,
        constructor_value: str | None,
        env_value: str | None,
        config_value: str | None,
        creds_value: str | None,
        expected_value: str | None,
        expected_source: str,
    ):
        """Test precedence: constructor > env > config > credentials > default"""

        async def env_loader():
            return {"AWS_REGION": env_value} if env_value else {}

        async def config_loader():
            return {"region": config_value} if config_value else {}

        async def creds_loader():
            return {"region": creds_value} if creds_value else {}

        kwargs = {
            "environment_loader": env_loader,
            "config_file_loader": config_loader,
            "credentials_file_loader": creds_loader,
        }

        config_kwargs: dict[str, Any] = {}
        if constructor_value:
            config_kwargs["region"] = constructor_value

        config = AWSClientConfig(**config_kwargs)
        await config.resolve(**kwargs)
        assert config.region == expected_value
        assert config.get_config_value_object("region").source == expected_source

    @pytest.mark.asyncio
    async def test_custom_loaders(self):
        async def custom_env_loader():
            return {"AWS_REGION": "custom-env"}

        async def custom_config_loader():
            return {"region": "custom-config"}

        config = AWSClientConfig()
        await config.resolve(
            environment_loader=custom_env_loader,
            config_file_loader=custom_config_loader,
        )
        assert config.region == "custom-env"

    @pytest.mark.asyncio
    async def test_multiple_resolve_calls_raise_error(
        self, empty_loaders: dict[str, Callable[[], Awaitable[dict[str, Any]]]]
    ):
        config = AWSClientConfig(region="us-west-2")

        await config.resolve(**empty_loaders)
        assert config.region == "us-west-2"

        with pytest.raises(RuntimeError, match="Config has already been resolved"):
            await config.resolve(**empty_loaders)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "field_name,invalid_value,expected_error",
        [
            ("aws_access_key_id", 123, "must be str \\| None, got int"),
            ("region", 456, "must be str \\| None, got int"),
            ("endpoint_uri", 123, "must be a string or URI"),
        ],
    )
    async def test_validation_errors(
        self, field_name: str, invalid_value: Any, expected_error: str
    ):
        kwargs: dict[str, Any] = {field_name: invalid_value}
        config = AWSClientConfig(**kwargs)
        with pytest.raises(TypeError, match=expected_error):
            await config.resolve()

    @pytest.mark.asyncio
    async def test_endpoint_uri_valid_string(self):
        config = AWSClientConfig(endpoint_uri="https://example.com")
        await config.resolve()
        assert config.endpoint_uri == "https://example.com"

    def test_unresolved_config_errors(self):
        config = AWSClientConfig()

        with pytest.raises(
            RuntimeError, match="Config must be resolved before accessing values"
        ):
            config.get_config_value_object("region")

    @pytest.mark.asyncio
    async def test_property_setters(self):
        config = AWSClientConfig(region="us-east-1")
        await config.resolve()

        config.region = "us-west-2"
        assert config.region == "us-west-2"
        assert config.get_config_value_object("region").source == SOURCE_IN_CODE_UPDATE

    @pytest.mark.asyncio
    async def test_custom_resolver_aws_credentials_identity_resolver(self):
        mock_resolver = AsyncMock()
        config = AWSClientConfig(aws_credentials_identity_resolver=mock_resolver)
        await config.resolve()

        assert config.aws_credentials_identity_resolver is mock_resolver
        assert (
            config.get_config_value_object("aws_credentials_identity_resolver").source
            == SOURCE_CONSTRUCTOR
        )

    @pytest.mark.asyncio
    async def test_custom_resolver_aws_credentials_fallback_to_default(
        self, empty_loaders: dict[str, Callable[[], Awaitable[dict[str, Any]]]]
    ):
        config = AWSClientConfig()
        await config.resolve(**empty_loaders)
        assert config.aws_credentials_identity_resolver is None
        assert (
            config.get_config_value_object("aws_credentials_identity_resolver").source
            == SOURCE_DEFAULT
        )

    def test_config_fields_no_none_values(self):
        for field_name, field_info in AWSClientConfig.CONFIG_FIELDS.items():
            for key in ["validator", "env_var", "config_key"]:
                if key in field_info:
                    assert field_info[key] is not None, (
                        f"Field {field_name} has {key} set to None - it should be omitted entirely"
                    )

    def test_config_fields_env_var_and_config_key_valid(self):
        for field_name, field_info in AWSClientConfig.CONFIG_FIELDS.items():
            if "env_var" in field_info:
                env_var = field_info["env_var"]
                assert isinstance(env_var, str) and len(env_var) > 0, (
                    f"Field {field_name} has invalid env_var: {env_var!r} - should be non-empty string or omitted entirely"
                )

            if "config_key" in field_info:
                config_key = field_info["config_key"]
                assert isinstance(config_key, str) and len(config_key) > 0, (
                    f"Field {field_name} has invalid config_key: {config_key!r} - should be non-empty string or omitted entirely"
                )

    @pytest.mark.asyncio
    async def test_config_file_loader_with_profile(self):
        async def mock_config_loader():
            return {"region": "test-region"}

        with patch.dict(os.environ, {"AWS_PROFILE": "test"}, clear=False):
            config = AWSClientConfig()
            await config.resolve(config_file_loader=mock_config_loader)
            assert config.region == "test-region"

    @pytest.mark.asyncio
    async def test_all_properties_accessible(
        self, empty_loaders: dict[str, Callable[[], Awaitable[dict[str, Any]]]]
    ):
        """Test that all CONFIG_FIELDS have working property accessors"""
        config = AWSClientConfig()
        await config.resolve(**empty_loaders)

        for field_name in AWSClientConfig.CONFIG_FIELDS:
            value = getattr(config, field_name)
            setattr(config, field_name, value)
            assert getattr(config, field_name) == value

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "field_name,valid_value",
        [
            ("region", "us-east-1"),
            ("region", None),
            ("aws_access_key_id", "AKIATEST"),
            ("aws_access_key_id", None),
            ("aws_secret_access_key", "secret"),
            ("aws_session_token", "token"),
            ("endpoint_uri", "https://example.com"),
            ("sdk_ua_app_id", "my-app"),
            ("user_agent_extra", "extra"),
        ],
    )
    async def test_type_validation_success(self, field_name: str, valid_value: Any):
        """Test that valid values pass type validation"""
        kwargs = {field_name: valid_value}
        config = AWSClientConfig(**kwargs)
        await config.resolve()
        assert getattr(config, field_name) == valid_value

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "field_name,invalid_value,expected_error",
        [
            ("region", 123, "must be str \\| None, got int"),
            ("aws_access_key_id", 456, "must be str \\| None, got int"),
            ("aws_secret_access_key", True, "must be str \\| None, got bool"),
            ("aws_session_token", [], "must be str \\| None, got list"),
            ("endpoint_uri", 789, "must be a string or URI"),
            ("sdk_ua_app_id", {}, "must be str \\| None, got dict"),
            ("user_agent_extra", 3.14, "must be str \\| None, got float"),
        ],
    )
    async def test_type_validation_errors(
        self, field_name: str, invalid_value: Any, expected_error: str
    ):
        kwargs = {field_name: invalid_value}
        config = AWSClientConfig(**kwargs)
        with pytest.raises(TypeError, match=expected_error):
            await config.resolve()
