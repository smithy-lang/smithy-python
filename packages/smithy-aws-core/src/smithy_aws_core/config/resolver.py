# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from functools import lru_cache

from smithy_core.config.resolver import ConfigResolver
from smithy_core.interfaces.config import ConfigSource

from .sources import EnvironmentSource


@lru_cache(maxsize=1)
def get_shared_resolver() -> ConfigResolver:
    """Get or create the shared AWS configuration resolver.

    This resolver is shared across all config objects and AWS service clients to avoid
    redundant reads from environment variables, config files, etc.

    :returns: The shared ConfigResolver instance
    """
    sources: list[ConfigSource] = [EnvironmentSource()]
    return ConfigResolver(sources=sources)


def reset_shared_resolver() -> None:
    """Reset the shared resolver (only for testing).

    This allows tests to start with a clean resolver state.
    """
    get_shared_resolver.cache_clear()
