# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import json
import platform as platform_mod
from pathlib import Path
from typing import cast
from unittest.mock import patch

import pytest
from smithy_aws_core.config import resolve_config_paths

_LOCATION_TESTS_FILE = (
    Path(__file__).parent / "test-data" / "config-file-location-tests.json"
)

with open(_LOCATION_TESTS_FILE) as f:
    _LOCATION_TESTS = json.load(f)["tests"]


@pytest.mark.parametrize(
    "test_case",
    _LOCATION_TESTS,
    ids=lambda t: t["name"],
)
def test_config_file_location(test_case: dict[str, object]):
    """Validate config/credentials file location based on the test cases
    in config-file-location-tests.json file"""
    test_platform = cast(str, test_case.get("platform", "linux"))

    # Skip Windows-specific tests on non-Windows machines and vice versa
    if test_platform == "windows" and platform_mod.system() != "Windows":
        pytest.skip("Windows-specific test, skipping on non-Windows platform")
    if test_platform == "linux" and platform_mod.system() == "Windows":
        pytest.skip("Linux-specific test, skipping on Windows platform")

    environment = cast(dict[str, str], test_case.get("environment", {}))
    expected_config = cast(str, test_case["configLocation"])
    expected_credentials = cast(str, test_case["credentialsLocation"])

    # Build the environment: only include keys that are actually "set"
    env_vars: dict[str, str] = {k: v for k, v in environment.items() if v != "ignored"}

    language_home = cast(str, test_case.get("languageSpecificHome"))
    if language_home and language_home != "ignored" and "HOME" not in env_vars:
        env_vars["HOME"] = language_home

    # Test resolve_config_paths() with the mocked environment
    with patch.dict("os.environ", env_vars, clear=True):
        resolved_config, resolved_credentials = resolve_config_paths()

    assert resolved_config == expected_config, (
        f"Config location mismatch: got '{resolved_config}', "
        f"expected '{expected_config}'"
    )
    assert resolved_credentials == expected_credentials, (
        f"Credentials location mismatch: got '{resolved_credentials}', "
        f"expected '{expected_credentials}'"
    )
