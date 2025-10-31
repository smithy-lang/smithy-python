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
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.utils.SmithyInternalApi;
import software.amazon.smithy.utils.StringUtils;

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
            writer.writeDocs(docs, context);

            var defaultPlugins = new LinkedHashSet<SymbolReference>();

            for (PythonIntegration integration : context.integrations()) {
                for (RuntimeClientPlugin runtimeClientPlugin : integration.getClientPlugins(context)) {
                    if (runtimeClientPlugin.matchesService(model, service)) {
                        runtimeClientPlugin.getPythonPlugin().ifPresent(defaultPlugins::add);
                    }
                }
            }

            writer.addDependency(SmithyPythonDependency.SMITHY_CORE);
            writer.addImport("smithy_core.retries", "RetryStrategyResolver");
            writer.write("""
                    def __init__(self, config: $1T | None = None, plugins: list[$2T] | None = None):
                        $3C
                        self._config = config or $1T()

                        client_plugins: list[$2T] = [
                            $4C
                        ]
                        if plugins:
                            client_plugins.extend(plugins)

                        for plugin in client_plugins:
                            plugin(self._config)

                        self._retry_strategy_resolver = RetryStrategyResolver()
                    """,
                    configSymbol,
                    pluginSymbol,
                    writer.consumer(w -> writeConstructorDocs(w, serviceSymbol.getName())),
                    writer.consumer(w -> writeDefaultPlugins(w, defaultPlugins)));

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
     * Generates docstring for client constructor.
     */
    private void writeConstructorDocs(PythonWriter writer, String clientName) {
        writer.writeDocs(() -> {
            writer.writeInline("""
                    Constructor for `$L`.

                    Args:
                        config:
                            Optional configuration for the client. Here you can set things like
                            the endpoint for HTTP services or auth credentials.
                        plugins:
                            A list of callables that modify the configuration dynamically. These
                            can be used to set defaults, for example.
                    """, clientName);
        });
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
                writer.consumer(w -> writeSharedOperationInit(w, operation, input, output)));
        writer.popState();
    }

    private void writeSharedOperationInit(PythonWriter writer, OperationShape operation, Shape input, Shape output) {
        writeSharedOperationInit(writer, operation, input, output, null);
    }

    private void writeSharedOperationInit(
            PythonWriter writer,
            OperationShape operation,
            Shape input,
            Shape output,
            String customReturnDocs
    ) {
        writer.writeDocs(() -> {
            var inputSymbolName = symbolProvider.toSymbol(input).getName();
            var outputSymbolName = symbolProvider.toSymbol(output).getName();

            var operationDocs = writer.formatDocs(operation.getTrait(DocumentationTrait.class)
                    .map(StringTrait::getValue)
                    .orElse(String.format("Invokes the %s operation.",
                            operation.getId().getName())),
                    context);

            var inputDocs = String.format("An instance of `%s`.", inputSymbolName);
            var outputDocs = customReturnDocs != null ? customReturnDocs
                    : String.format("An instance of `%s`.", outputSymbolName);

            writer.writeInline("""
                    $L

                    Args:
                        input:
                            $L
                        plugins:
                            A list of callables that modify the configuration dynamically.
                            Changes made by these plugins only apply for the duration of the
                            operation execution and will not affect any other operation
                            invocations.

                    Returns:
                        ${L|}
                    """, operationDocs, inputDocs, outputDocs);
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
        writer.addImport("smithy_core.retries", "RetryStrategyOptions");
        writer.addImport("smithy_core.interfaces.retries", "RetryStrategy");
        writer.addStdlibImport("copy", "deepcopy");

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

                retry_strategy = await self._retry_strategy_resolver.resolve_retry_strategy(
                    retry_strategy=config.retry_strategy
                )

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
                    retry_strategy=retry_strategy,
                )
                """, writer.consumer(w -> writeDefaultPlugins(w, defaultPlugins)));

    }

    private void generateEventStreamOperation(PythonWriter writer, OperationShape operation) {
        writer.pushState(new OperationSection(service, operation));
        writer.addDependency(SmithyPythonDependency.SMITHY_CORE);
        writer.addDependency(SmithyPythonDependency.SMITHY_AWS_CORE.withOptionalDependencies("eventstream"));
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
                var returnDocs = generateEventStreamReturnDocs(
                        "DuplexEventStream",
                        inputStreamSymbol.get().getName(),
                        outputStreamSymbol.get().getName(),
                        outputSymbol.getName());
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
                        writer.consumer(w -> writeSharedOperationInit(w, operation, input, output, returnDocs)));
            } else {
                writer.addImport("smithy_core.aio.eventstream", "InputEventStream");
                var returnDocs = generateEventStreamReturnDocs(
                        "InputEventStream",
                        inputStreamSymbol.get().getName(),
                        null,
                        outputSymbol.getName());
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
                        """, writer.consumer(w -> writeSharedOperationInit(w, operation, input, output, returnDocs)));
            }
        } else {
            writer.addImport("smithy_core.aio.eventstream", "OutputEventStream");
            var returnDocs = generateEventStreamReturnDocs(
                    "OutputEventStream",
                    null,
                    outputStreamSymbol.get().getName(),
                    outputSymbol.getName());
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
                    writer.consumer(w -> writeSharedOperationInit(w, operation, input, output, returnDocs)));
        }

        writer.popState();
    }

    /**
     * Generates documentation for event stream return types.
     */
    private String generateEventStreamReturnDocs(
            String containerType,
            String inputStreamName,
            String outputStreamName,
            String outputName
    ) {
        String docs = switch (containerType) {
            case "DuplexEventStream" -> String.format(
                    "A `DuplexEventStream` for bidirectional streaming of `%s` and `%s` events with initial `%s` response.",
                    inputStreamName,
                    outputStreamName,
                    outputName);
            case "InputEventStream" -> String.format(
                    "An `InputEventStream` for client-to-server streaming of `%s` events with final `%s` response.",
                    inputStreamName,
                    outputName);
            case "OutputEventStream" -> String.format(
                    "An `OutputEventStream` for server-to-client streaming of `%s` events with initial `%s` response.",
                    outputStreamName,
                    outputName);
            default -> throw new IllegalArgumentException("Unknown event stream type: " + containerType);
        };
        // Subtract 12 chars for 3 indentation (4 spaces each)
        String wrapped = StringUtils.wrap(
                docs,
                CodegenUtils.MAX_PREFERRED_LINE_LENGTH - 12);
        // Add additional indentation (4 spaces) to continuation lines for proper Google-style formatting
        return wrapped.replace("\n", "\n    ");
    }
}
