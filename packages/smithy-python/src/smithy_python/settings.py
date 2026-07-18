# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Self, cast

from .exceptions import CodegenError
from .model import ShapeID


class ArtifactType(StrEnum):
    CLIENT = "client"
    TYPES = "types"


@dataclass(frozen=True, slots=True)
class PluginEnvironment:
    """Environment values supplied by Smithy's process-based run plugin."""

    root_dir: Path | None = None
    plugin_dir: Path | None = None
    projection_name: str | None = None
    artifact_name: str | None = None
    includes_prelude: bool = False

    @classmethod
    def from_environ(cls, environ: Mapping[str, str] = os.environ) -> Self:
        def path(name: str) -> Path | None:
            return Path(value) if (value := environ.get(name)) else None

        return cls(
            root_dir=path("SMITHY_ROOT_DIR"),
            plugin_dir=path("SMITHY_PLUGIN_DIR"),
            projection_name=environ.get("SMITHY_PROJECTION_NAME"),
            artifact_name=environ.get("SMITHY_ARTIFACT_NAME"),
            includes_prelude=environ.get("SMITHY_INCLUDES_PRELUDE", "false").lower()
            == "true",
        )


@dataclass(frozen=True, slots=True)
class GeneratorSettings:
    artifact_type: ArtifactType
    module_name: str
    module_version: str
    service: ShapeID | None = None
    module_description: str | None = None
    selector: str = "*"
    generate_inputs_and_outputs: bool = False
    include_shapes: tuple[ShapeID, ...] = ()
    format_code: bool = True
    lint_code: bool = False

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[a-z_][a-z_0-9]*", self.module_name):
            raise CodegenError(
                "Python module names must start with a lowercase letter or underscore "
                "and contain only lowercase letters, numbers, and underscores"
            )
        if not self.module_version:
            raise CodegenError("moduleVersion must not be empty")
        if self.artifact_type is ArtifactType.CLIENT and self.service is None:
            raise CodegenError("Client generation requires a service shape ID")

    @classmethod
    def from_mapping(
        cls, artifact_type: ArtifactType, values: Mapping[str, object]
    ) -> Self:
        def required_string(*keys: str) -> str:
            for key in keys:
                if isinstance(value := values.get(key), str) and value:
                    return value
            raise CodegenError(f"Missing required setting: {keys[0]}")

        service_value = values.get("service")
        include_values = values.get("includeShapes", values.get("include_shapes", []))
        if not isinstance(include_values, list | tuple):
            raise CodegenError("includeShapes must be an array of shape IDs")
        include_shape_ids = cast(list[object] | tuple[object, ...], include_values)
        if not all(isinstance(value, str) for value in include_shape_ids):
            raise CodegenError("includeShapes must contain only shape ID strings")
        module_description = values.get(
            "moduleDescription", values.get("module_description")
        )
        if module_description is not None and not isinstance(module_description, str):
            raise CodegenError("moduleDescription must be a string")
        return cls(
            artifact_type=artifact_type,
            service=ShapeID.parse(service_value)
            if isinstance(service_value, str)
            else None,
            module_name=required_string("module", "module_name"),
            module_version=required_string("moduleVersion", "module_version"),
            module_description=module_description,
            selector=str(values.get("selector", "*")),
            generate_inputs_and_outputs=bool(
                values.get(
                    "generateInputsAndOutputs",
                    values.get("generate_inputs_and_outputs", False),
                )
            ),
            include_shapes=tuple(
                ShapeID.parse(value)
                for value in include_shape_ids
                if isinstance(value, str)
            ),
            format_code=bool(values.get("format", values.get("format_code", True))),
            lint_code=bool(values.get("lint", values.get("lint_code", False))),
        )

    @property
    def description(self) -> str:
        return (
            self.module_description or f"{self.module_name} {self.artifact_type.value}"
        )
