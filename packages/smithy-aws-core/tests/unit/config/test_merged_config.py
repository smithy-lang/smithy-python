# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Unit tests for MergedConfig class."""

from smithy_aws_core.config.file_parser import (
    RawParsedSections,
    Section,
    StandardizedOutput,
)
from smithy_aws_core.config.merged_config import MergedConfig


def _to_section_map(
    raw: RawParsedSections | None,
) -> dict[str, Section]:
    """Convert a raw dict to a SectionMap (dict[str, Section])."""
    if raw is None:
        return {}
    result: dict[str, Section] = {}
    for name, value in raw.items():
        properties: dict[str, str] = {}
        sub_properties: dict[str, dict[str, str]] = {}
        for k, v in value.items():
            if isinstance(v, dict):
                sub_properties[k] = v
            else:
                properties[k] = v
        result[name] = Section(properties=properties, sub_properties=sub_properties)
    return result


def _make_config_file(
    config_profiles: RawParsedSections | None = None,
    config_sso_sessions: RawParsedSections | None = None,
    config_services: RawParsedSections | None = None,
    credentials_profiles: RawParsedSections | None = None,
) -> MergedConfig:
    """Helper to build a MergedConfig from raw dicts."""
    config_data = StandardizedOutput(
        profiles=_to_section_map(config_profiles),
        sso_sessions=_to_section_map(config_sso_sessions),
        services=_to_section_map(config_services),
    )
    credentials_data = StandardizedOutput(
        profiles=_to_section_map(credentials_profiles),
    )
    return MergedConfig(config_data, credentials_data)


class TestGet:
    """Tests for MergedConfig.get()"""

    def test_returns_value_for_existing_profile_and_key(self):
        cf = _make_config_file(config_profiles={"default": {"region": "us-east-1"}})
        assert cf.get("default", "region") == "us-east-1"

    def test_returns_none_for_missing_profile(self):
        cf = _make_config_file(config_profiles={"default": {"region": "us-east-1"}})
        assert cf.get("nonexistent", "region") is None

    def test_returns_none_for_missing_key(self):
        cf = _make_config_file(config_profiles={"default": {"region": "us-east-1"}})
        assert cf.get("default", "output") is None

    def test_is_case_insensitive_for_keys(self):
        cf = _make_config_file(config_profiles={"default": {"region": "us-east-1"}})
        assert cf.get("default", "REGION") == "us-east-1"
        assert cf.get("default", "Region") == "us-east-1"

    def test_returns_none_for_sub_property_key(self):
        """get() should return None if the value is a dict (sub-property).
        We should use get_sub_property instead."""
        cf = _make_config_file(
            config_profiles={"default": {"s3": {"max_concurrent_requests": "20"}}}
        )
        assert cf.get("default", "s3") is None


class TestGetSubProperty:
    """Tests for MergedConfig.get_sub_property()"""

    def test_returns_value(self):
        cf = _make_config_file(
            config_profiles={
                "default": {
                    "s3": {"max_concurrent_requests": "20", "addressing_style": "path"}
                }
            }
        )
        assert cf.get_sub_property("default", "s3", "max_concurrent_requests") == "20"
        assert cf.get_sub_property("default", "s3", "addressing_style") == "path"

    def test_returns_none_for_missing_sub_key(self):
        cf = _make_config_file(
            config_profiles={"default": {"s3": {"max_concurrent_requests": "20"}}}
        )
        assert cf.get_sub_property("default", "s3", "nonexistent") is None

    def test_returns_none_for_scalar_value(self):
        """If the parent key is a string (not a dict), return None."""
        cf = _make_config_file(config_profiles={"default": {"region": "us-east-1"}})
        assert cf.get_sub_property("default", "region", "anything") is None

    def test_returns_none_for_missing_profile(self):
        cf = _make_config_file(config_profiles={})
        assert cf.get_sub_property("default", "s3", "anything") is None


class TestGetProfile:
    """Tests for MergedConfig.get_profile()"""

    def test_returns_all_properties(self):
        cf = _make_config_file(
            config_profiles={"work": {"region": "us-west-2", "output": "json"}}
        )
        profile = cf.get_profile("work")
        assert profile is not None
        assert profile.properties == {"region": "us-west-2", "output": "json"}
        assert profile.sub_properties == {}

    def test_returns_none_for_missing(self):
        cf = _make_config_file(config_profiles={})
        assert cf.get_profile("nonexistent") is None


class TestMerge:
    """Tests for credentials/config merge behavior."""

    def test_credentials_override_config_for_duplicate_key(self):
        """When same key exists in both files, credentials wins."""
        cf = _make_config_file(
            config_profiles={
                "default": {
                    "aws_access_key_id": "CONFIG_KEY_ONE",
                    "region": "us-east-1",
                }
            },
            credentials_profiles={"default": {"aws_access_key_id": "CONFIG_KEY_TWO"}},
        )
        assert cf.get("default", "aws_access_key_id") == "CONFIG_KEY_TWO"
        assert cf.get("default", "region") == "us-east-1"

    def test_profiles_from_both_files_are_merged(self):
        cf = _make_config_file(
            config_profiles={"config_only": {"region": "us-east-1"}},
            credentials_profiles={"creds_only": {"aws_access_key_id": "KEY"}},
        )
        assert cf.get("config_only", "region") == "us-east-1"
        assert cf.get("creds_only", "aws_access_key_id") == "KEY"

    def test_properties_merged_within_same_profile(self):
        cf = _make_config_file(
            config_profiles={"default": {"region": "us-east-1", "output": "json"}},
            credentials_profiles={
                "default": {
                    "aws_access_key_id": "KEY",
                    "aws_secret_access_key": "SECRET",
                }
            },
        )
        profile = cf.get_profile("default")
        assert profile is not None
        assert profile.properties == {
            "region": "us-east-1",
            "output": "json",
            "aws_access_key_id": "KEY",
            "aws_secret_access_key": "SECRET",
        }


class TestSsoSessions:
    """Tests for SSO session access."""

    def test_get_sso_session_returns_properties(self):
        cf = _make_config_file(
            config_sso_sessions={
                "my-session": {
                    "sso_start_url": "https://example.com",
                    "sso_region": "us-east-1",
                }
            }
        )
        session = cf.get_sso_session("my-session")
        assert session is not None
        assert session.properties == {
            "sso_start_url": "https://example.com",
            "sso_region": "us-east-1",
        }

    def test_get_sso_session_returns_none_for_missing(self):
        cf = _make_config_file()
        assert cf.get_sso_session("nonexistent") is None


class TestProperties:
    """Tests for read-only property accessors."""

    def test_profiles_property_returns_all(self):
        cf = _make_config_file(
            config_profiles={"a": {"x": "1"}, "b": {"y": "2"}},
        )
        assert "a" in cf.profiles
        assert "b" in cf.profiles
        assert cf.profiles["a"].properties == {"x": "1"}
        assert cf.profiles["b"].properties == {"y": "2"}

    def test_sso_sessions_property(self):
        cf = _make_config_file(config_sso_sessions={"sess": {"url": "https://x"}})
        assert "sess" in cf.sso_sessions
        assert cf.sso_sessions["sess"].properties == {"url": "https://x"}

    def test_services_property(self):
        cf = _make_config_file(
            config_services={"my-svc": {"endpoint_url": "http://localhost"}}
        )
        assert "my-svc" in cf.services
        assert cf.services["my-svc"].properties == {"endpoint_url": "http://localhost"}
