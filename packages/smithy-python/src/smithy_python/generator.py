# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""End-to-end orchestration for Python-native Smithy code generation."""

from __future__ import annotations

import fnmatch
from pathlib import Path

from .context import GenerationContext
from .exceptions import CodegenError
from .filters import AllShapes, ConnectedShapeFilter
from .generators.client import ClientGenerator
from .generators.config import ConfigGenerator
from .generators.models import ModelsGenerator
from .generators.schema import SchemaGenerator
from .generators.setup import SetupGenerator
from .model import Model, Shape, ShapeID, ShapeType
from .plugins import PluginRegistry
from .postprocess import format_python, lint_python
from .settings import ArtifactType, GeneratorSettings, PluginEnvironment
from .symbols import PythonSymbolProvider


class PythonCodeGenerator:
    """Runs a complete generation request with ordered plugin hooks."""

    def __init__(self, plugins: PluginRegistry | None = None) -> None:
        self.plugins = plugins or PluginRegistry.discover()

    def generate(
        self,
        model: Model,
        settings: GeneratorSettings,
        *,
        output_dir: Path,
        environment: PluginEnvironment | None = None,
    ) -> tuple[Path, ...]:
        environment = environment or PluginEnvironment.from_environ()
        model = self.plugins.preprocess(model, settings)
        shapes = self._select_shapes(model, settings)
        provider = PythonSymbolProvider(model, settings)
        context = GenerationContext(
            model=model,
            settings=settings,
            environment=environment,
            output_dir=output_dir,
            plugins=self.plugins,
            symbol_provider=provider,
            shapes=shapes,
        )
        for plugin in self.plugins.plugins:
            context.symbol_provider = plugin.decorate_symbol_provider(
                context.symbol_provider, context
            )

        if settings.artifact_type is ArtifactType.CLIENT:
            service = context.service
            if service is None:
                raise CodegenError("Client generation requires a service")
            context.protocol = self.plugins.resolve_protocol(service)
            if context.protocol is None:
                raise CodegenError(
                    f"No installed generator plugin supports a protocol on {service.id}"
                )
            context.add_dependency(*context.protocol.dependencies)

        SchemaGenerator(context).run()
        ModelsGenerator(context).run()
        if settings.artifact_type is ArtifactType.CLIENT:
            ConfigGenerator(context).run()
            ClientGenerator(context).run()
            if context.protocol is not None:
                context.protocol.generate_tests(context)
        for plugin in self.plugins.plugins:
            plugin.write_additional_files(context)
        SetupGenerator(context).run()

        written = context.manifest.flush()
        if settings.format_code:
            format_python(output_dir, written)
        if settings.lint_code:
            lint_python(output_dir)
        return written

    def _select_shapes(
        self, model: Model, settings: GeneratorSettings
    ) -> tuple[Shape, ...]:
        predicate = self._predicate(settings)
        if settings.artifact_type is ArtifactType.CLIENT:
            if settings.service is None:
                raise CodegenError("Client generation requires a service")
            return ConnectedShapeFilter(
                (settings.service,),
                include=settings.include_shapes,
                predicate=predicate,
            ).select(model)

        roots: tuple[ShapeID, ...] = settings.include_shapes
        if settings.service is not None:
            roots = (settings.service, *roots)
        selector_roots = self._selector_roots(model, settings.selector)
        if selector_roots is not None:
            roots = (*roots, *selector_roots)
        if roots:
            return ConnectedShapeFilter(roots, predicate=predicate).select(model)
        return AllShapes(predicate).select(model)

    def _predicate(self, settings: GeneratorSettings):
        selector = settings.selector.strip()

        def predicate(shape: Shape) -> bool:
            if settings.artifact_type is ArtifactType.TYPES:
                if shape.type in {
                    ShapeType.SERVICE,
                    ShapeType.RESOURCE,
                    ShapeType.OPERATION,
                }:
                    return False
                if not settings.generate_inputs_and_outputs and (
                    shape.has_trait("smithy.api#input")
                    or shape.has_trait("smithy.api#output")
                ):
                    return False
            if (
                selector in {"", "*"}
                or "#" in selector
                or selector.startswith("namespace:")
            ):
                return True
            raise CodegenError(
                "Python codegen selectors currently support '*', comma-separated "
                "absolute shape IDs, and 'namespace:<glob>'"
            )

        return predicate

    def _selector_roots(
        self, model: Model, selector: str
    ) -> tuple[ShapeID, ...] | None:
        selector = selector.strip()
        if selector in {"", "*"}:
            return None
        if selector.startswith("namespace:"):
            pattern = selector.removeprefix("namespace:")
            return tuple(
                shape.id
                for shape in model
                if fnmatch.fnmatch(shape.id.namespace, pattern)
            )
        values = tuple(
            ShapeID.parse(value.strip())
            for value in selector.split(",")
            if value.strip()
        )
        for value in values:
            model.expect(value)
        return values
