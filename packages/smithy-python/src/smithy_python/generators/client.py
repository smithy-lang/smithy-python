# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from ..context import GenerationContext
from ..docs import DocumentationConverter
from ..model import Shape, ShapeType
from ..symbols import OPERATION_METHOD
from ..writer import PythonWriter


class ClientGenerator:
    def __init__(self, context: GenerationContext) -> None:
        self.context = context
        self.docs = DocumentationConverter()

    def run(self) -> None:
        service = self.context.service
        if service is None:
            return
        writer = PythonWriter()
        self._imports(writer)
        operations = [
            shape for shape in self.context.shapes if shape.type is ShapeType.OPERATION
        ]
        for operation in operations:
            writer.import_(
                ".models",
                self.context.symbol_provider.to_symbol(operation).name,
                category="local",
            )
            for key in ("input", "output"):
                target = self._target(operation, key)
                if target is not None:
                    writer.import_(
                        ".models",
                        self.context.symbol_provider.to_symbol(target).name,
                        category="local",
                    )

        service_symbol = self.context.symbol_provider.to_symbol(service)
        writer.write("logger = logging.getLogger(__name__)")
        writer.write()
        writer.write(f"class {service_symbol.name}:")
        documentation = service.trait("smithy.api#documentation")
        writer.write(
            self.docs.docstring(
                str(documentation)
                if documentation
                else f"Client for {service.id.name}."
            )
        )
        writer.write("    def __init__(")
        writer.write(
            "        self, config: Config | None = None, plugins: list[Plugin] | None = None"
        )
        writer.write("    ) -> None:")
        writer.write("        self._config = config or Config()")
        default_plugins = self.context.intercept(
            f"src/{self.context.settings.module_name}/client.py",
            "client.default_plugins",
            "",
            shape=service,
        )
        writer.write("        client_plugins: list[Plugin] = [")
        if default_plugins:
            writer.write(default_plugins.rstrip())
        writer.write("        ]")
        writer.write("        if plugins:")
        writer.write("            client_plugins.extend(plugins)")
        writer.write("        for plugin in client_plugins:")
        writer.write("            plugin(self._config)")
        writer.write("        self._retry_strategy_resolver = RetryStrategyResolver()")
        for operation in operations:
            writer.write()
            for line in self._operation(operation).splitlines():
                writer.write(f"    {line}" if line else "")

        path = f"src/{self.context.settings.module_name}/client.py"
        self.context.write(path, writer.render(), section="client", shape=service)

    def _imports(self, writer: PythonWriter) -> None:
        writer.import_("copy", "deepcopy", category="stdlib")
        writer.import_("logging", category="stdlib")
        writer.import_("smithy_core.aio.client", "ClientCall", category="third_party")
        writer.import_(
            "smithy_core.aio.client", "RequestPipeline", category="third_party"
        )
        writer.import_(
            "smithy_core.aio.retries", "RetryStrategyResolver", category="third_party"
        )
        writer.import_(
            "smithy_core.exceptions", "ExpectationNotMetError", category="third_party"
        )
        writer.import_(
            "smithy_core.interceptors", "InterceptorChain", category="third_party"
        )
        writer.import_("smithy_core.types", "TypedProperties", category="third_party")
        writer.import_(
            "smithy_http.plugins", "user_agent_plugin", category="third_party"
        )
        writer.import_(
            "smithy_http.aio.aiohttp", "AIOHTTPClient", category="third_party"
        )
        writer.import_(".config", "Config", category="local")
        writer.import_(".config", "Plugin", category="local")
        if self.context.service is not None and self.context.service.has_trait(
            "aws.api#service"
        ):
            writer.import_(".user_agent", "aws_user_agent_plugin", category="local")

    def _operation(self, operation: Shape) -> str:
        input_shape = self._target(operation, "input")
        output_shape = self._target(operation, "output")
        if input_shape is None or output_shape is None:
            return f"# {operation.id.name} omitted because it has no generated input/output."
        operation_symbol = self.context.symbol_provider.to_symbol(operation)
        method = operation_symbol.expect_property(OPERATION_METHOD).name
        input_name = self.context.symbol_provider.to_symbol(input_shape).name
        output_name = self.context.symbol_provider.to_symbol(output_shape).name
        documentation = operation.trait("smithy.api#documentation")
        docs = self.docs.docstring(
            str(documentation) if documentation else f"Invoke {operation.id.name}."
        ).lstrip()
        return "\n".join(
            (
                f"async def {method}(",
                f"    self, input: {input_name}, plugins: list[Plugin] | None = None",
                f") -> {output_name}:",
                f"    {docs}",
                "    config = deepcopy(self._config)",
                "    for plugin in plugins or ():",
                "        plugin(config)",
                "    if config.protocol is None:",
                "        raise ExpectationNotMetError(",
                '            "protocol must be configured before making a call"',
                "        )",
                "    if config.transport is None:",
                "        config.transport = AIOHTTPClient()",
                "    retry_strategy = await self._retry_strategy_resolver.resolve_retry_strategy(",
                "        retry_strategy=config.retry_strategy",
                "    )",
                "    pipeline = RequestPipeline(protocol=config.protocol, transport=config.transport)",
                "    call = ClientCall(",
                "        input=input,",
                f"        operation={operation_symbol.name},",
                '        context=TypedProperties({"config": config}),',
                "        interceptor=InterceptorChain(config.interceptors),",
                "        auth_scheme_resolver=config.auth_scheme_resolver,",
                "        supported_auth_schemes=config.auth_schemes,",
                "        endpoint_resolver=config.endpoint_resolver,",
                "        retry_strategy=retry_strategy,",
                "    )",
                "    return await pipeline(call)",
            )
        )

    def _target(self, operation: Shape, key: str) -> Shape | None:
        value = operation.attributes.get(key)
        if not isinstance(value, dict):
            return None
        target_id = value.get("target")
        if not isinstance(target_id, str):
            return None
        target = self.context.model.expect(target_id)
        return target if target in self.context.shapes else None
