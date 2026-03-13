# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Sequence
from typing import Any

from smithy_core.interfaces.config import ConfigSource

from smithy_aws_core.config.source_info import SimpleSource


class ConfigResolver:
    """Resolves configuration values from multiple sources.

    The resolver iterates through sources in precedence order, returning
    the first non-None value found for a given configuration key.
    """

    def __init__(self, sources: Sequence[ConfigSource]) -> None:
        """Initialize the resolver with sources in precedence order.

        :param sources: List of configuration sources in precedence order. The first
            source in the list has the highest priority.
        """
        self._sources = sources

    def get(self, key: str) -> tuple[Any, SimpleSource | None]:
        """Resolve a configuration value from sources by iterating through them in precedence order.

        :param key: The configuration key to resolve (e.g., 'retry_mode')

        :returns: A tuple of (value, source_name). If no source provides a value,
            returns (None, None).
        """
        for source in self._sources:
            value = source.get(key)
            if value is not None:
                return (value, SimpleSource(source.name))
        return (None, None)
