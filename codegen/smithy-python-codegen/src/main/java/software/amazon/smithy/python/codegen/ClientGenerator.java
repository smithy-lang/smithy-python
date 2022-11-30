/*
 * Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License").
 * You may not use this file except in compliance with the License.
 * A copy of the License is located at
 *
 *   http://aws.amazon.com/apache2.0
 *
 * or in the "license" file accompanying this file. This file is distributed
 * on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
 * express or implied. See the License for the specific language governing
 * permissions and limitations under the License.
 */

package software.amazon.smithy.python.codegen;

import software.amazon.smithy.model.knowledge.TopDownIndex;
import software.amazon.smithy.model.shapes.OperationShape;
import software.amazon.smithy.model.shapes.ServiceShape;
import software.amazon.smithy.model.traits.DocumentationTrait;
import software.amazon.smithy.model.traits.StringTrait;

/**
 * Generates the actual client and implements operations.
 */
final class ClientGenerator implements Runnable {

    private final GenerationContext context;
    private final ServiceShape service;

    ClientGenerator(GenerationContext context, ServiceShape service) {
        this.context = context;
        this.service = service;
    }

    @Override
    public void run() {
        context.writerDelegator().useShapeWriter(service, this::generateService);
    }

    private void generateService(PythonWriter writer) {
        var serviceSymbol = context.symbolProvider().toSymbol(service);
        var configSymbol = CodegenUtils.getConfigSymbol(context.settings());
        var pluginSymbol = CodegenUtils.getPluginSymbol(context.settings());
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

            // TODO: generate default plugins
            writer.write("""
                    def __init__(self, config: $1T | None = None, plugins: list[$2T] | None = None):
                        self._config = config or $1T()

                        client_plugins: list[$2T] = [
                        ]
                        if plugins is not None:
                            client_plugins.extend(plugins)

                        for plugin in client_plugins:
                            plugin(self._config)
                    """, configSymbol, pluginSymbol);

            var topDownIndex = TopDownIndex.of(context.model());
            for (OperationShape operation : topDownIndex.getContainedOperations(service)) {
                generateOperation(writer, operation);
            }
        });
    }

    /**
     * Generates the function for a single operation.
     */
    private void generateOperation(PythonWriter writer, OperationShape operation) {
        var operationSymbol = context.symbolProvider().toSymbol(operation);
        var pluginSymbol = CodegenUtils.getPluginSymbol(context.settings());

        var input = context.model().expectShape(operation.getInputShape());
        var inputSymbol = context.symbolProvider().toSymbol(input);

        var output = context.model().expectShape(operation.getOutputShape());
        var outputSymbol = context.symbolProvider().toSymbol(output);

        writer.openBlock("async def $L(self, input: $T, plugins: list[$T] | None = None) -> $T:", "",
                operationSymbol.getName(), inputSymbol, pluginSymbol, outputSymbol, () -> {
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

                        :param plugins: A list of callables that modify the configuration dynamically.
                        Changes made by these plugins only apply for the duration of the operation
                        execution and will not affect any other operation invocations.""", docs, inputDocs);
            });

            writer.write("raise NotImplementedError()");
        });
    }
}
