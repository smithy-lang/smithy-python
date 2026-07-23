# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Tests for the config resolution pipeline.

Tests AsyncAwsConfig.resolve(), resolver functions, SharedConfigContext,
provenance tracking, and precedence behavior.
"""

import os
from unittest.mock import patch

import pytest
from smithy_aws_core.config.aws_config import AsyncAwsConfig
from smithy_aws_core.config.context import SharedConfigContext
from smithy_aws_core.config.resolvers import (
    resolve_region,
    resolve_retry_config,
)
from smithy_aws_core.config.types import ConfigSource
from smithy_core.exceptions import ConfigError, ConfigValidationError


class NullFileSystem:
    async def read_file(self, path: str) -> str | None:
        return None


class FakeFileSystem:
    def __init__(self, files: dict[str, str]):
        self._files = files

    async def read_file(self, path: str) -> str | None:
        return self._files.get(path)


class TestResolveRegion:
    @pytest.mark.asyncio
    async def test_resolves_from_aws_region(self):
        with patch.dict(os.environ, {"AWS_REGION": "us-west-2"}, clear=True):
            ctx = SharedConfigContext()
            result = await resolve_region(ctx)
            assert result.value == "us-west-2"
            assert result.source == ConfigSource.ENV

    @pytest.mark.asyncio
    async def test_resolves_from_aws_default_region(self):
        with patch.dict(os.environ, {"AWS_DEFAULT_REGION": "eu-central-1"}, clear=True):
            ctx = SharedConfigContext()
            result = await resolve_region(ctx)
            assert result.value == "eu-central-1"
            assert result.source == ConfigSource.ENV

    @pytest.mark.asyncio
    async def test_aws_region_takes_precedence_over_default_region(self):
        with patch.dict(
            os.environ,
            {"AWS_REGION": "us-west-2", "AWS_DEFAULT_REGION": "eu-west-1"},
            clear=True,
        ):
            ctx = SharedConfigContext()
            result = await resolve_region(ctx)
            assert result.value == "us-west-2"

    @pytest.mark.asyncio
    async def test_resolves_from_profile_when_no_env(self):
        fs = FakeFileSystem(
            {"/fake/config": "[profile default]\nregion = ap-southeast-1\n"}
        )
        with patch.dict(os.environ, {}, clear=True):
            ctx = SharedConfigContext(
                fs=fs,
                config_file_path="/fake/config",
                credentials_file_path="/fake/credentials",
            )
            result = await resolve_region(ctx)
            assert result.value == "ap-southeast-1"
            assert result.source == ConfigSource.PROFILE

    @pytest.mark.asyncio
    async def test_env_takes_precedence_over_profile(self):
        fs = FakeFileSystem({"/fake/config": "[profile default]\nregion = eu-west-1\n"})
        with patch.dict(os.environ, {"AWS_REGION": "us-west-2"}, clear=True):
            ctx = SharedConfigContext(
                fs=fs,
                config_file_path="/fake/config",
                credentials_file_path="/fake/credentials",
            )
            result = await resolve_region(ctx)
            assert result.value == "us-west-2"
            assert result.source == ConfigSource.ENV

    @pytest.mark.asyncio
    async def test_empty_string_env_var_treated_as_absent(self):
        fs = FakeFileSystem({"/fake/config": "[profile default]\nregion = eu-west-1\n"})
        with patch.dict(os.environ, {"AWS_REGION": ""}, clear=True):
            ctx = SharedConfigContext(
                fs=fs,
                config_file_path="/fake/config",
                credentials_file_path="/fake/credentials",
            )
            result = await resolve_region(ctx)
            assert result.value == "eu-west-1"
            assert result.source == ConfigSource.PROFILE


class TestResolveRetryConfig:
    @pytest.mark.asyncio
    async def test_resolves_both_from_env(self):
        with patch.dict(
            os.environ,
            {"AWS_RETRY_MODE": "standard", "AWS_MAX_ATTEMPTS": "10"},
            clear=True,
        ):
            ctx = SharedConfigContext()
            result = await resolve_retry_config(ctx)
            assert result.value.retry_mode == "standard"
            assert result.value.max_attempts == 10
            assert result.source == ConfigSource.ENV

    @pytest.mark.asyncio
    async def test_uses_defaults_when_nothing_found(self):
        with patch.dict(os.environ, {}, clear=True):
            ctx = SharedConfigContext(fs=NullFileSystem())
            result = await resolve_retry_config(ctx)
            assert result.value.retry_mode == "standard"
            assert result.value.max_attempts is None
            assert result.source == ConfigSource.DEFAULT

    @pytest.mark.asyncio
    async def test_partial_resolution_uses_defaults_for_missing(self):
        with patch.dict(os.environ, {"AWS_RETRY_MODE": "standard"}, clear=True):
            ctx = SharedConfigContext(fs=NullFileSystem())
            result = await resolve_retry_config(ctx)
            assert result.value.retry_mode == "standard"
            assert result.value.max_attempts is None
            assert result.source == ConfigSource.ENV

    @pytest.mark.asyncio
    async def test_max_attempts_cast_to_int(self):
        with patch.dict(
            os.environ,
            {"AWS_RETRY_MODE": "standard", "AWS_MAX_ATTEMPTS": "5"},
            clear=True,
        ):
            ctx = SharedConfigContext()
            result = await resolve_retry_config(ctx)
            assert result.value.max_attempts == 5
            assert isinstance(result.value.max_attempts, int)

    @pytest.mark.asyncio
    async def test_max_attempts_unset_when_not_found(self):
        with patch.dict(os.environ, {}, clear=True):
            ctx = SharedConfigContext(fs=NullFileSystem())
            result = await resolve_retry_config(ctx)
            assert result.value.max_attempts is None

    @pytest.mark.asyncio
    async def test_invalid_max_attempts_raises_config_error(self):
        with patch.dict(os.environ, {"AWS_MAX_ATTEMPTS": "abc"}, clear=True):
            ctx = SharedConfigContext(fs=NullFileSystem())
            with pytest.raises(ConfigValidationError, match="Invalid integer value"):
                await resolve_retry_config(ctx)


class TestAsyncAwsConfigResolve:
    @pytest.mark.asyncio
    async def test_resolves_region_from_env(self):
        with patch.dict(os.environ, {"AWS_REGION": "us-west-2"}, clear=True):
            config = await AsyncAwsConfig.resolve(fs=NullFileSystem())
            assert config.region == "us-west-2"

    @pytest.mark.asyncio
    async def test_resolves_retry_from_env(self):
        with patch.dict(
            os.environ,
            {
                "AWS_RETRY_MODE": "standard",
                "AWS_MAX_ATTEMPTS": "5",
                "AWS_REGION": "us-east-1",
            },
            clear=True,
        ):
            config = await AsyncAwsConfig.resolve(fs=NullFileSystem())
            assert config.retry_strategy_options is not None
            assert config.retry_strategy_options.retry_mode == "standard"
            assert config.retry_strategy_options.max_attempts == 5

    @pytest.mark.asyncio
    async def test_explicit_override_takes_precedence(self):
        with patch.dict(os.environ, {"AWS_REGION": "us-west-2"}, clear=True):
            config = await AsyncAwsConfig.resolve(
                region="eu-west-1", fs=NullFileSystem()
            )
            assert config.region == "eu-west-1"

    @pytest.mark.asyncio
    async def test_default_region_raises_error(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ConfigValidationError, match="Region is required"):
                await AsyncAwsConfig.resolve(fs=NullFileSystem())

    @pytest.mark.asyncio
    async def test_default_retry_strategy(self):
        with patch.dict(os.environ, {"AWS_REGION": "us-east-1"}, clear=True):
            config = await AsyncAwsConfig.resolve(fs=NullFileSystem())
            assert config.retry_strategy_options is not None
            assert config.retry_strategy_options.retry_mode == "standard"
            assert config.retry_strategy_options.max_attempts is None

    @pytest.mark.asyncio
    async def test_resolves_region_from_non_default_profile(self):
        fs = FakeFileSystem(
            {
                "/fake/config": "[profile default]\nregion = us-east-1\n"
                "[profile work]\nregion = eu-west-1\n"
            }
        )
        with patch.dict(os.environ, {}, clear=True):
            config = await AsyncAwsConfig.resolve(
                profile="work",
                fs=fs,
                config_file_path="/fake/config",
                credentials_file_path="/fake/credentials",
            )
            assert config.region == "eu-west-1"
            assert config.source_of("region") == ConfigSource.PROFILE

    @pytest.mark.asyncio
    async def test_invalid_override_triggers_validator(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(
                ConfigValidationError, match="Must be a valid AWS region"
            ):
                await AsyncAwsConfig.resolve(region="bad-value!")


class TestProvenanceTracking:
    @pytest.mark.asyncio
    async def test_source_of_env_resolved_field(self):
        with patch.dict(os.environ, {"AWS_REGION": "us-west-2"}, clear=True):
            config = await AsyncAwsConfig.resolve(fs=NullFileSystem())
            assert config.source_of("region") == ConfigSource.ENV

    @pytest.mark.asyncio
    async def test_source_of_profile_resolved_field(self):
        fs = FakeFileSystem({"/fake/config": "[profile default]\nregion = eu-west-1\n"})
        with patch.dict(os.environ, {}, clear=True):
            config = await AsyncAwsConfig.resolve(
                fs=fs,
                config_file_path="/fake/config",
                credentials_file_path="/fake/credentials",
            )
            assert config.source_of("region") == ConfigSource.PROFILE

    @pytest.mark.asyncio
    async def test_source_of_default_field(self):
        with patch.dict(os.environ, {"AWS_REGION": "us-east-1"}, clear=True):
            config = await AsyncAwsConfig.resolve(fs=NullFileSystem())
            assert config.source_of("retry_strategy_options") == ConfigSource.DEFAULT

    @pytest.mark.asyncio
    async def test_source_of_override_field(self):
        with patch.dict(os.environ, {}, clear=True):
            config = await AsyncAwsConfig.resolve(
                region="us-east-1", fs=NullFileSystem()
            )
            assert config.source_of("region") == ConfigSource.OVERRIDE

    @pytest.mark.asyncio
    async def test_post_resolution_assignment_marks_source_as_override(self):
        with patch.dict(os.environ, {"AWS_REGION": "us-west-2"}, clear=True):
            config = await AsyncAwsConfig.resolve(fs=NullFileSystem())
            assert config.source_of("region") == ConfigSource.ENV
            config.region = "eu-west-1"
            assert config.source_of("region") == ConfigSource.OVERRIDE
            assert config.region == "eu-west-1"


class TestConstructionBlocking:
    def test_direct_instantiation_raises_error(self):
        with pytest.raises(ConfigError, match="cannot be constructed directly"):
            AsyncAwsConfig()

    @pytest.mark.asyncio
    async def test_unknown_override_field_raises_error(self):
        with patch.dict(os.environ, {"AWS_REGION": "us-east-1"}, clear=True):
            with pytest.raises(ConfigValidationError, match="Unknown config field"):
                await AsyncAwsConfig.resolve(reigon="us-west-2")

    @pytest.mark.parametrize(
        "field_name,invalid_value,match",
        [
            ("region", "bad-value!", "Must be a valid AWS region"),
            ("region", None, "Region is required"),
            (
                "retry_strategy_options",
                "not-a-strategy",
                "Must be RetryStrategyOptions",
            ),
        ],
    )
    @pytest.mark.asyncio
    async def test_setattr_validates_during_override(
        self,
        field_name: str,
        invalid_value: str | None,
        match: str,
    ):
        with patch.dict(os.environ, {"AWS_REGION": "us-east-1"}, clear=True):
            config = await AsyncAwsConfig.resolve(fs=NullFileSystem())
            with pytest.raises(ConfigValidationError, match=match):
                setattr(config, field_name, invalid_value)


class TestSharedConfigContext:
    def test_default_profile_is_default(self):
        with patch.dict(os.environ, {}, clear=True):
            ctx = SharedConfigContext()
            assert ctx.profile_name == "default"

    def test_profile_from_aws_profile_env(self):
        with patch.dict(os.environ, {"AWS_PROFILE": "work"}, clear=True):
            ctx = SharedConfigContext()
            assert ctx.profile_name == "work"

    def test_explicit_profile_overrides_env(self):
        with patch.dict(os.environ, {"AWS_PROFILE": "work"}, clear=True):
            ctx = SharedConfigContext(profile_name="custom")
            assert ctx.profile_name == "custom"

    @pytest.mark.asyncio
    async def test_parsed_profiles_caches_result(self):
        fs = FakeFileSystem({"/fake/config": "[profile default]\nregion = us-east-1\n"})
        with patch.dict(os.environ, {}, clear=True):
            ctx = SharedConfigContext(
                fs=fs,
                config_file_path="/fake/config",
                credentials_file_path="/fake/credentials",
            )
            result1 = await ctx.parsed_profiles()
            result2 = await ctx.parsed_profiles()
            assert result1 is result2
