# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from .file_parser import (
    Section,
    SectionMap,
    StandardizedOutput,
)


class MergedConfig:
    """A merged representation of AWS config and credentials files.

    Provides lookup access to profile properties after merging both files
    with the correct precedence rules (credentials wins for duplicates).
    """

    def __init__(
        self,
        config_data: StandardizedOutput,
        credentials_data: StandardizedOutput,
    ):
        """Initialize with standardized data from both files.

        :param config_data: Standardized output from the config file.
        :param credentials_data: Standardized output from the credentials file.
        """
        self._profiles = self._merge_profiles(
            config_data.profiles,
            credentials_data.profiles,
        )
        self._sso_sessions = config_data.sso_sessions
        self._services = config_data.services

    def get(self, profile_name: str, key: str) -> str | None:
        """Get a property value for a specific profile.

        :param profile_name: The profile name to look up.
        :param key: The property key (case-insensitive, stored lowercase).
        :returns: The property value, or None if not found.
        """
        profile = self._profiles.get(profile_name)
        if profile is None:
            return None
        val = profile.properties.get(key.lower())
        return val if isinstance(val, str) else None

    def get_sub_property(self, profile_name: str, key: str, sub_key: str) -> str | None:
        """Get a sub-property value for a specific profile.

        For properties like:
            s3 =
              max_concurrent_requests = 20

        Usage: get_sub_property("default", "s3", "max_concurrent_requests")

        :param profile_name: The profile name.
        :param key: The parent property key.
        :param sub_key: The sub-property key.
        :returns: The sub-property value, or None if not found.
        """
        profile = self._profiles.get(profile_name)
        if profile is None:
            return None
        val = profile.properties.get(key.lower())
        if isinstance(val, dict):
            return val.get(sub_key.lower())
        return None

    def get_profile(self, profile_name: str) -> Section | None:
        """Get all properties for a profile.

        :param profile_name: The profile name.
        :returns: Section object, or None if profile doesn't exist.
        """
        return self._profiles.get(profile_name)

    def get_sso_session(self, session_name: str) -> Section | None:
        """Get properties for an SSO session.

        :param session_name: The SSO session name.
        :returns: Section object, or None if session doesn't exist.
        """
        return self._sso_sessions.get(session_name)

    @property
    def profiles(self) -> SectionMap:
        """All merged profiles."""
        return self._profiles

    @property
    def sso_sessions(self) -> SectionMap:
        """All SSO sessions from config file."""
        return self._sso_sessions

    @property
    def services(self) -> SectionMap:
        """All services sections from config file."""
        return self._services

    @staticmethod
    def _merge_profiles(
        config_profiles: SectionMap,
        credentials_profiles: SectionMap,
    ) -> SectionMap:
        """Merge profiles from config and credentials files. Credentials wins for duplicates."""
        merged: SectionMap = {}
        for name, section in config_profiles.items():
            merged[name] = Section(properties=dict(section.properties))
        for name, section in credentials_profiles.items():
            if name in merged:
                merged[name].properties.update(section.properties)
            else:
                merged[name] = Section(properties=dict(section.properties))
        return merged
