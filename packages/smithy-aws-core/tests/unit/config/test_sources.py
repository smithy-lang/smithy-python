# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import os
from unittest.mock import patch

from smithy_aws_core.config.sources import EnvironmentSource


class TestEnvironmentSource:
    def test_source_name(self):
        source = EnvironmentSource()
        assert source.name == "environment"

    def test_get_region_from_aws_region(self):
        with patch.dict(os.environ, {"AWS_REGION": "us-west-2"}, clear=False):
            source = EnvironmentSource()
            value = source.get("region")
            assert value == "us-west-2"

    def test_get_returns_none_when_env_var_not_set(self):
        with patch.dict(os.environ, {}, clear=True):
            source = EnvironmentSource()
            value = source.get("region")
            assert value is None

    def test_get_returns_none_for_unknown_key(self):
        source = EnvironmentSource()
        value = source.get("unknown_config_key")
        assert value is None

    def test_get_handles_empty_string_env_var(self):
        with patch.dict(os.environ, {"AWS_REGION": ""}, clear=False):
            source = EnvironmentSource()
            value = source.get("region")
            # Empty string should be treated as None
            assert value == ""

    def test_get_handles_whitespace_env_var(self):
        with patch.dict(os.environ, {"AWS_REGION": "  us-west-2  "}, clear=False):
            source = EnvironmentSource()
            value = source.get("region")
            # Whitespaces should be stripped
            assert value == "us-west-2"

    def test_get_handles_whole_whitespace_env_var(self):
        with patch.dict(os.environ, {"AWS_REGION": "  "}, clear=False):
            source = EnvironmentSource()
            value = source.get("region")
            # Whitespaces should be stripped
            assert value == ""

    def test_multiple_keys_with_different_env_vars(self):
        env_vars = {"AWS_REGION": "eu-west-1", "AWS_RETRY_MODE": "standard"}
        with patch.dict(os.environ, env_vars, clear=False):
            source = EnvironmentSource()

            region = source.get("region")
            retry_mode = source.get("retry_mode")

            assert region == "eu-west-1"
            assert retry_mode == "standard"

    def test_get_is_idempotent(self):
        with patch.dict(os.environ, {"AWS_REGION": "ap-south-1"}, clear=False):
            source = EnvironmentSource()
            # Calling get on source multiple times should return the same value
            value1 = source.get("region")
            value2 = source.get("region")
            value3 = source.get("region")

            assert value1 == value2 == value3 == "ap-south-1"

    def test_source_does_not_cache_env_vars(self):
        source = EnvironmentSource()

        # First read
        with patch.dict(os.environ, {"AWS_REGION": "us-east-1"}, clear=False):
            value1 = source.get("region")
            assert value1 == "us-east-1"

        # Environment changes
        with patch.dict(os.environ, {"AWS_REGION": "us-west-2"}, clear=False):
            value2 = source.get("region")
            assert value2 == "us-west-2"

        # Source reads from os.environ and not from cache
        assert value1 != value2
