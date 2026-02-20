# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from typing import Any

from smithy_core.interfaces.config import ConfigSource


class ConfigResolver:
    """Resolves configuration values from multiple sources.

    The resolver iterates through sources in precedence order, returning
    the first non-None value found for a given configuration key.
    """

    def __init__(self, sources: list[ConfigSource]) -> None:
        """Initialize the resolver with sources in precedence order.

        :param sources: List of configuration sources in precedence order. The first
            source in the list has the highest priority. The list is copied to
            prevent external modification.
        """
        self._sources = list(sources)

    def get(self, key: str) -> tuple[Any, str]:
        """Resolve a configuration value from sources by iterating through them in precedence order.

        :param key: The configuration key to resolve (e.g., 'retry_mode')

        :returns: A tuple of (value, source_name). If no source provides a value,
            returns (None, 'unresolved').
        """
        for source in self._sources:
            value = source.get(key)
            if value is not None:
                return (value, source.name)
        return (None, "unresolved")
