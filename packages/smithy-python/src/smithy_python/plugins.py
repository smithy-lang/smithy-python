# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Discoverable, topologically ordered generator customization hooks."""

from __future__ import annotations

import importlib
import importlib.metadata
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, ClassVar, Protocol, Self

from .exceptions import ModelError, PluginError
from .model import Model, Shape, ShapeID
from .symbols import PythonDependency, Symbol, SymbolProvider

if TYPE_CHECKING:
    from .context import GenerationContext
    from .settings import GeneratorSettings


@dataclass(frozen=True, slots=True)
class CodeSection:
    """Identifies a replaceable portion of a generated file."""

    name: str
    path: str
    shape: ShapeID | None = None
    metadata: Mapping[str, object] = field(default_factory=lambda: _empty_metadata())


def _empty_metadata() -> Mapping[str, object]:
    return {}


class ProtocolGenerator(Protocol):
    """A protocol implementation discovered from generator plugins."""

    protocol_id: ShapeID
    application_protocol: str
    protocol_symbol: Symbol
    dependencies: tuple[PythonDependency, ...]

    def protocol_expression(self, context: GenerationContext) -> str: ...

    def generate_tests(self, context: GenerationContext) -> None: ...


class GeneratorPlugin:
    """Base class for Python generator integrations.

    Hooks intentionally operate on public model, symbol, context, and code-section
    objects. Plugins do not need access to generator implementation details.
    """

    name: ClassVar[str]
    before: ClassVar[tuple[str, ...]] = ()
    after: ClassVar[tuple[str, ...]] = ()

    def preprocess_model(self, model: Model, settings: GeneratorSettings) -> Model:
        return model

    def decorate_symbol_provider(
        self, provider: SymbolProvider, context: GenerationContext
    ) -> SymbolProvider:
        return provider

    def protocols(self) -> Sequence[ProtocolGenerator]:
        return ()

    def write_additional_files(self, context: GenerationContext) -> None:
        pass

    def intercept_code(
        self, context: GenerationContext, section: CodeSection, code: str
    ) -> str:
        return code


class PluginRegistry:
    """An immutable collection of plugins in dependency order."""

    ENTRY_POINT_GROUP = "smithy_python.codegen.plugins"

    def __init__(self, plugins: Iterable[GeneratorPlugin]) -> None:
        self.plugins = self._order(tuple(plugins))

    @classmethod
    def discover(cls, explicit: Iterable[str] = ()) -> Self:
        from .integrations.aws import AwsPlugin
        from .integrations.rest_json import RestJsonPlugin

        plugins: list[GeneratorPlugin] = [RestJsonPlugin(), AwsPlugin()]
        names = {plugin.name for plugin in plugins}
        for entry_point in importlib.metadata.entry_points(group=cls.ENTRY_POINT_GROUP):
            if entry_point.name in names:
                continue
            plugin = _instantiate(entry_point.load(), entry_point.name)
            plugins.append(plugin)
            names.add(plugin.name)
        for target in explicit:
            plugin = _load_explicit(target)
            if plugin.name in names:
                plugins = [item for item in plugins if item.name != plugin.name]
            plugins.append(plugin)
            names.add(plugin.name)
        return cls(plugins)

    def preprocess(self, model: Model, settings: GeneratorSettings) -> Model:
        for plugin in self.plugins:
            model = plugin.preprocess_model(model, settings)
        return model

    def resolve_protocol(self, service: Shape) -> ProtocolGenerator | None:
        registered: dict[ShapeID, ProtocolGenerator] = {}
        for plugin in self.plugins:
            for protocol in plugin.protocols():
                registered[protocol.protocol_id] = protocol
        for trait_id in service.traits:
            try:
                shape_id = ShapeID.parse(trait_id)
            except ModelError:
                continue
            if shape_id in registered:
                return registered[shape_id]
        return None

    @staticmethod
    def _order(plugins: tuple[GeneratorPlugin, ...]) -> tuple[GeneratorPlugin, ...]:
        by_name: dict[str, GeneratorPlugin] = {}
        for plugin in plugins:
            name = getattr(plugin, "name", "")
            if not name:
                raise PluginError(f"Generator plugin has no name: {plugin!r}")
            if name in by_name:
                raise PluginError(f"Duplicate generator plugin name: {name}")
            by_name[name] = plugin

        outgoing: dict[str, set[str]] = defaultdict(set)
        indegree = dict.fromkeys(by_name, 0)
        for plugin in plugins:
            for successor in plugin.before:
                if successor in by_name and successor not in outgoing[plugin.name]:
                    outgoing[plugin.name].add(successor)
                    indegree[successor] += 1
            for predecessor in plugin.after:
                if predecessor in by_name and plugin.name not in outgoing[predecessor]:
                    outgoing[predecessor].add(plugin.name)
                    indegree[plugin.name] += 1

        # Preserve discovery order among otherwise unrelated plugins.
        position = {plugin.name: index for index, plugin in enumerate(plugins)}
        ready = sorted(
            (name for name, count in indegree.items() if count == 0),
            key=position.__getitem__,
        )
        ordered: list[GeneratorPlugin] = []
        while ready:
            name = ready.pop(0)
            ordered.append(by_name[name])
            for successor in sorted(outgoing[name], key=position.__getitem__):
                indegree[successor] -= 1
                if indegree[successor] == 0:
                    ready.append(successor)
                    ready.sort(key=position.__getitem__)
        if len(ordered) != len(plugins):
            cycle = ", ".join(name for name, count in indegree.items() if count)
            raise PluginError(f"Generator plugin ordering contains a cycle: {cycle}")
        return tuple(ordered)


def _load_explicit(target: str) -> GeneratorPlugin:
    module_name, separator, attribute = target.partition(":")
    if not separator or not module_name or not attribute:
        raise PluginError(
            f"Invalid plugin {target!r}; expected a 'package.module:object' reference"
        )
    try:
        value = getattr(importlib.import_module(module_name), attribute)
    except (ImportError, AttributeError) as error:
        raise PluginError(
            f"Unable to load generator plugin {target!r}: {error}"
        ) from error
    return _instantiate(value, target)


def _instantiate(value: Any, source: str) -> GeneratorPlugin:
    try:
        plugin = value() if isinstance(value, type) else value
    except Exception as error:
        raise PluginError(
            f"Unable to initialize generator plugin {source!r}: {error}"
        ) from error
    if not isinstance(plugin, GeneratorPlugin):
        raise PluginError(f"Generator plugin {source!r} must extend GeneratorPlugin")
    return plugin
