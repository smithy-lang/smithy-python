# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from typing import TYPE_CHECKING, Any

from .context import shared_config_files_exist
from .exceptions import (
    ConfigError,
    ConfigParseError,
    ConfigValidationError,
    ProfileNotFoundError,
)
from .merged_config import MergedConfig
from .types import ConfigSource

if TYPE_CHECKING:
    from ..aio.config.aws_config import AsyncAwsConfig, AwsConfigOverrides
    from ..aio.config.context import SharedConfigContext, load_config
    from ..aio.config.filesystem import DefaultFileSystem, FileSystem

__all__ = [
    "AsyncAwsConfig",
    "AwsConfigOverrides",
    "ConfigError",
    "ConfigParseError",
    "ConfigSource",
    "ConfigValidationError",
    "DefaultFileSystem",
    "FileSystem",
    "MergedConfig",
    "ProfileNotFoundError",
    "SharedConfigContext",
    "load_config",
    "shared_config_files_exist",
]

# Preserve the pre-relocation public import path without an eager import cycle:
# aio.config.aws_config imports back into this package's exceptions during its own
# initialization, so these relocated symbols are resolved lazily on first access.
_RELOCATED = {
    "AsyncAwsConfig": "aws_config",
    "AwsConfigOverrides": "aws_config",
    "SharedConfigContext": "context",
    "load_config": "context",
    "DefaultFileSystem": "filesystem",
    "FileSystem": "filesystem",
}


def __getattr__(name: str) -> Any:
    module = _RELOCATED.get(name)
    if module is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    import importlib

    return getattr(importlib.import_module(f"..aio.config.{module}", __name__), name)


# Keep the lazily relocated names reachable via dir() so the public surface is
# discoverable (and recorded by the api-snapshot), not just importable.
def __dir__() -> list[str]:
    return [*globals(), *_RELOCATED]
