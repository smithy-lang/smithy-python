# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
from typing import Any, ClassVar

import pytest
from smithy_core.config import Config, ConfigValidationError
from smithy_core.config.types import ConfigSource, FieldSpec, Resolved


def _region_resolver(_ctx: Any) -> Resolved[str]:
    return Resolved(value="us-east-1", source=ConfigSource.ENV)


@dataclass(repr=False)
class _ToyConfig(Config):
    region: str | None = None
    max_attempts: int | None = None
    endpoint: str | None = None

    _FIELDS: ClassVar[dict[str, FieldSpec]] = {
        "region": FieldSpec(
            default=None,
            resolver=_region_resolver,
        ),
        "max_attempts": FieldSpec(default=3, converter=int),
        "endpoint": FieldSpec(default=None),
    }


def test_resolver_supplies_value_and_source():
    config = _ToyConfig.resolve()
    assert config.region == "us-east-1"
    assert config.source_of("region") is ConfigSource.ENV


def test_override_wins_over_resolver_and_runs_converter():
    config = _ToyConfig.resolve(region="eu-west-1", max_attempts="5")
    assert config.region == "eu-west-1"
    assert config.source_of("region") is ConfigSource.OVERRIDE
    assert config.max_attempts == 5  # converter int("5")


def test_default_applies_when_no_resolver_or_override():
    config = _ToyConfig.resolve()
    assert config.max_attempts == 3
    assert config.endpoint is None


def test_unknown_field_raises():
    with pytest.raises(ConfigValidationError, match="Unknown config field"):
        _ToyConfig.resolve(not_a_field="x")


def test_validator_runs_on_resolved_value():
    def reject_negative(value: Any) -> None:
        if value is not None and value < 0:
            raise ValueError("max_attempts must be non-negative")

    @dataclass(repr=False)
    class _ValidatedConfig(Config):
        max_attempts: int | None = None

        _FIELDS: ClassVar[dict[str, FieldSpec]] = {
            "max_attempts": FieldSpec(default=1, validator=reject_negative),
        }

    with pytest.raises(ValueError, match="non-negative"):
        _ValidatedConfig.resolve(max_attempts=-1)
