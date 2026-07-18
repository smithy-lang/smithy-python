# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from ..context import GenerationContext
from ..docs import DocumentationConverter
from ..model import Shape, ShapeType
from ..symbols import DESERIALIZER, OPERATION_METHOD, PythonDependency
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
        operations = [
            shape for shape in self.context.shapes if shape.type is ShapeType.OPERATION
        ]
        self._imports(writer, operations)
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
            input_stream, output_stream = self._event_streams(operation)
            if input_stream is not None:
                writer.import_(
                    ".models",
                    self.context.symbol_provider.to_symbol(input_stream).name,
                    category="local",
                )
            if output_stream is not None:
                output_symbol = self.context.symbol_provider.to_symbol(output_stream)
                writer.import_(".models", output_symbol.name, category="local")
                writer.import_(
                    ".models",
                    output_symbol.expect_property(DESERIALIZER).name,
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

    def _imports(self, writer: PythonWriter, operations: list[Shape]) -> None:
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
        stream_kinds = {
            (
                input_stream is not None,
                output_stream is not None,
            )
            for operation in operations
            for input_stream, output_stream in (self._event_streams(operation),)
            if input_stream is not None or output_stream is not None
        }
        if (True, True) in stream_kinds:
            writer.import_(
                "smithy_core.aio.eventstream",
                "DuplexEventStream",
                category="third_party",
            )
        if (True, False) in stream_kinds:
            writer.import_(
                "smithy_core.aio.eventstream",
                "InputEventStream",
                category="third_party",
            )
        if (False, True) in stream_kinds:
            writer.import_(
                "smithy_core.aio.eventstream",
                "OutputEventStream",
                category="third_party",
            )
        writer.import_(
            "smithy_http.plugins", "user_agent_plugin", category="third_party"
        )
        if self.context.service is None or not self.context.service.has_trait(
            "aws.api#service"
        ):
            writer.import_(
                "smithy_http.aio.aiohttp", "AIOHTTPClient", category="third_party"
            )
            self.context.add_dependency(
                PythonDependency("smithy-http", "~=0.4.0", extras=("aiohttp",))
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
        input_stream, output_stream = self._event_streams(operation)
        input_stream_name = (
            self.context.symbol_provider.to_symbol(input_stream).name
            if input_stream is not None
            else None
        )
        output_stream_symbol = (
            self.context.symbol_provider.to_symbol(output_stream)
            if output_stream is not None
            else None
        )
        if input_stream_name is not None and output_stream_symbol is not None:
            output_stream_name = output_stream_symbol.name
            return_type = (
                f"DuplexEventStream[{input_stream_name}, {output_stream_name}, "
                f"{output_name}]"
            )
            invocation = (
                "    return await pipeline.duplex_stream(\n"
                "        call,\n"
                f"        {input_stream_name},\n"
                f"        {output_stream_name},\n"
                f"        {output_stream_symbol.expect_property(DESERIALIZER).name}().deserialize,\n"
                "    )"
            )
        elif input_stream_name is not None:
            return_type = f"InputEventStream[{input_stream_name}, {output_name}]"
            invocation = (
                f"    return await pipeline.input_stream(call, {input_stream_name})"
            )
        elif output_stream_symbol is not None:
            output_stream_name = output_stream_symbol.name
            return_type = f"OutputEventStream[{output_stream_name}, {output_name}]"
            invocation = (
                "    return await pipeline.output_stream(\n"
                "        call,\n"
                f"        {output_stream_name},\n"
                f"        {output_stream_symbol.expect_property(DESERIALIZER).name}().deserialize,\n"
                "    )"
            )
        else:
            return_type = output_name
            invocation = "    return await pipeline(call)"
        documentation = operation.trait("smithy.api#documentation")
        docs = self.docs.docstring(
            str(documentation) if documentation else f"Invoke {operation.id.name}."
        ).lstrip()
        return "\n".join(
            (
                f"async def {method}(",
                f"    self, input: {input_name}, plugins: list[Plugin] | None = None",
                f") -> {return_type}:",
                f"    {docs}",
                "    config = deepcopy(self._config)",
                "    for plugin in plugins or ():",
                "        plugin(config)",
                "    if config.protocol is None or config.transport is None:"
                if self.context.service is not None
                and self.context.service.has_trait("aws.api#service")
                else "    if config.protocol is None:",
                "        raise ExpectationNotMetError(",
                '            "protocol and transport must be configured before making a call"'
                if self.context.service is not None
                and self.context.service.has_trait("aws.api#service")
                else '            "protocol must be configured before making a call"',
                "        )",
                *(
                    ()
                    if self.context.service is not None
                    and self.context.service.has_trait("aws.api#service")
                    else (
                        "    if config.transport is None:",
                        "        config.transport = AIOHTTPClient()",
                    )
                ),
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
                invocation,
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

    def _event_streams(self, operation: Shape) -> tuple[Shape | None, Shape | None]:
        return (
            self._event_stream(self._target(operation, "input")),
            self._event_stream(self._target(operation, "output")),
        )

    def _event_stream(self, container: Shape | None) -> Shape | None:
        if container is None:
            return None
        for member in container.members:
            target = self.context.model.expect(member.target)
            if target.type is ShapeType.UNION and target.has_trait(
                "smithy.api#streaming"
            ):
                return target
        return None
