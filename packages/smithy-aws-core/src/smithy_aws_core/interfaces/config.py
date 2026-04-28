# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ConfigSource(Protocol):
    """Protocol for configuration sources that provide values from various locations
    like environment variables and configuration files.
    """

    @property
    def name(self) -> str:
        """Returns a string identifying the source.

        :returns: A string identifier for this source.
        """
        ...

    def get(self, key: str) -> Any | None:
        """Returns a configuration value from the source.

        :param key: The configuration key to retrieve (e.g., 'region')

        :returns: The value associated with the key, or None if not found.
        """
        ...
