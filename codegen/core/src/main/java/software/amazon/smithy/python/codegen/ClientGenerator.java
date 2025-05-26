/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen;

import static software.amazon.smithy.python.codegen.SymbolProperties.DESERIALIZER;
import static software.amazon.smithy.python.codegen.SymbolProperties.OPERATION_METHOD;

import java.util.Collection;
import java.util.LinkedHashSet;
import software.amazon.smithy.codegen.core.SymbolProvider;
import software.amazon.smithy.codegen.core.SymbolReference;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.knowledge.EventStreamIndex;
import software.amazon.smithy.model.knowledge.EventStreamInfo;
import software.amazon.smithy.model.knowledge.TopDownIndex;
import software.amazon.smithy.model.shapes.OperationShape;
import software.amazon.smithy.model.shapes.ServiceShape;
import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.model.traits.DocumentationTrait;
import software.amazon.smithy.model.traits.StringTrait;
import software.amazon.smithy.python.codegen.integrations.PythonIntegration;
import software.amazon.smithy.python.codegen.integrations.RuntimeClientPlugin;
import software.amazon.smithy.python.codegen.sections.*;
import software.amazon.smithy.python.codegen.writer.MarkdownToRstDocConverter;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Generates the actual client and implements operations.
 */
@SmithyInternalApi
final class ClientGenerator implements Runnable {

    private final GenerationContext context;
    private final Model model;
    private final ServiceShape service;
    private final SymbolProvider symbolProvider;

    ClientGenerator(GenerationContext context, ServiceShape service) {
        this.context = context;
        this.symbolProvider = context.symbolProvider();
        this.model = context.model();
        this.service = service;
    }

    @Override
    public void run() {
        context.writerDelegator().useShapeWriter(service, this::generateService);
    }

    private void generateService(PythonWriter writer) {
        var serviceSymbol = symbolProvider.toSymbol(service);
        var configSymbol = CodegenUtils.getConfigSymbol(context.settings());
        var pluginSymbol = CodegenUtils.getPluginSymbol(context.settings());
        writer.addLogger();

        writer.openBlock("class $L:", "", serviceSymbol.getName(), () -> {
            var docs = service.getTrait(DocumentationTrait.class)
                    .map(StringTrait::getValue)
                    .orElse("Client for " + serviceSymbol.getName());
            String rstDocs =
                    MarkdownToRstDocConverter.getInstance().convertCommonmarkToRst(docs);
            writer.writeDocs(() -> {
                writer.write("""
                        $L

                        :param config: Optional configuration for the client. Here you can set things like the
                            endpoint for HTTP services or auth credentials.

                        :param plugins: A list of callables that modify the configuration dynamically. These
                            can be used to set defaults, for example.""", rstDocs);
            });

            var defaultPlugins = new LinkedHashSet<SymbolReference>();

            for (PythonIntegration integration : context.integrations()) {
                for (RuntimeClientPlugin runtimeClientPlugin : integration.getClientPlugins(context)) {
                    if (runtimeClientPlugin.matchesService(model, service)) {
                        runtimeClientPlugin.getPythonPlugin().ifPresent(defaultPlugins::add);
                    }
                }
            }

            writer.write("""
                    def __init__(self, config: $1T | None = None, plugins: list[$2T] | None = None):
                        self._config = config or $1T()

                        client_plugins: list[$2T] = [
                            $3C
                        ]
                        if plugins:
                            client_plugins.extend(plugins)

                        for plugin in client_plugins:
                            plugin(self._config)
                    """, configSymbol, pluginSymbol, writer.consumer(w -> writeDefaultPlugins(w, defaultPlugins)));

            var topDownIndex = TopDownIndex.of(model);
            var eventStreamIndex = EventStreamIndex.of(model);
            for (OperationShape operation : topDownIndex.getContainedOperations(service)) {
                if (eventStreamIndex.getInputInfo(operation).isPresent()
                        || eventStreamIndex.getOutputInfo(operation).isPresent()) {
                    generateEventStreamOperation(writer, operation);
                } else {
                    generateOperation(writer, operation);
                }
            }
        });
    }

    private void writeDefaultPlugins(PythonWriter writer, Collection<SymbolReference> plugins) {
        for (SymbolReference plugin : plugins) {
            writer.write("$T,", plugin);
        }
    }

    /**
     * Generates the function for a single operation.
     */
    private void generateOperation(PythonWriter writer, OperationShape operation) {
        var operationSymbol = symbolProvider.toSymbol(operation);
        var operationMethodSymbol = operationSymbol.expectProperty(OPERATION_METHOD);
        var pluginSymbol = CodegenUtils.getPluginSymbol(context.settings());

        var input = model.expectShape(operation.getInputShape());
        var inputSymbol = symbolProvider.toSymbol(input);

        var output = model.expectShape(operation.getOutputShape());
        var outputSymbol = symbolProvider.toSymbol(output);

        writer.pushState(new OperationSection(service, operation));
        writer.addStdlibImport("copy", "deepcopy");
        writer.putContext("input", inputSymbol);
        writer.putContext("output", outputSymbol);
        writer.putContext("plugin", pluginSymbol);
        writer.putContext("operationName", operationMethodSymbol.getName());
        writer.write("""
                async def ${operationName:L}(
                    self,
                    input: ${input:T},
                    plugins: list[${plugin:T}] | None = None
                ) -> ${output:T}:
                    ${C|}
                    return await pipeline(call)
                """,
                writer.consumer(w -> writeSharedOperationInit(w, operation, input)));
        writer.popState();
    }

    private void writeSharedOperationInit(PythonWriter writer, OperationShape operation, Shape input) {
        writer.writeDocs(() -> {
            var docs = writer.formatDocs(operation.getTrait(DocumentationTrait.class)
                    .map(StringTrait::getValue)
                    .orElse(String.format("Invokes the %s operation.",
                            operation.getId().getName())));

            var inputDocs = input.getTrait(DocumentationTrait.class)
                    .map(StringTrait::getValue)
                    .orElse("The operation's input.");

            writer.write("""
                    $L
                    """, docs);
            writer.write("");
            writer.write(":param input: $L", inputDocs);
            writer.write("");
            writer.write("""
                    :param plugins: A list of callables that modify the configuration dynamically.
                        Changes made by these plugins only apply for the duration of the operation
                        execution and will not affect any other operation invocations.
                        """);

        });

        var defaultPlugins = new LinkedHashSet<SymbolReference>();
        for (PythonIntegration integration : context.integrations()) {
            for (RuntimeClientPlugin runtimeClientPlugin : integration.getClientPlugins(context)) {
                if (runtimeClientPlugin.matchesOperation(model, service, operation)) {
                    runtimeClientPlugin.getPythonPlugin().ifPresent(defaultPlugins::add);
                }
            }
        }

        writer.putContext("operation", symbolProvider.toSymbol(operation));
        writer.addImport("smithy_core.aio.client", "ClientCall");
        writer.addImport("smithy_core.interceptors", "InterceptorChain");
        writer.addImport("smithy_core.types", "TypedProperties");
        writer.addImport("smithy_core.aio.client", "RequestPipeline");
        writer.addImport("smithy_core.exceptions", "ExpectationNotMetError");

        writer.write("""
                operation_plugins: list[Plugin] = [
                    $C
                ]
                if plugins:
                    operation_plugins.extend(plugins)
                config = deepcopy(self._config)
                for plugin in operation_plugins:
                    plugin(config)
                if config.protocol is None or config.transport is None:
                    raise ExpectationNotMetError("protocol and transport MUST be set on the config to make calls.")
                pipeline = RequestPipeline(
                    protocol=config.protocol,
                    transport=config.transport
                )
                call = ClientCall(
                    input=input,
                    operation=${operation:T},
                    context=TypedProperties({"config": config}),
                    interceptor=InterceptorChain(config.interceptors),
                    auth_scheme_resolver=config.auth_scheme_resolver,
                    supported_auth_schemes=config.auth_schemes,
                    endpoint_resolver=config.endpoint_resolver,
                    retry_strategy=config.retry_strategy,
                )
                """, writer.consumer(w -> writeDefaultPlugins(w, defaultPlugins)));

    }

    private void generateEventStreamOperation(PythonWriter writer, OperationShape operation) {
        writer.pushState(new OperationSection(service, operation));
        writer.addDependency(SmithyPythonDependency.SMITHY_CORE);
        var operationSymbol = symbolProvider.toSymbol(operation);
        writer.putContext("operation", operationSymbol);
        var operationMethodSymbol = operationSymbol.expectProperty(OPERATION_METHOD);
        writer.putContext("operationName", operationMethodSymbol.getName());
        var pluginSymbol = CodegenUtils.getPluginSymbol(context.settings());
        writer.putContext("plugin", pluginSymbol);

        var input = model.expectShape(operation.getInputShape());
        var inputSymbol = symbolProvider.toSymbol(input);
        writer.putContext("input", inputSymbol);

        var eventStreamIndex = EventStreamIndex.of(model);
        var inputStreamSymbol = eventStreamIndex.getInputInfo(operation)
                .map(EventStreamInfo::getEventStreamTarget)
                .map(symbolProvider::toSymbol);
        writer.putContext("inputStream", inputStreamSymbol.orElse(null));

        var output = model.expectShape(operation.getOutputShape());
        var outputSymbol = symbolProvider.toSymbol(output);
        writer.putContext("output", outputSymbol);

        var outputStreamSymbol = eventStreamIndex.getOutputInfo(operation)
                .map(EventStreamInfo::getEventStreamTarget)
                .map(symbolProvider::toSymbol);
        writer.putContext("outputStream", outputStreamSymbol.orElse(null));
        writer.putContext("outputStreamDeserializer",
                outputStreamSymbol
                        .map(s -> s.expectProperty(DESERIALIZER))
                        .orElse(null));

        // Note that we need to do a bunch of type ignoring here. This is ultimately because you can't
        // pass a union into something that expects a `type[T]` and there is no equivalent for unions.
        // The only other way to type those signatures would be as UnionType, but then you've broadened
        // the type declaration so much that it's no better than Any.
        if (inputStreamSymbol.isPresent()) {
            if (outputStreamSymbol.isPresent()) {
                writer.addImport("smithy_core.aio.eventstream", "DuplexEventStream");
                writer.write("""
                        async def ${operationName:L}(
                            self,
                            input: ${input:T},
                            plugins: list[${plugin:T}] | None = None
                        ) -> DuplexEventStream[${inputStream:T}, ${outputStream:T}, ${output:T}]:
                            ${C|}
                            return await pipeline.duplex_stream(
                                call,
                                ${inputStream:T},
                                ${outputStream:T},
                                ${outputStreamDeserializer:T}().deserialize
                            )
                        """,
                        writer.consumer(w -> writeSharedOperationInit(w, operation, input)));
            } else {
                writer.addImport("smithy_core.aio.eventstream", "InputEventStream");
                writer.write("""
                        async def ${operationName:L}(
                            self,
                            input: ${input:T},
                            plugins: list[${plugin:T}] | None = None
                        ) -> InputEventStream[${inputStream:T}, ${output:T}]:
                            ${C|}
                            return await pipeline.input_stream(
                                call,
                                ${inputStream:T}
                            )
                        """, writer.consumer(w -> writeSharedOperationInit(w, operation, input)));
            }
        } else {
            writer.addImport("smithy_core.aio.eventstream", "OutputEventStream");
            writer.write("""
                    async def ${operationName:L}(
                        self,
                        input: ${input:T},
                        plugins: list[${plugin:T}] | None = None
                    ) -> OutputEventStream[${outputStream:T}, ${output:T}]:
                        ${C|}
                        return await pipeline.output_stream(
                            call,
                            ${outputStream:T},
                            ${outputStreamDeserializer:T}().deserialize
                        )
                    """,
                    writer.consumer(w -> writeSharedOperationInit(w, operation, input)));
        }

        writer.popState();
    }
}
