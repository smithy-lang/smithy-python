# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Tests for the config resolution pipeline.

Tests AsyncAwsConfig.resolve(), resolver functions, SharedConfigContext,
provenance tracking, and precedence behavior.
"""

from pathlib import Path

import pytest
from smithy_aws_core.config.aws_config import AsyncAwsConfig
from smithy_aws_core.config.context import SharedConfigContext
from smithy_aws_core.config.exceptions import ConfigError
from smithy_aws_core.config.resolvers import (
    resolve_region,
    resolve_retry_config,
)
from smithy_aws_core.config.types import ConfigSource


class TestResolveRegion:
    @pytest.mark.asyncio
    async def test_resolves_from_aws_region(self):
        ctx = SharedConfigContext(env={"AWS_REGION": "us-west-2"})
        result = await resolve_region(ctx)
        assert result.value == "us-west-2"
        assert result.source == ConfigSource.ENV

    @pytest.mark.asyncio
    async def test_resolves_from_aws_default_region(self):
        ctx = SharedConfigContext(env={"AWS_DEFAULT_REGION": "eu-central-1"})
        result = await resolve_region(ctx)
        assert result.value == "eu-central-1"
        assert result.source == ConfigSource.ENV

    @pytest.mark.asyncio
    async def test_aws_region_takes_precedence_over_default_region(self):
        ctx = SharedConfigContext(
            env={"AWS_REGION": "us-west-2", "AWS_DEFAULT_REGION": "eu-west-1"},
        )
        result = await resolve_region(ctx)
        assert result.value == "us-west-2"

    @pytest.mark.asyncio
    async def test_resolves_from_profile_when_no_env(self, tmp_path: Path):
        config_file = tmp_path / "config"
        config_file.write_text("[profile default]\nregion = ap-southeast-1\n")

        ctx = SharedConfigContext(
            env={},
            config_file_path=str(config_file),
            credentials_file_path=str(tmp_path / "none"),
        )
        result = await resolve_region(ctx)
        assert result.value == "ap-southeast-1"
        assert result.source == ConfigSource.PROFILE

    @pytest.mark.asyncio
    async def test_env_takes_precedence_over_profile(self, tmp_path: Path):
        config_file = tmp_path / "config"
        config_file.write_text("[profile default]\nregion = eu-west-1\n")
        ctx = SharedConfigContext(
            env={"AWS_REGION": "us-west-2"},
            config_file_path=str(config_file),
            credentials_file_path=str(tmp_path / "nonexistent"),
        )
        result = await resolve_region(ctx)
        assert result.value == "us-west-2"
        assert result.source == ConfigSource.ENV

    @pytest.mark.asyncio
    async def test_empty_string_env_var_treated_as_absent(self, tmp_path: Path):
        config_file = tmp_path / "config"
        config_file.write_text("[profile default]\nregion = eu-west-1\n")
        ctx = SharedConfigContext(
            env={"AWS_REGION": ""},
            config_file_path=str(config_file),
            credentials_file_path=str(tmp_path / "nonexistent"),
        )
        result = await resolve_region(ctx)
        assert result.value == "eu-west-1"
        assert result.source == ConfigSource.PROFILE


class TestResolveRetryConfig:
    @pytest.mark.asyncio
    async def test_resolves_both_from_env(self):
        ctx = SharedConfigContext(
            env={"AWS_RETRY_MODE": "standard", "AWS_MAX_ATTEMPTS": "10"},
        )
        result = await resolve_retry_config(ctx)
        assert result.value.retry_mode == "standard"
        assert result.value.max_attempts == 10
        assert result.source == ConfigSource.ENV

    @pytest.mark.asyncio
    async def test_uses_defaults_when_nothing_found(self):
        ctx = SharedConfigContext(env={})
        result = await resolve_retry_config(ctx)
        assert result.value.retry_mode == "standard"
        assert result.value.max_attempts is None
        assert result.source == ConfigSource.DEFAULT

    @pytest.mark.asyncio
    async def test_partial_resolution_uses_defaults_for_missing(self):
        ctx = SharedConfigContext(env={"AWS_RETRY_MODE": "standard"})
        result = await resolve_retry_config(ctx)
        assert result.value.retry_mode == "standard"
        assert result.value.max_attempts is None  # RetryStrategyOptions default
        assert result.source == ConfigSource.ENV  # strongest source

    @pytest.mark.asyncio
    async def test_max_attempts_cast_to_int(self):
        ctx = SharedConfigContext(
            env={"AWS_RETRY_MODE": "standard", "AWS_MAX_ATTEMPTS": "5"}
        )
        result = await resolve_retry_config(ctx)
        assert result.value.max_attempts == 5
        assert isinstance(result.value.max_attempts, int)

    @pytest.mark.asyncio
    async def test_max_attempts_unset_when_not_found(self):
        ctx = SharedConfigContext(env={})
        result = await resolve_retry_config(ctx)
        assert result.value.max_attempts is None

    @pytest.mark.asyncio
    async def test_invalid_max_attempts_raises_config_error(self):
        ctx = SharedConfigContext(env={"AWS_MAX_ATTEMPTS": "abc"})
        with pytest.raises(ConfigError, match="Invalid integer value"):
            await resolve_retry_config(ctx)


class TestAsyncAwsConfigResolve:
    @pytest.mark.asyncio
    async def test_resolves_region_from_env(self):
        config = await AsyncAwsConfig.resolve(env={"AWS_REGION": "us-west-2"})
        assert config.region == "us-west-2"

    @pytest.mark.asyncio
    async def test_resolves_retry_from_env(self):
        config = await AsyncAwsConfig.resolve(
            env={"AWS_RETRY_MODE": "standard", "AWS_MAX_ATTEMPTS": "5"},
        )
        assert config.retry_strategy_options is not None
        assert config.retry_strategy_options.retry_mode == "standard"
        assert config.retry_strategy_options.max_attempts == 5

    @pytest.mark.asyncio
    async def test_explicit_override_takes_precedence(self):
        config = await AsyncAwsConfig.resolve(
            env={"AWS_REGION": "us-west-2"},
            region="eu-west-1",
        )
        assert config.region == "eu-west-1"

    @pytest.mark.asyncio
    async def test_default_region_raises_error(self, tmp_path: Path):
        with pytest.raises(ConfigError, match="Region is required"):
            await AsyncAwsConfig.resolve(
                env={},
                config_file_path=str(tmp_path / "no_config"),
                credentials_file_path=str(tmp_path / "no_creds"),
            )

    @pytest.mark.asyncio
    async def test_default_retry_strategy(self, tmp_path: Path):
        config = await AsyncAwsConfig.resolve(
            env={"AWS_REGION": "us-east-1"},
            config_file_path=str(tmp_path / "no_config"),
            credentials_file_path=str(tmp_path / "no_creds"),
        )
        assert config.retry_strategy_options is not None
        assert config.retry_strategy_options.retry_mode == "standard"
        assert config.retry_strategy_options.max_attempts is None

    @pytest.mark.asyncio
    async def test_resolves_region_from_non_default_profile(self, tmp_path: Path):
        config_file = tmp_path / "config"
        config_file.write_text(
            "[profile default]\nregion = us-east-1\n"
            "[profile work]\nregion = eu-west-1\n"
        )

        config = await AsyncAwsConfig.resolve(
            profile="work",
            env={},
            config_file_path=str(config_file),
            credentials_file_path=str(tmp_path / "none"),
        )
        assert config.region == "eu-west-1"
        assert config.source_of("region") == ConfigSource.PROFILE

    @pytest.mark.asyncio
    async def test_invalid_override_triggers_validator(self):
        with pytest.raises(ConfigError, match="Must be a valid AWS region"):
            await AsyncAwsConfig.resolve(
                env={},
                region="bad-value!",
            )


class TestProvenanceTracking:
    @pytest.mark.asyncio
    async def test_source_of_env_resolved_field(self):
        config = await AsyncAwsConfig.resolve(env={"AWS_REGION": "us-west-2"})
        assert config.source_of("region") == ConfigSource.ENV

    @pytest.mark.asyncio
    async def test_source_of_profile_resolved_field(self, tmp_path: Path):
        config_file = tmp_path / "config"
        config_file.write_text("[profile default]\nregion = eu-west-1\n")

        config = await AsyncAwsConfig.resolve(
            env={},
            config_file_path=str(config_file),
            credentials_file_path=str(tmp_path / "none"),
        )
        assert config.source_of("region") == ConfigSource.PROFILE

    @pytest.mark.asyncio
    async def test_source_of_default_field(self, tmp_path: Path):
        config = await AsyncAwsConfig.resolve(
            env={"AWS_REGION": "us-east-1"},
            config_file_path=str(tmp_path / "no_config"),
            credentials_file_path=str(tmp_path / "no_creds"),
        )
        assert config.source_of("retry_strategy_options") == ConfigSource.DEFAULT

    @pytest.mark.asyncio
    async def test_source_of_override_field(self):
        config = await AsyncAwsConfig.resolve(env={}, region="us-east-1")
        assert config.source_of("region") == ConfigSource.OVERRIDE

    @pytest.mark.asyncio
    async def test_post_resolution_assignment_marks_source_as_override(self):
        config = await AsyncAwsConfig.resolve(env={"AWS_REGION": "us-west-2"})
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
        with pytest.raises(ConfigError, match="Unknown config field"):
            await AsyncAwsConfig.resolve(
                env={"AWS_REGION": "us-east-1"},
                reigon="us-west-2",
            )


class TestSharedConfigContext:
    def test_default_profile_is_default(self):
        ctx = SharedConfigContext(env={})
        assert ctx.profile_name == "default"

    def test_profile_from_aws_profile_env(self):
        ctx = SharedConfigContext(env={"AWS_PROFILE": "work"})
        assert ctx.profile_name == "work"

    def test_explicit_profile_overrides_env(self):
        ctx = SharedConfigContext(profile_name="custom", env={"AWS_PROFILE": "work"})
        assert ctx.profile_name == "custom"

    @pytest.mark.asyncio
    async def test_parsed_profiles_caches_result(self, tmp_path: Path):
        config_file = tmp_path / "config"
        config_file.write_text("[profile default]\nregion = us-east-1\n")

        ctx = SharedConfigContext(
            env={},
            config_file_path=str(config_file),
            credentials_file_path=str(tmp_path / "none"),
        )

        result1 = await ctx.parsed_profiles()
        result2 = await ctx.parsed_profiles()
        assert result1 is result2
