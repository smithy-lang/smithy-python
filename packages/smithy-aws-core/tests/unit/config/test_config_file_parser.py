# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import json
from pathlib import Path
from typing import cast

import pytest
from smithy_aws_core.config import DefaultFileSystem
from smithy_aws_core.config.file_parser import (
    FileType,
    RawParsedSections,
    parse_config_file,
    standardize,
)
from smithy_aws_core.config.merged_config import MergedConfig
from smithy_core.exceptions import ConfigParseError

_PARSER_TESTS_FILE = (
    Path(__file__).parent / "test-data" / "config-file-parser-tests.json"
)

with open(_PARSER_TESTS_FILE) as f:
    _PARSER_TESTS = json.load(f)["tests"]


async def _run_parse_and_standardize(
    tmp_path: Path,
    config_content: str | None = None,
    credentials_content: str | None = None,
) -> dict[str, object]:
    """Write content to temp files, parse through public API, return merged output."""
    # Write config content to temp file
    fs = DefaultFileSystem()
    if config_content is not None:
        config_path = tmp_path / "config"
        config_path.write_text(config_content, encoding="utf-8")
        raw_config = await parse_config_file(str(config_path), fs)
    else:
        raw_config = {}

    # Write credentials content to temp file
    if credentials_content is not None:
        credentials_path = tmp_path / "credentials"
        credentials_path.write_text(credentials_content, encoding="utf-8")
        raw_credentials = await parse_config_file(str(credentials_path), fs)
    else:
        raw_credentials = {}

    # Standardize
    std_config = standardize(raw_config, FileType.CONFIG)
    std_credentials = standardize(raw_credentials, FileType.CREDENTIALS)

    # Merge
    merged_config = MergedConfig(std_config, std_credentials)

    # Build output matching JSON test format (convert Profile objects to flat dicts)
    result: dict[str, object] = {}
    profiles_dict = {}
    for name, profile in merged_config.profiles.items():
        flat: dict[str, str | dict[str, str]] = dict(profile.properties)
        profiles_dict[name] = flat
    result["profiles"] = profiles_dict

    sso_sessions_dict = {}
    for name, profile in merged_config.sso_sessions.items():
        flat = dict(profile.properties)
        sso_sessions_dict[name] = flat
    if sso_sessions_dict:
        result["ssoSessions"] = sso_sessions_dict

    return result


@pytest.mark.parametrize(
    "test_case",
    _PARSER_TESTS,
    ids=lambda t: t["name"],
)
@pytest.mark.asyncio
async def test_config_file_parser_conformance(
    test_case: dict[str, object], tmp_path: Path
):
    """Validate config file parsing against conformance test cases in config-file-parser-tests.json."""
    input_data = cast(dict[str, str], test_case["input"])
    expected_output = cast(dict[str, object], test_case["output"])

    config_content = input_data.get("configFile")
    credentials_content = input_data.get("credentialsFile")

    # Error case
    if "errorContaining" in expected_output:
        expected_error = cast(str, expected_output["errorContaining"])
        with pytest.raises(ConfigParseError, match=expected_error):
            await _run_parse_and_standardize(
                tmp_path, config_content, credentials_content
            )
        return

    # Success case
    actual_output: dict[str, object] = await _run_parse_and_standardize(
        tmp_path, config_content, credentials_content
    )

    if "profiles" in expected_output:
        assert actual_output.get("profiles", {}) == expected_output["profiles"], (
            f"Profiles mismatch.\n"
            f"Expected: {json.dumps(expected_output['profiles'], indent=2)}\n"
            f"Actual: {json.dumps(actual_output.get('profiles', {}), indent=2)}"
        )

    if "ssoSessions" in expected_output:
        assert actual_output.get("ssoSessions", {}) == expected_output["ssoSessions"], (
            f"SSO sessions mismatch.\n"
            f"Expected: {json.dumps(expected_output['ssoSessions'], indent=2)}\n"
            f"Actual: {json.dumps(actual_output.get('ssoSessions', {}), indent=2)}"
        )


@pytest.mark.parametrize(
    "section_name,should_be_valid",
    [
        # Valid credentials profiles — names that happen to start with reserved words
        ("services-internal", True),
        ("sso-session-backup", True),
        ("sso-session.prod", True),
        # Invalid — uses the "profile <name>" prefix syntax
        ("profile prod", False),
        ("sso-session default", False),
        ("service my-service", False),
    ],
)
def test_credentials_section_names(section_name: str, should_be_valid: bool):
    raw: RawParsedSections = {section_name: {"key": "value"}}
    result = standardize(raw, FileType.CREDENTIALS)
    if should_be_valid:
        assert section_name in result.profiles, (
            f"'{section_name}' should be a valid credentials profile"
        )
        assert result.profiles[section_name].properties.get("key") == "value"
    else:
        assert section_name not in result.profiles, (
            f"'{section_name}' should be rejected in credentials file"
        )


@pytest.mark.asyncio
async def test_parse_error_includes_file_path(tmp_path: Path):
    fs = DefaultFileSystem()
    bad_file = tmp_path / "config"
    bad_file.write_text("[profile p\n")  # unclosed section header

    with pytest.raises(ConfigParseError, match=str(bad_file)):
        await parse_config_file(str(bad_file), fs)


@pytest.mark.asyncio
async def test_invalid_property_continuation_not_appended_to_previous(tmp_path: Path):
    """Continuation lines after an invalid property should be discarded,
    not appended to the previous valid property."""
    fs = DefaultFileSystem()
    config_file = tmp_path / "config"
    config_file.write_text(
        "[profile p]\nregion = us-east-1\ninvalid key = ignored\n  continuation\n"
    )
    raw = await parse_config_file(str(config_file), fs)
    result = standardize(raw, FileType.CONFIG)
    assert result.profiles["p"].properties["region"] == "us-east-1"


@pytest.mark.asyncio
async def test_invalid_property_in_first_line_with_continuation_ignored(tmp_path: Path):
    """Continuation lines when the first property is invalid should be discarded"""
    fs = DefaultFileSystem()
    config_file = tmp_path / "config"
    config_file.write_text(
        "[profile p]\ninvalid key = ignored\n  continuation\n"
        "region = us-east-1\ninvalid key = ignored\n  continuation\n"
    )
    raw = await parse_config_file(str(config_file), fs)
    result = standardize(raw, FileType.CONFIG)
    assert result.profiles["p"].properties["region"] == "us-east-1"


@pytest.mark.asyncio
async def test_consecutive_invalid_properties_ignored(tmp_path: Path):
    """Consecutive invalid properties should be discarded"""
    fs = DefaultFileSystem()
    config_file = tmp_path / "config"
    config_file.write_text(
        "[profile p]\nregion = us-east-1\ninvalid key = ignored\n  continuation\n"
        "invalid key = ignored\n  continuation\ninvalid key = ignored\n  continuation\n"
        "output = json\n"
    )
    raw = await parse_config_file(str(config_file), filesystem=fs)
    result = standardize(raw, FileType.CONFIG)
    assert result.profiles["p"].properties["region"] == "us-east-1"
    assert result.profiles["p"].properties["output"] == "json"
