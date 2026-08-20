# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Tests for the config resolution pipeline.

Tests AsyncAwsConfig.resolve(), resolver functions, SharedConfigContext,
provenance tracking, and precedence behavior.
"""

import os
from copy import deepcopy
from dataclasses import dataclass
from inspect import signature
from unittest.mock import patch

import pytest
from smithy_aws_core.config.aws_config import AsyncAwsConfig, AwsConfigOverrides
from smithy_aws_core.config.context import SharedConfigContext
from smithy_aws_core.config.exceptions import (
    ConfigError,
    ConfigValidationError,
    ProfileNotFoundError,
)
from smithy_aws_core.config.resolvers import (
    EndpointUriResolver,
    resolve_endpoint_uri,
    resolve_max_attempts,
    resolve_region,
    resolve_retry_mode,
    resolve_sdk_ua_app_id,
)
from smithy_aws_core.config.types import UNSET, ConfigSource
from smithy_aws_core.identity.environment import EnvironmentCredentialsResolver
from smithy_aws_core.identity.static import StaticCredentialsResolver
from smithy_core.aio.retries import StandardRetryStrategy
from smithy_http.interfaces import HTTPRequestConfiguration
from smithy_http.testing import MockHTTPClient


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
            assert config.region == "us-east-1"
            assert config.retry_mode == "standard"
            assert config.max_attempts == 5

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
            assert config.region == "us-east-1"
            assert config.retry_mode == "standard"
            assert config.max_attempts is None

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
                await AsyncAwsConfig.resolve(region="bad-value!", fs=NullFileSystem())

    @pytest.mark.asyncio
    async def test_invalid_profile_raises_error(self):
        with patch.dict(os.environ, {"AWS_REGION": "us-east-1"}, clear=True):
            with pytest.raises(
                ProfileNotFoundError,
                match="Profile 'FOOBAR' from profile argument was not found in config file",
            ):
                await AsyncAwsConfig.resolve(
                    profile="FOOBAR",
                    fs=NullFileSystem(),
                )

    @pytest.mark.asyncio
    async def test_invalid_profile_set_via_env_var_raises_error(self):
        with patch.dict(
            os.environ,
            {"AWS_REGION": "us-east-1", "AWS_PROFILE": "FOOBAR"},
            clear=True,
        ):
            with pytest.raises(
                ProfileNotFoundError,
                match="Profile 'FOOBAR' from AWS_PROFILE environment variable was not found in config file",
            ):
                await AsyncAwsConfig.resolve(
                    fs=NullFileSystem(),
                )

    @pytest.mark.asyncio
    async def test_unknown_profile_raises_when_config_file_has_others(self):
        fs = FakeFileSystem({"/fake/config": "[profile work]\nregion = eu-west-1\n"})
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(
                ProfileNotFoundError,
                match="Profile 'other' from profile argument was not found in config file",
            ):
                await AsyncAwsConfig.resolve(
                    profile="other",
                    fs=fs,
                    config_file_path="/fake/config",
                    credentials_file_path="/fake/credentials",
                )

    @pytest.mark.asyncio
    async def test_invalid_aws_profile_env_raises_profile_error(self):
        fs = FakeFileSystem({"/fake/config": "[profile work]\nregion = eu-west-1\n"})
        with patch.dict(os.environ, {"AWS_PROFILE": "wrok"}, clear=True):
            with pytest.raises(
                ProfileNotFoundError,
                match="Profile 'wrok' from AWS_PROFILE environment variable was not found in config file",
            ):
                await AsyncAwsConfig.resolve(
                    fs=fs,
                    config_file_path="/fake/config",
                    credentials_file_path="/fake/credentials",
                )

    @pytest.mark.asyncio
    async def test_profile_from_credentials_file_is_valid(self):
        fs = FakeFileSystem({"/fake/credentials": "[work]\nregion = eu-west-1\n"})
        with patch.dict(os.environ, {"AWS_PROFILE": "work"}, clear=True):
            config = await AsyncAwsConfig.resolve(
                fs=fs,
                config_file_path="/fake/config",
                credentials_file_path="/fake/credentials",
            )
            assert config.region == "eu-west-1"

    @pytest.mark.asyncio
    async def test_implicit_default_profile_not_validated(self):
        with patch.dict(os.environ, {"AWS_REGION": "us-east-1"}, clear=True):
            config = await AsyncAwsConfig.resolve(fs=NullFileSystem())
            assert config.region == "us-east-1"

    @pytest.mark.asyncio
    async def test_explicit_default_profile_is_validated(self):
        with patch.dict(os.environ, {"AWS_REGION": "us-east-1"}, clear=True):
            with pytest.raises(ProfileNotFoundError, match="'default'"):
                await AsyncAwsConfig.resolve(
                    profile="default",
                    fs=NullFileSystem(),
                )

    @pytest.mark.asyncio
    async def test_base_class_resolves_endpoint_uri_from_global_env(self):
        with patch.dict(
            os.environ,
            {"AWS_REGION": "us-east-1", "AWS_ENDPOINT_URL": "https://localhost:4567"},
            clear=True,
        ):
            config = await AsyncAwsConfig.resolve(fs=NullFileSystem())
            assert config.endpoint_uri == "https://localhost:4567"
            assert config.source_of("endpoint_uri") == ConfigSource.ENV

    @pytest.mark.asyncio
    async def test_resolve_defaults_all_non_resolved_fields(self):
        with patch.dict(os.environ, {"AWS_REGION": "us-east-1"}, clear=True):
            config = await AsyncAwsConfig.resolve(fs=NullFileSystem())
        assert config.interceptors == []
        assert config.transport is None
        assert config.retry_strategy is None
        assert config.http_request_config is None
        assert config.user_agent_extra is None
        assert config.aws_credentials_identity_resolver is None
        for name in ("interceptors", "transport", "user_agent_extra"):
            assert config.source_of(name) == ConfigSource.DEFAULT


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
            assert config.source_of("retry_mode") == ConfigSource.DEFAULT

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

    def test_direct_instantiation_with_arguments_raises_error(self):
        with pytest.raises(ConfigError, match="cannot be constructed directly"):
            AsyncAwsConfig("unexpected", region="us-east-1")

    def test_direct_constructor_does_not_advertise_config_fields(self):
        constructor_parameters = signature(AsyncAwsConfig).parameters
        assert not set(constructor_parameters) & set(
            AsyncAwsConfig._FIELDS  # pyright: ignore[reportPrivateUsage]
        )

    def test_typed_overrides_cover_all_base_config_fields(self):
        assert set(AwsConfigOverrides.__annotations__) == set(
            AsyncAwsConfig._FIELDS  # pyright: ignore[reportPrivateUsage]
        )

    @pytest.mark.asyncio
    async def test_unknown_override_field_raises_error(self):
        with patch.dict(os.environ, {"AWS_REGION": "us-east-1"}, clear=True):
            with pytest.raises(ConfigValidationError, match="Unknown config field"):
                await AsyncAwsConfig.resolve(
                    reigon="us-west-2"  # pyright: ignore[reportCallIssue]
                )

    @pytest.mark.parametrize(
        "field_name,invalid_value,match",
        [
            ("region", "bad-value!", "Must be a valid AWS region"),
            ("region", None, "Region is required"),
            (
                "retry_mode",
                "not-retry",
                "Invalid value for 'retry_mode'",
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

    @pytest.mark.asyncio
    async def test_typo_in_field_name_raises_attribute_error(self):
        with patch.dict(os.environ, {"AWS_REGION": "us-east-1"}, clear=True):
            config = await AsyncAwsConfig.resolve(fs=NullFileSystem())
            with pytest.raises(AttributeError, match="has no config field 'regoin'"):
                config.regoin = "us-west-2"


class TestSharedConfigContext:
    def test_default_profile_is_default(self):
        with patch.dict(os.environ, {}, clear=True):
            ctx = SharedConfigContext()
            assert ctx.profile_name == "default"
            assert ctx.profile_source is ConfigSource.DEFAULT

    def test_profile_from_aws_profile_env(self):
        with patch.dict(os.environ, {"AWS_PROFILE": "work"}, clear=True):
            ctx = SharedConfigContext()
            assert ctx.profile_name == "work"
            assert ctx.profile_source is ConfigSource.ENV

    def test_empty_aws_profile_env_treated_as_absent(self):
        with patch.dict(os.environ, {"AWS_PROFILE": ""}, clear=True):
            ctx = SharedConfigContext()
            assert ctx.profile_name == "default"
            assert ctx.profile_source is ConfigSource.DEFAULT

    def test_explicit_profile_overrides_env(self):
        with patch.dict(os.environ, {"AWS_PROFILE": "work"}, clear=True):
            ctx = SharedConfigContext(profile_name="custom")
            assert ctx.profile_name == "custom"
            assert ctx.profile_source is ConfigSource.OVERRIDE

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

    def test_deepcopy_returns_same_instance(self):
        with patch.dict(os.environ, {}, clear=True):
            ctx = SharedConfigContext(fs=NullFileSystem())
            assert deepcopy(ctx) is ctx


class TestConfigDeepCopy:
    """Generated clients deep-copy the config on every operation call.

    The copy exists to keep plugin mutations scoped to a single call, so the
    fields plugins write must be independent per copy. The resolution context
    is read-only afterwards and is shared instead, which keeps the per-request
    cost from scaling with the size of the caller's shared config files.
    """

    @pytest.mark.asyncio
    async def test_resolution_context_is_shared(self):
        fs = FakeFileSystem({"/fake/config": "[profile default]\nregion = us-east-1\n"})
        with patch.dict(os.environ, {}, clear=True):
            config = await AsyncAwsConfig.resolve(
                fs=fs,
                config_file_path="/fake/config",
                credentials_file_path="/fake/credentials",
            )
        # Sanity check: there is a context to share, so the assertion below
        # is meaningful.
        assert config.resolution_context() is not None
        assert deepcopy(config).resolution_context() is config.resolution_context()

    @pytest.mark.asyncio
    async def test_mutable_fields_are_isolated(self):
        with patch.dict(os.environ, {"AWS_REGION": "us-east-1"}, clear=True):
            config = await AsyncAwsConfig.resolve(fs=NullFileSystem())

        first = deepcopy(config)
        second = deepcopy(config)

        # A plugin appending an interceptor must not affect the shared config
        # or any other in-flight call.
        first.interceptors.append("first-only")
        second.interceptors.append("second-only")
        assert first.interceptors == ["first-only"]
        assert second.interceptors == ["second-only"]
        assert config.interceptors == []

        # Scalar overrides and their provenance stay per-copy too.
        first.region = "eu-west-2"
        assert first.region == "eu-west-2"
        assert config.region == "us-east-1"
        assert first.source_of("region") is ConfigSource.OVERRIDE
        assert config.source_of("region") is ConfigSource.ENV

    @pytest.mark.asyncio
    async def test_shared_resources_are_shared_by_identity(self):
        with patch.dict(os.environ, {"AWS_REGION": "us-east-1"}, clear=True):
            config = await AsyncAwsConfig.resolve(fs=NullFileSystem())

        # The transport, credentials resolver, and retry strategy hold network
        # clients, locks, and shared retry quotas that must not be duplicated
        transport = MockHTTPClient()
        resolver = EnvironmentCredentialsResolver()
        retry_strategy = StandardRetryStrategy()
        config.transport = transport
        config.aws_credentials_identity_resolver = resolver
        config.retry_strategy = retry_strategy

        copy = deepcopy(config)
        assert copy is not config
        assert copy.transport is transport
        assert copy.aws_credentials_identity_resolver is resolver
        assert copy.retry_strategy is retry_strategy

    @pytest.mark.asyncio
    async def test_deepcopy_with_no_shared_resources(self):
        with patch.dict(os.environ, {"AWS_REGION": "us-east-1"}, clear=True):
            config = await AsyncAwsConfig.resolve(fs=NullFileSystem())
        config.http_request_config = HTTPRequestConfiguration(read_timeout=1.0)

        copy = deepcopy(config)
        assert copy is not config
        # None resources are skipped by the identity-sharing shortcut.
        assert copy.transport is None
        assert copy.aws_credentials_identity_resolver is None
        assert copy.retry_strategy is None

        assert copy.region == "us-east-1"
        assert copy.http_request_config == config.http_request_config
        assert copy.http_request_config is not config.http_request_config


class TestResolveRetryMode:
    @pytest.mark.asyncio
    async def test_resolves_from_env(self):
        with patch.dict(os.environ, {"AWS_RETRY_MODE": "standard"}, clear=True):
            ctx = SharedConfigContext()
            result = await resolve_retry_mode(ctx)
            assert result.value == "standard"
            assert result.source == ConfigSource.ENV

    @pytest.mark.asyncio
    async def test_resolves_from_profile_when_no_env(self):
        fs = FakeFileSystem(
            {"/fake/config": "[profile default]\nretry_mode = standard\n"}
        )
        with patch.dict(os.environ, {}, clear=True):
            ctx = SharedConfigContext(
                fs=fs,
                config_file_path="/fake/config",
                credentials_file_path="/fake/credentials",
            )
            result = await resolve_retry_mode(ctx)
            assert result.value == "standard"
            assert result.source == ConfigSource.PROFILE

    @pytest.mark.asyncio
    async def test_adaptive_from_profile_warns_and_maps_to_standard(self):
        fs = FakeFileSystem(
            {"/fake/config": "[profile default]\nretry_mode = adaptive\n"}
        )
        with patch.dict(os.environ, {}, clear=True):
            ctx = SharedConfigContext(
                fs=fs,
                config_file_path="/fake/config",
                credentials_file_path="/fake/credentials",
            )
            with pytest.warns(
                UserWarning,
                match="'adaptive' retry mode is not supported, using 'standard' instead.",
            ):
                result = await resolve_retry_mode(ctx)
            assert result.value == "standard"
            assert result.source == ConfigSource.PROFILE

    @pytest.mark.asyncio
    async def test_env_takes_precedence_over_profile(self):
        fs = FakeFileSystem(
            {"/fake/config": "[profile default]\nretry_mode = adaptive\n"}
        )
        with patch.dict(os.environ, {"AWS_RETRY_MODE": "standard"}, clear=True):
            ctx = SharedConfigContext(
                fs=fs,
                config_file_path="/fake/config",
                credentials_file_path="/fake/credentials",
            )
            result = await resolve_retry_mode(ctx)
            assert result.value == "standard"
            assert result.source == ConfigSource.ENV

    @pytest.mark.asyncio
    async def test_returns_unset_when_not_found(self):
        with patch.dict(os.environ, {}, clear=True):
            ctx = SharedConfigContext(fs=NullFileSystem())
            result = await resolve_retry_mode(ctx)
            assert result.value is UNSET
            assert result.source is ConfigSource.DEFAULT

    @pytest.mark.asyncio
    async def test_legacy_warns_and_maps_to_standard(self):
        with patch.dict(os.environ, {"AWS_RETRY_MODE": "legacy"}, clear=True):
            ctx = SharedConfigContext()
            with pytest.warns(
                UserWarning,
                match="'legacy' retry mode is not supported, using 'standard' instead.",
            ):
                result = await resolve_retry_mode(ctx)
            assert result.value == "standard"
            assert result.source == ConfigSource.ENV

    @pytest.mark.asyncio
    async def test_adaptive_warns_and_maps_to_standard(self):
        with patch.dict(os.environ, {"AWS_RETRY_MODE": "adaptive"}, clear=True):
            ctx = SharedConfigContext()
            with pytest.warns(
                UserWarning,
                match="'adaptive' retry mode is not supported, using 'standard' instead.",
            ):
                result = await resolve_retry_mode(ctx)
            assert result.value == "standard"
            assert result.source == ConfigSource.ENV


class TestResolveMaxAttempts:
    @pytest.mark.asyncio
    async def test_resolves_from_env(self):
        with patch.dict(os.environ, {"AWS_MAX_ATTEMPTS": "5"}, clear=True):
            ctx = SharedConfigContext()
            result = await resolve_max_attempts(ctx)
            assert result.value == 5
            assert result.source == ConfigSource.ENV

    @pytest.mark.asyncio
    async def test_resolves_from_profile_when_no_env(self):
        fs = FakeFileSystem({"/fake/config": "[profile default]\nmax_attempts = 10\n"})
        with patch.dict(os.environ, {}, clear=True):
            ctx = SharedConfigContext(
                fs=fs,
                config_file_path="/fake/config",
                credentials_file_path="/fake/credentials",
            )
            result = await resolve_max_attempts(ctx)
            assert result.value == 10
            assert result.source == ConfigSource.PROFILE

    @pytest.mark.asyncio
    async def test_env_takes_precedence_over_profile(self):
        fs = FakeFileSystem({"/fake/config": "[profile default]\nmax_attempts = 10\n"})
        with patch.dict(os.environ, {"AWS_MAX_ATTEMPTS": "3"}, clear=True):
            ctx = SharedConfigContext(
                fs=fs,
                config_file_path="/fake/config",
                credentials_file_path="/fake/credentials",
            )
            result = await resolve_max_attempts(ctx)
            assert result.value == 3
            assert result.source == ConfigSource.ENV

    @pytest.mark.asyncio
    async def test_returns_unset_when_not_found(self):
        with patch.dict(os.environ, {}, clear=True):
            ctx = SharedConfigContext(fs=NullFileSystem())
            result = await resolve_max_attempts(ctx)
            assert result.value is UNSET

    @pytest.mark.asyncio
    async def test_casts_to_int(self):
        with patch.dict(os.environ, {"AWS_MAX_ATTEMPTS": "7"}, clear=True):
            ctx = SharedConfigContext()
            result = await resolve_max_attempts(ctx)
            assert result.value == 7
            assert isinstance(result.value, int)

    @pytest.mark.asyncio
    async def test_invalid_value_raises_error(self):
        with patch.dict(os.environ, {"AWS_MAX_ATTEMPTS": "abc"}, clear=True):
            ctx = SharedConfigContext()
            with pytest.raises(ConfigValidationError, match="Invalid integer value"):
                await resolve_max_attempts(ctx)


class TestEndpointUriResolver:
    @pytest.fixture
    def resolver(self):

        return EndpointUriResolver("bedrock_runtime")

    @pytest.mark.asyncio
    async def test_service_specific_env_var_takes_precedence(
        self, resolver: EndpointUriResolver
    ):
        fs = FakeFileSystem(
            {
                "/fake/config": "[profile default]\nendpoint_url = https://global-profile.com\n"
            }
        )
        with patch.dict(
            os.environ,
            {"AWS_ENDPOINT_URL_BEDROCK_RUNTIME": "https://service-env.com"},
            clear=True,
        ):
            ctx = SharedConfigContext(
                fs=fs,
                config_file_path="/fake/config",
                credentials_file_path="/fake/creds",
            )
            result = await resolver(ctx)
            assert result.value == "https://service-env.com"
            assert result.source == ConfigSource.ENV

    @pytest.mark.asyncio
    async def test_global_env_var_when_no_service_specific(
        self, resolver: EndpointUriResolver
    ):
        with patch.dict(
            os.environ, {"AWS_ENDPOINT_URL": "https://global-env.com"}, clear=True
        ):
            ctx = SharedConfigContext(
                fs=NullFileSystem(),
                config_file_path="/fake/config",
                credentials_file_path="/fake/creds",
            )
            result = await resolver(ctx)
            assert result.value == "https://global-env.com"
            assert result.source == ConfigSource.ENV

    @pytest.mark.asyncio
    async def test_service_env_beats_global_env(self, resolver: EndpointUriResolver):
        with patch.dict(
            os.environ,
            {
                "AWS_ENDPOINT_URL_BEDROCK_RUNTIME": "https://service-env.com",
                "AWS_ENDPOINT_URL": "https://global-env.com",
            },
            clear=True,
        ):
            ctx = SharedConfigContext(
                fs=NullFileSystem(),
                config_file_path="/fake/config",
                credentials_file_path="/fake/creds",
            )
            result = await resolver(ctx)
            assert result.value == "https://service-env.com"

    @pytest.mark.asyncio
    async def test_service_specific_config_file(self, resolver: EndpointUriResolver):
        fs = FakeFileSystem(
            {
                "/fake/config": (
                    "[profile default]\n"
                    "services = my-services\n"
                    "\n"
                    "[services my-services]\n"
                    "bedrock_runtime =\n"
                    "  endpoint_url = https://service-config.com\n"
                )
            }
        )
        with patch.dict(os.environ, {}, clear=True):
            ctx = SharedConfigContext(
                fs=fs,
                config_file_path="/fake/config",
                credentials_file_path="/fake/creds",
            )
            result = await resolver(ctx)
            assert result.value == "https://service-config.com"
            assert result.source == ConfigSource.PROFILE

    @pytest.mark.asyncio
    async def test_global_config_file_fallback(self, resolver: EndpointUriResolver):
        fs = FakeFileSystem(
            {
                "/fake/config": "[profile default]\nendpoint_url = https://global-config.com\n"
            }
        )
        with patch.dict(os.environ, {}, clear=True):
            ctx = SharedConfigContext(
                fs=fs,
                config_file_path="/fake/config",
                credentials_file_path="/fake/creds",
            )
            result = await resolver(ctx)
            assert result.value == "https://global-config.com"
            assert result.source == ConfigSource.PROFILE

    @pytest.mark.asyncio
    async def test_service_config_beats_global_config(
        self, resolver: EndpointUriResolver
    ):
        fs = FakeFileSystem(
            {
                "/fake/config": (
                    "[profile default]\n"
                    "endpoint_url = https://global-config.com\n"
                    "services = my-services\n"
                    "\n"
                    "[services my-services]\n"
                    "bedrock_runtime =\n"
                    "  endpoint_url = https://service-config.com\n"
                )
            }
        )
        with patch.dict(os.environ, {}, clear=True):
            ctx = SharedConfigContext(
                fs=fs,
                config_file_path="/fake/config",
                credentials_file_path="/fake/creds",
            )
            result = await resolver(ctx)
            assert result.value == "https://service-config.com"

    @pytest.mark.asyncio
    async def test_env_beats_config_file(self, resolver: EndpointUriResolver):
        fs = FakeFileSystem(
            {
                "/fake/config": (
                    "[profile default]\n"
                    "endpoint_url = https://global-config.com\n"
                    "services = my-services\n"
                    "\n"
                    "[services my-services]\n"
                    "bedrock_runtime =\n"
                    "  endpoint_url = https://service-config.com\n"
                )
            }
        )
        with patch.dict(
            os.environ, {"AWS_ENDPOINT_URL": "https://global-env.com"}, clear=True
        ):
            ctx = SharedConfigContext(
                fs=fs,
                config_file_path="/fake/config",
                credentials_file_path="/fake/creds",
            )
            result = await resolver(ctx)
            assert result.value == "https://global-env.com"

    @pytest.mark.asyncio
    async def test_returns_unset_when_nothing_found(
        self, resolver: EndpointUriResolver
    ):
        with patch.dict(os.environ, {}, clear=True):
            ctx = SharedConfigContext(
                fs=NullFileSystem(),
                config_file_path="/fake/config",
                credentials_file_path="/fake/creds",
            )
            result = await resolver(ctx)
            assert result.value is UNSET

    @pytest.mark.asyncio
    async def test_spaced_sdk_id_produces_valid_env_var_name(self):
        """Passing a raw SDK ID with spaces (e.g., 'Bedrock Runtime') should
        still resolve from the correctly normalized env var."""
        resolver = EndpointUriResolver("Bedrock Runtime")
        with patch.dict(
            os.environ,
            {"AWS_ENDPOINT_URL_BEDROCK_RUNTIME": "https://from-env.com"},
            clear=True,
        ):
            ctx = SharedConfigContext(
                fs=NullFileSystem(),
                config_file_path="/fake/config",
                credentials_file_path="/fake/creds",
            )
            result = await resolver(ctx)
            assert result.value == "https://from-env.com"
            assert result.source == ConfigSource.ENV


class TestReprDoesNotLeakSecrets:
    @pytest.mark.asyncio
    async def test_repr_does_not_leak_secrets(self):
        with patch.dict(os.environ, {"AWS_REGION": "us-east-1"}, clear=True):
            config = await AsyncAwsConfig.resolve(
                fs=NullFileSystem(),
                aws_access_key_id="AKIAIOSFODNN7EXAMPLE",
                aws_secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                aws_session_token="FwoGZXIvYXdzEBYaDHqa0AP",
            )

            # Sanity check: the credentials really are populated, so the
            # assertions below are meaningful.
            assert config.aws_access_key_id == "AKIAIOSFODNN7EXAMPLE"

            config_repr = repr(config)
            assert "AKIAIOSFODNN7EXAMPLE" not in config_repr
            assert "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY" not in config_repr
            assert "FwoGZXIvYXdzEBYaDHqa0AP" not in config_repr
            assert "region='us-east-1'" in config_repr

    @pytest.mark.asyncio
    async def test_subclass_repr_does_not_leak_secrets(self):
        """Subclasses declared with repr=False inherit the filtered __repr__.

        This mirrors what codegen emits for service-specific async configs.
        """

        @dataclass(kw_only=True, repr=False, init=False)
        class ServiceConfig(AsyncAwsConfig):
            aws_access_key_id: str | None = None
            aws_secret_access_key: str | None = None
            aws_session_token: str | None = None

        with patch.dict(os.environ, {"AWS_REGION": "us-east-1"}, clear=True):
            config = await ServiceConfig.resolve(
                fs=NullFileSystem(),
                aws_access_key_id="AKIAIOSFODNN7EXAMPLE",
                aws_secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            )

            assert config.aws_access_key_id == "AKIAIOSFODNN7EXAMPLE"

            config_repr = repr(config)
            assert config_repr.startswith("ServiceConfig(")
            assert "AKIAIOSFODNN7EXAMPLE" not in config_repr
            assert "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY" not in config_repr


class TestIncodeStaticCredentialResolution:
    """Credentials must be resolved from a single source — never mixed."""

    @pytest.mark.asyncio
    async def test_no_credentials_when_nothing_set(self):
        with patch.dict(os.environ, {"AWS_REGION": "us-east-1"}, clear=True):
            config = await AsyncAwsConfig.resolve(fs=NullFileSystem())
            assert config.aws_access_key_id is None
            assert config.aws_secret_access_key is None
            assert config.aws_session_token is None
            assert config.source_of("aws_access_key_id") == ConfigSource.DEFAULT

    @pytest.mark.asyncio
    async def test_partial_credential_override_raises_error(self):
        """Overriding only one credential raises an error."""
        with patch.dict(os.environ, {"AWS_REGION": "us-east-1"}, clear=True):
            with pytest.raises(
                ConfigValidationError, match="Partial credential override"
            ):
                await AsyncAwsConfig.resolve(
                    fs=NullFileSystem(),
                    config_file_path="/fake/config",
                    credentials_file_path="/fake/credentials",
                    aws_access_key_id="OVERRIDE_KEY",
                )

    @pytest.mark.asyncio
    async def test_credentials_cannot_be_overridden_after_resolution(self):
        with patch.dict(os.environ, {"AWS_REGION": "us-east-1"}, clear=True):
            config = await AsyncAwsConfig.resolve(
                fs=NullFileSystem(),
                aws_access_key_id="AKID",
                aws_secret_access_key="SECRET",
            )
            with pytest.raises(
                AttributeError, match="cannot be modified after resolution"
            ):
                config.aws_access_key_id = "NEW_KEY"

    @pytest.mark.asyncio
    async def test_session_token_only_override_raises_error(self):
        with patch.dict(os.environ, {"AWS_REGION": "us-east-1"}, clear=True):
            with pytest.raises(
                ConfigValidationError, match="Partial credential override"
            ):
                await AsyncAwsConfig.resolve(
                    fs=NullFileSystem(),
                    aws_session_token="FRESH_TOKEN",
                )

    @pytest.mark.asyncio
    async def test_key_and_secret_auto_wires_static_resolver(self):
        with patch.dict(os.environ, {"AWS_REGION": "us-east-1"}, clear=True):
            config = await AsyncAwsConfig.resolve(
                fs=NullFileSystem(),
                aws_access_key_id="AKID",
                aws_secret_access_key="SECRET",
            )
            assert config.aws_access_key_id == "AKID"
            assert config.aws_secret_access_key == "SECRET"
            assert config.aws_credentials_identity_resolver is not None
            identity = await config.aws_credentials_identity_resolver.get_identity(
                properties={}
            )
            assert identity.access_key_id == "AKID"
            assert identity.secret_access_key == "SECRET"

    @pytest.mark.asyncio
    async def test_explicit_resolver_not_overwritten(self):
        custom_resolver = StaticCredentialsResolver()
        with patch.dict(os.environ, {"AWS_REGION": "us-east-1"}, clear=True):
            config = await AsyncAwsConfig.resolve(
                fs=NullFileSystem(),
                aws_access_key_id="AKID",
                aws_secret_access_key="SECRET",
                aws_credentials_identity_resolver=custom_resolver,
            )
            assert config.aws_credentials_identity_resolver is custom_resolver

    @pytest.mark.asyncio
    async def test_no_credentials_leaves_resolver_none(self):
        with patch.dict(os.environ, {"AWS_REGION": "us-east-1"}, clear=True):
            config = await AsyncAwsConfig.resolve(fs=NullFileSystem())
            assert config.aws_credentials_identity_resolver is None


class TestResolveSdkUaAppId:
    @pytest.mark.asyncio
    async def test_resolves_from_env(self):
        with patch.dict(os.environ, {"AWS_SDK_UA_APP_ID": "my-app"}, clear=True):
            ctx = SharedConfigContext(fs=NullFileSystem())
            result = await resolve_sdk_ua_app_id(ctx)
            assert result.value == "my-app"
            assert result.source == ConfigSource.ENV

    @pytest.mark.asyncio
    async def test_resolves_from_profile(self):
        fs = FakeFileSystem(
            {"/fake/config": "[profile default]\nsdk_ua_app_id = profile-app\n"}
        )
        with patch.dict(os.environ, {}, clear=True):
            ctx = SharedConfigContext(fs=fs, config_file_path="/fake/config")
            result = await resolve_sdk_ua_app_id(ctx)
            assert result.value == "profile-app"
            assert result.source == ConfigSource.PROFILE

    @pytest.mark.asyncio
    async def test_returns_unset_when_not_configured(self):
        with patch.dict(os.environ, {}, clear=True):
            ctx = SharedConfigContext(fs=NullFileSystem())
            result = await resolve_sdk_ua_app_id(ctx)
            assert result.value is UNSET


class TestResolveEndpointUri:
    @pytest.mark.asyncio
    async def test_resolves_from_env(self):
        with patch.dict(
            os.environ, {"AWS_ENDPOINT_URL": "https://custom.endpoint"}, clear=True
        ):
            ctx = SharedConfigContext(fs=NullFileSystem())
            result = await resolve_endpoint_uri(ctx)
            assert result.value == "https://custom.endpoint"
            assert result.source == ConfigSource.ENV

    @pytest.mark.asyncio
    async def test_resolves_from_profile(self):
        fs = FakeFileSystem(
            {
                "/fake/config": "[profile default]\nendpoint_url = https://profile.endpoint\n"
            }
        )
        with patch.dict(os.environ, {}, clear=True):
            ctx = SharedConfigContext(fs=fs, config_file_path="/fake/config")
            result = await resolve_endpoint_uri(ctx)
            assert result.value == "https://profile.endpoint"
            assert result.source == ConfigSource.PROFILE

    @pytest.mark.asyncio
    async def test_returns_unset_when_not_configured(self):
        with patch.dict(os.environ, {}, clear=True):
            ctx = SharedConfigContext(fs=NullFileSystem())
            result = await resolve_endpoint_uri(ctx)
            assert result.value is UNSET
