# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import pytest
from smithy_aws_core.config.validators import (
    ConfigValidationError,
    validate_host_label,
    validate_max_attempts,
    validate_retry_mode,
)


class TestValidators:
    @pytest.mark.parametrize("region", ["us-east-1", "eu-west-1", "ap-south-1"])
    def test_validate_region_accepts_valid_values(self, region: str) -> None:
        assert validate_host_label(region) == region

    @pytest.mark.parametrize("invalid", ["-invalid", "-east", "12345", "", 1234])
    def test_validate_region_rejects_invalid_values(self, invalid: str) -> None:
        with pytest.raises(ConfigValidationError):
            validate_host_label(invalid)

    @pytest.mark.parametrize("mode", ["standard", "simple"])
    def test_validate_retry_mode_accepts_valid_values(self, mode: str) -> None:
        assert validate_retry_mode(mode) == mode

    @pytest.mark.parametrize("invalid_mode", ["some_retry", "some_retry_one", ""])
    def test_validate_retry_mode_rejects_invalid_values(
        self, invalid_mode: str
    ) -> None:
        with pytest.raises(ConfigValidationError):
            validate_retry_mode(invalid_mode)

    def test_validate_invalid_max_attempts_raises_error(self) -> None:
        with pytest.raises(
            ConfigValidationError, match="max_attempts must be a number"
        ):
            validate_max_attempts("abcd")

    def test_invalid_retry_mode_error_message(self) -> None:
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_retry_mode("random_mode")
        assert (
            "Invalid value for 'retry_mode': 'random_mode'. Retry mode must be one "
            "of ('simple', 'standard'), got random_mode" in str(exc_info.value)
        )
