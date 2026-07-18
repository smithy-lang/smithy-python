# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .model import Model, Shape
from .plugins import CodeSection, PluginRegistry, ProtocolGenerator
from .settings import GeneratorSettings, PluginEnvironment
from .symbols import PythonDependency, SymbolProvider
from .writer import FileManifest


@dataclass(slots=True)
class GenerationContext:
    """Shared, public state for generators and plugins."""

    model: Model
    settings: GeneratorSettings
    environment: PluginEnvironment
    output_dir: Path
    plugins: PluginRegistry
    symbol_provider: SymbolProvider
    shapes: tuple[Shape, ...]
    protocol: ProtocolGenerator | None = None
    manifest: FileManifest = field(init=False)
    dependencies: set[PythonDependency] = field(default_factory=lambda: set())

    def __post_init__(self) -> None:
        self.manifest = FileManifest(self.output_dir)

    @property
    def service(self) -> Shape | None:
        if self.settings.service is None:
            return None
        return self.model.service(self.settings.service)

    def add_dependency(self, *dependencies: PythonDependency) -> None:
        self.dependencies.update(dependencies)

    def write(
        self,
        path: str,
        code: str,
        *,
        section: str = "file",
        shape: Shape | None = None,
    ) -> None:
        self.manifest.write(path, self.intercept(path, section, code, shape=shape))

    def intercept(
        self,
        path: str,
        section: str,
        code: str,
        *,
        shape: Shape | None = None,
    ) -> str:
        code_section = CodeSection(
            name=section,
            path=path,
            shape=shape.id if shape is not None else None,
        )
        for plugin in self.plugins.plugins:
            code = plugin.intercept_code(self, code_section, code)
        return code

    def append(
        self,
        path: str,
        code: str,
        *,
        section: str,
        shape: Shape | None = None,
    ) -> None:
        self.manifest.append(path, self.intercept(path, section, code, shape=shape))
