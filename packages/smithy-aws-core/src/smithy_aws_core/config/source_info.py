# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
from enum import StrEnum


class SourceName(StrEnum):
    """Known source names for config value provenance tracking."""

    INSTANCE = "instance"  # value provided via Config constructor

    IN_CODE = "in-code"  # value set via setter after Config construction

    ENVIRONMENT = "environment"  # value resolved from environment variable

    DEFAULT = "default"  # value fall back to default


@dataclass(frozen=True)
class SimpleSource:
    """Source info for a config value resolved from a single source.

    Examples: region from environment, max_attempts from config file.
    """
    # TODO: Currently only environment variable is implemented as a config
    # source. Tests use raw strings (e.g., "environment", "config_file") as
    # source names to simulate multi-source scenarios. Once additional
    # config sources are implemented, update the `name` parameter type
    # from `str` to `SourceName` and replace raw strings in tests with
    # the corresponding enum values.
    name: str


@dataclass(frozen=True)
class ComplexSource:
    """Source info for a config value resolved from multiple sources.

    Used when a config property is composed of multiple sources.
    Example: retry_strategy is composed of retry_mode and max_attempts and they both
    could be from different sources: {"retry_mode": "environment", "max_attempts": "config_file"}
    """

    components: dict[str, str]


SourceInfo = SimpleSource | ComplexSource
