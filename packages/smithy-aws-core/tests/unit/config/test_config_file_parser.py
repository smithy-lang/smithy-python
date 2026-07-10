# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import json
from pathlib import Path
from typing import cast

import pytest
from smithy_aws_core.config.exceptions import ConfigParseError
from smithy_aws_core.config.file_parser import (
    FileType,
    parse_config_file,
    standardize,
)
from smithy_aws_core.config.merged_config import MergedConfig

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
    if config_content is not None:
        config_path = tmp_path / "config"
        config_path.write_text(config_content, encoding="utf-8")
        raw_config = await parse_config_file(str(config_path))
    else:
        raw_config = {}

    # Write credentials content to temp file
    if credentials_content is not None:
        credentials_path = tmp_path / "credentials"
        credentials_path.write_text(credentials_content, encoding="utf-8")
        raw_credentials = await parse_config_file(str(credentials_path))
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
        flat.update(profile.sub_properties)
        profiles_dict[name] = flat
    result["profiles"] = profiles_dict

    sso_sessions_dict = {}
    for name, profile in merged_config.sso_sessions.items():
        flat = dict(profile.properties)
        flat.update(profile.sub_properties)
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
