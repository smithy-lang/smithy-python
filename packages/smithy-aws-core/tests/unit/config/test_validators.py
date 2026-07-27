# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Tests for config field validators."""

import pytest
from smithy_aws_core.config.exceptions import ConfigValidationError
from smithy_aws_core.config.types import FieldSpec
from smithy_aws_core.config.validators import (
    validate_max_attempts,
    validate_region,
    validate_retry_mode,
)


class TestValidateRegion:
    @pytest.mark.parametrize(
        "region",
        [
            "us-east-1",
            "ap-southeast-2",
            "eu-west-1",
            "us",
            "us-gov-west-1",
        ],
    )
    def test_valid_regions(self, region: str):
        validate_region(region)

    def test_none_raises(self):
        with pytest.raises(ConfigValidationError, match="Region is required"):
            validate_region(None)

    @pytest.mark.parametrize(
        "region,reason",
        [
            ("", "empty string"),
            ("-us-east-1", "starts with dash"),
            ("us-east-1-", "ends with dash"),
            ("12345", "all numbers"),
            ("us-east-1!", "special characters"),
            ("us east 1", "spaces"),
        ],
        ids=lambda x: x if isinstance(x, str) else "",
    )
    def test_invalid_regions(self, region: str, reason: str):
        with pytest.raises(ConfigValidationError, match="Must be a valid AWS region"):
            validate_region(region)

    def test_non_string_raises(self):
        with pytest.raises(ConfigValidationError, match="Must be a valid AWS region"):
            validate_region(123)


class TestFieldSpec:
    """Tests for FieldSpec validation constraints."""

    def test_default_only_is_valid(self):
        FieldSpec(default=None)

    def test_default_factory_only_is_valid(self):
        FieldSpec(default_factory=list)

    def test_both_default_and_factory_raises(self):
        with pytest.raises(ValueError, match="cannot set both"):
            FieldSpec(default=None, default_factory=list)

    def test_neither_default_nor_factory_raises(self):
        with pytest.raises(ValueError, match="exactly one of"):
            FieldSpec()


class TestValidateRetryMode:
    @pytest.mark.parametrize("mode", ["standard"])
    def test_valid_modes(self, mode: str):
        validate_retry_mode(mode)

    @pytest.mark.parametrize("mode", ["fake-mode", "", "STANDARD"])
    def test_invalid_modes(self, mode: str):
        with pytest.raises(ConfigValidationError, match="retry_mode"):
            validate_retry_mode(mode)


class TestValidateMaxAttempts:
    @pytest.mark.parametrize("value", [1, 3, 10, 100])
    def test_valid_values(self, value: int):
        validate_max_attempts(value)

    @pytest.mark.parametrize("value", [0, -1, -100])
    def test_invalid_values(self, value: int):
        with pytest.raises(ConfigValidationError, match="max_attempts"):
            validate_max_attempts(value)
