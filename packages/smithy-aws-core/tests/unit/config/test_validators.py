# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Unit tests for AWS configuration validators."""

from typing import Any

import pytest
from smithy_aws_core.config.validators import (
    ConfigValidationError,
    allow_none,
    validate_region,
    validate_retry_mode,
)


class TestAllowNoneDecorator:
    def test_allows_none_to_pass_through(self) -> None:
        call_count = 0

        @allow_none
        def mock_validator(value: Any, source: str | None = None) -> Any:
            nonlocal call_count
            call_count += 1
            return value

        result: Any = mock_validator(None)

        assert result is None
        assert call_count == 0  # Validator should not be called

    def test_calls_validator_for_non_none_values(self) -> None:
        call_count = 0

        @allow_none
        def mock_validator(value: Any, source: str | None = None) -> Any:
            nonlocal call_count
            call_count += 1
            return value

        _ = mock_validator("test")

        assert call_count == 1

    def test_preserves_validator_exceptions(self) -> None:
        @allow_none
        def failing_validator(value: Any, source: str | None = None) -> str:
            raise ValueError("Validation failed")

        with pytest.raises(ValueError, match="Validation failed"):
            failing_validator("test")


class TestValidators:
    @pytest.mark.parametrize("region", ["us-east-1", "eu-west-1", "ap-south-1"])
    def test_validate_region_accepts_valid_values(self, region: str) -> None:
        assert validate_region(region) == region

    @pytest.mark.parametrize("invalid", ["invalid-east-2", "us-east", "", "US-EAST-1"])
    def test_validate_region_rejects_invalid_values(self, invalid: str) -> None:
        with pytest.raises(ConfigValidationError):
            validate_region(invalid)

    @pytest.mark.parametrize("mode", ["standard", "simple"])
    def test_validate_retry_mode_accepts_valid_values(self, mode: str) -> None:
        assert validate_retry_mode(mode) == mode

    @pytest.mark.parametrize("invalid_mode", ["some_retry", "some_retry_one", ""])
    def test_validate_retry_mode_rejects_invalid_values(
        self, invalid_mode: str
    ) -> None:
        with pytest.raises(ConfigValidationError):
            validate_retry_mode(invalid_mode)
