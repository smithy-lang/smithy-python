# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import json
from pathlib import Path
from typing import cast

import pytest
from smithy_aws_core.config.exceptions import ConfigParseError
from smithy_aws_core.config.file_parser import (
    FileType,
    parse_content,
    standardize,
)
from smithy_aws_core.config.parsed_config_file import ParsedConfigFile

_PARSER_TESTS_FILE = (
    Path(__file__).parent / "test-data" / "config-file-parser-tests.json"
)

with open(_PARSER_TESTS_FILE) as f:
    _PARSER_TESTS = json.load(f)["tests"]


def _run_parse_and_standardize(
    config_content: str | None = None,
    credentials_content: str | None = None,
) -> dict[str, object]:
    """Parse and standardize config/credentials content, return merged output.

    Returns a dict with 'profiles' and 'ssoSessions' keys matching the
    JSON test case expected output format.
    """
    raw_config = parse_content(config_content) if config_content is not None else {}
    raw_credentials = (
        parse_content(credentials_content) if credentials_content is not None else {}
    )

    std_config = standardize(raw_config, FileType.CONFIG)
    std_credentials = standardize(raw_credentials, FileType.CREDENTIALS)

    config_file = ParsedConfigFile(std_config, std_credentials)

    result: dict[str, object] = {}
    if config_file.profiles:
        result["profiles"] = config_file.profiles
    else:
        result["profiles"] = {}

    if config_file.sso_sessions:
        result["ssoSessions"] = config_file.sso_sessions

    return result


@pytest.mark.parametrize(
    "test_case",
    _PARSER_TESTS,
    ids=lambda t: t["name"],
)
def test_config_file_parser_conformance(test_case: dict[str, object]):
    """Validate config file parsing against SEP conformance test cases."""
    input_data = cast(dict[str, str], test_case["input"])
    expected_output = cast(dict[str, object], test_case["output"])

    config_content = input_data.get("configFile")
    credentials_content = input_data.get("credentialsFile")

    # Error case
    if "errorContaining" in expected_output:
        expected_error = cast(str, expected_output["errorContaining"])
        with pytest.raises(ConfigParseError, match=expected_error):
            _run_parse_and_standardize(config_content, credentials_content)
        return

    # Success case
    actual_output: dict[str, object] = _run_parse_and_standardize(
        config_content, credentials_content
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
