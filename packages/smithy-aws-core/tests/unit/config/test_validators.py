# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from typing import Any

import pytest
from smithy_aws_core.config.validators import (
    ConfigValidationError,
    validate_max_attempts,
    validate_region,
    validate_retry_mode,
)


class TestValidators:
    @pytest.mark.parametrize("region", ["us-east-1", "eu-west-1", "ap-south-1"])
    def test_validate_region_accepts_valid_values(self, region: str) -> None:
        assert validate_region(region) == region

    @pytest.mark.parametrize("invalid", ["-invalid", "-east", "12345", ""])
    def test_validate_region_rejects_invalid_values(self, invalid: str) -> None:
        with pytest.raises(ConfigValidationError):
            validate_region(invalid)

    @pytest.mark.parametrize("mode", ["standard"])
    def test_validate_retry_mode_accepts_valid_values(self, mode: str) -> None:
        assert validate_retry_mode(mode) == mode

    @pytest.mark.parametrize("invalid_mode", ["some_retry", "some_retry_one", ""])
    def test_validate_retry_mode_rejects_invalid_values(
        self, invalid_mode: str
    ) -> None:
        with pytest.raises(ConfigValidationError):
            validate_retry_mode(invalid_mode)

    @pytest.mark.parametrize("invalid_max_attempts", ["abcd", 0, -1])
    def test_validate_invalid_max_attempts_raises_error(
        self, invalid_max_attempts: Any
    ) -> None:
        with pytest.raises(
            ConfigValidationError,
            match=r"(max_attempts must be a number|max_attempts must be a positive integer)",
        ):
            validate_max_attempts(invalid_max_attempts)

    def test_invalid_retry_mode_error_message(self) -> None:
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_retry_mode("random_mode")
        assert (
            "Invalid value for 'retry_mode': 'random_mode'. retry_mode must be one "
            "of ('standard',), got random_mode" in str(exc_info.value)
        )
