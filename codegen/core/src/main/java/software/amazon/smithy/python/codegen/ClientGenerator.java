/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen;

import java.util.Collection;
import java.util.LinkedHashSet;
import java.util.List;
import software.amazon.smithy.codegen.core.SymbolProvider;
import software.amazon.smithy.codegen.core.SymbolReference;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.knowledge.EventStreamIndex;
import software.amazon.smithy.model.knowledge.TopDownIndex;
import software.amazon.smithy.model.shapes.OperationShape;
import software.amazon.smithy.model.shapes.ServiceShape;
import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.model.traits.DocumentationTrait;
import software.amazon.smithy.model.traits.StringTrait;
import software.amazon.smithy.python.codegen.integrations.PythonIntegration;
import software.amazon.smithy.python.codegen.integrations.RuntimeClientPlugin;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Generates the actual client and implements operations.
 */
@SmithyInternalApi
final class ClientGenerator implements Runnable {

    private final GenerationContext context;
    private final ServiceShape service;
    private final SymbolProvider symbolProvider;
    private final Model model;

    ClientGenerator(GenerationContext context, ServiceShape service) {
        this.context = context;
        this.service = service;
        this.symbolProvider = context.symbolProvider();
        this.model = context.model();
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

        writer.addStdlibImport("typing", "TypeVar");
        writer.write("""
                Input = TypeVar("Input")
                Output = TypeVar("Output")
                """);

        // TODO: Extend a base client class
        writer.openBlock("class $L:", "", serviceSymbol.getName(), () -> {
            var docs = service.getTrait(DocumentationTrait.class)
                    .map(StringTrait::getValue)
                    .orElse("Client for " + serviceSymbol.getName());
            writer.writeDocs(() -> {
                writer.write("""
                        $L

                        :param config: Optional configuration for the client. Here you can set things like the
                        endpoint for HTTP services or auth credentials.

                        :param plugins: A list of callables that modify the configuration dynamically. These
                        can be used to set defaults, for example.""", docs);
            });

            var defaultPlugins = new LinkedHashSet<SymbolReference>();

            for (PythonIntegration integration : context.integrations()) {
                for (RuntimeClientPlugin runtimeClientPlugin : integration.getClientPlugins(context)) {
                    if (runtimeClientPlugin.matchesService(model, service)) {
                        runtimeClientPlugin.getPythonPlugin().ifPresent(defaultPlugins::add);
                    }
                }
            }

            // TODO: Set default client protocol
            // Need some mapping between protocol shape and the python implementation
            // For now, test with restjson
            writer.addImport("smithy_core.protocols", "RestJsonClientProtocol");
            writer.write("protocol = RestJsonClientProtocol");

            writer.addImport("smithy_core.type_registry", "TypeRegistry");
            writer.write("""
                    type_registry = TypeRegistry({
                        $C
                    })
                    """, writer.consumer(this::writeErrorTypeRegistry));

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
                    // TODO: event streaming operations
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
     * Generates the type-registry for the modeled errors of the service.
     * TODO: Implicit errors
     */
    private void writeErrorTypeRegistry(PythonWriter writer) {
        List<ShapeId> errors = service.getErrors();
        if (!errors.isEmpty()) {
            writer.addImport("smithy_core.shapes", "ShapeID");
        }
        for (var error : errors) {
            var errSymbol = symbolProvider.toSymbol(model.expectShape(error));
            writer.write("ShapeID($S): $T,", error, errSymbol);
        }
    }

    /**
     * Generates the function for a single operation.
     */
    private void generateOperation(PythonWriter writer, OperationShape operation) {
        var operationSymbol = symbolProvider.toSymbol(operation);
        var operationMethodSymbol = operationSymbol.expectProperty(SymbolProperties.OPERATION_METHOD);
        var pluginSymbol = CodegenUtils.getPluginSymbol(context.settings());

        var input = model.expectShape(operation.getInputShape());
        var inputSymbol = symbolProvider.toSymbol(input);

        var output = model.expectShape(operation.getOutputShape());
        var outputSymbol = symbolProvider.toSymbol(output);

        writer.openBlock("async def $L(self, input: $T, plugins: list[$T] | None = None) -> $T:",
                "",
                operationMethodSymbol.getName(),
                inputSymbol,
                pluginSymbol,
                outputSymbol,
                () -> {
                    writeOperationDocs(writer, operation, input);

                    if (context.protocolGenerator() == null) {
                        writer.write("raise NotImplementedError()");
                    } else {
                        // TODO: override config
                        // TODO: try/except with error
                        // TODO: align with implementation of call() in the base client class (when its created)
                        writer.write("return await call(input, $T)", operationSymbol);
                    }
                });

    }

    private void writeOperationDocs(PythonWriter writer, OperationShape operation, Shape input) {
        writer.writeDocs(() -> {
            var docs = operation.getTrait(DocumentationTrait.class)
                    .map(StringTrait::getValue)
                    .orElse(String.format("Invokes the %s operation.", operation.getId().getName()));

            var inputDocs = input.getTrait(DocumentationTrait.class)
                    .map(StringTrait::getValue)
                    .orElse("The operation's input.");

            writer.write("""
                    $L

                    :param input: $L
                    """, docs, inputDocs);
        });
    }
}
