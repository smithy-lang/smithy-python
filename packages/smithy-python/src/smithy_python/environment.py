# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Smithy build environment provided to the code generator."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Self


@dataclass(frozen=True, slots=True)
class PluginEnvironment:
    """Environment values supplied by Smithy's process-based run plugin."""

    root_dir: Path | None = None
    plugin_dir: Path | None = None
    projection_name: str | None = None
    artifact_name: str | None = None
    includes_prelude: bool = False

    @classmethod
    def from_environ(cls, environ: Mapping[str, str] | None = None) -> Self:
        """Load the Smithy run plugin environment from a mapping."""

        source = os.environ if environ is None else environ

        def path(name: str) -> Path | None:
            return Path(value) if (value := source.get(name)) else None

        return cls(
            root_dir=path("SMITHY_ROOT_DIR"),
            plugin_dir=path("SMITHY_PLUGIN_DIR"),
            projection_name=source.get("SMITHY_PROJECTION_NAME"),
            artifact_name=source.get("SMITHY_ARTIFACT_NAME"),
            includes_prelude=source.get("SMITHY_INCLUDES_PRELUDE", "false").lower()
            == "true",
        )
