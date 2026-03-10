# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass


@dataclass(frozen=True)
class SimpleSource:
    """Source info for a config value resolved from a single source.

    Examples: region from environment, max_attempts from config file.
    """

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
