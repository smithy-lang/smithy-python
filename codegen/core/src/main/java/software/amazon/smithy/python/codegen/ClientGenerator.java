/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen;

import static software.amazon.smithy.python.codegen.SymbolProperties.DESERIALIZER;
import static software.amazon.smithy.python.codegen.SymbolProperties.OPERATION_METHOD;

import java.util.Collection;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.Map;
import java.util.function.UnaryOperator;
import java.util.stream.Collectors;
import software.amazon.smithy.codegen.core.Symbol;
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
import software.amazon.smithy.model.traits.RequiredTrait;
import software.amazon.smithy.model.traits.StringTrait;
import software.amazon.smithy.python.codegen.integrations.PythonIntegration;
import software.amazon.smithy.python.codegen.integrations.RuntimeClientPlugin;
import software.amazon.smithy.python.codegen.sections.ClientSetupSection;
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
        context.writerDelegator().useShapeWriter(service, writer -> generateService(writer, false));
        var mapper = SyncVariant.mapper(context.settings());
        var syncClient = mapper.apply(symbolProvider.toSymbol(service));
        context.writerDelegator()
                .useFileWriter(syncClient.getDefinitionFile(), syncClient.getNamespace(), writer -> {
                    writer.setSymbolMapper(mapper);
                    generateService(writer, true);
                });
        writeExports(syncClient, mapper);
    }

    private void writeExports(Symbol syncClient, UnaryOperator<Symbol> mapper) {
        var asyncConfig = CodegenUtils.getAsyncConfigSymbol(context.settings(), model);
        var asyncClient = symbolProvider.toSymbol(service).getName();
        var moduleName = context.settings().moduleName();
        var root = new LinkedHashMap<String, String>();
        root.put(syncClient.getName(), ".client");
        root.put(mapper.apply(asyncConfig).getName(), ".config");
        root.put(asyncClient, ".aio.client");
        root.put(asyncConfig.getName(), ".aio.config");
        writeExports("./src/" + moduleName + "/__init__.py", moduleName, root);
        var aio = new LinkedHashMap<String, String>();
        aio.put(asyncClient, ".client");
        aio.put(asyncConfig.getName(), ".config");
        writeExports("./src/" + moduleName + "/aio/__init__.py", moduleName + ".aio", aio);
    }

    // Lazily exported so importing the package imports neither client.
    private void writeExports(String file, String namespace, Map<String, String> exports) {
        context.writerDelegator().useFileWriter(file, namespace, writer -> {
            writer.addStdlibImport("typing", "TYPE_CHECKING");
            writer.addStdlibImport("typing", "Any");
            writer.addStdlibImport("importlib", "import_module");
            writer.write("""
                    if TYPE_CHECKING:
                        ${C|}

                    __all__ = [${L}]

                    _EXPORTS = {${L}}


                    def __getattr__(name: str) -> Any:
                        if name in _EXPORTS:
                            return getattr(import_module(_EXPORTS[name], __name__), name)
                        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

                    """,
                    writer.consumer(w -> exports.forEach(
                            (name, module) -> w.write("from $L import $L", module, name))),
                    exports.keySet().stream().map(n -> '"' + n + '"').collect(Collectors.joining(", ")),
                    exports.entrySet()
                            .stream()
                            .map(e -> '"' + e.getKey() + "\": \"" + e.getValue() + '"')
                            .collect(Collectors.joining(", ")));
        });
    }

    private void generateService(PythonWriter writer, boolean sync) {
        UnaryOperator<String> code = sync ? SyncVariant::toSyncCode : UnaryOperator.identity();
        var serviceSymbol = writer.getSymbolMapper().apply(symbolProvider.toSymbol(service));
        writer.addLocallyDefinedSymbol(serviceSymbol);
        writer.addImport(context.settings().moduleName(), "models", "_models");
        writer.addLogger();

        // AWS configs resolve from the environment; the rest are plain dataclasses.
        var isAwsConfig = CodegenUtils.isAwsService(context);
        var configSym = CodegenUtils.getAsyncConfigSymbol(context.settings(), context.model());

        writer.openBlock("class $L($T[$T]):",
                "",
                serviceSymbol.getName(),
                RuntimeTypes.ASYNC_CLIENT,
                configSym,
                () -> {
                    var docs = service.getTrait(DocumentationTrait.class)
                            .map(StringTrait::getValue)
                            .orElse("Client for " + service.getId().getName());
                    writer.writeDocs(docs, context);
                    writer.addDependency(SmithyPythonDependency.SMITHY_CORE);

                    // Collect service-scoped plugins applied once during setup.
                    var servicePlugins = new LinkedHashSet<SymbolReference>();
                    for (PythonIntegration integration : context.integrations()) {
                        for (RuntimeClientPlugin runtimeClientPlugin : integration.getClientPlugins(context)) {
                            if (runtimeClientPlugin.matchesService(model, service)) {
                                runtimeClientPlugin.getPythonPlugin().ifPresent(servicePlugins::add);
                            }
                        }
                    }
                    if (!servicePlugins.isEmpty()) {
                        writer.write("""
                                _client_plugins = (
                                    ${C|}
                                )
                                """, writer.consumer(w -> writeDefaultPlugins(w, servicePlugins)));
                    }

                    var topDownIndex = TopDownIndex.of(model);
                    var eventStreamIndex = EventStreamIndex.of(model);
                    for (OperationShape operation : topDownIndex.getContainedOperations(service)) {
                        if (eventStreamIndex.getInputInfo(operation).isPresent()
                                || eventStreamIndex.getOutputInfo(operation).isPresent()) {
                            // Sync clients don't support event streams.
                            if (!sync) {
                                generateEventStreamOperation(writer, operation);
                            }
                        } else {
                            generateOperation(writer, operation, sync);
                        }
                    }

                    writer.write(code.apply("""
                            async def _new_config(self) -> $T:
                                return $L
                            """),
                            configSym,
                            isAwsConfig
                                    ? writer.format(code.apply("await $T.resolve()"), configSym)
                                    : writer.format("$T()", configSym));
                    writer.pushState(new ClientSetupSection(sync, configSym));
                    writer.popState();
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
    private void generateOperation(PythonWriter writer, OperationShape operation, boolean sync) {
        var operationSymbol = symbolProvider.toSymbol(operation);
        var operationMethodSymbol = operationSymbol.expectProperty(OPERATION_METHOD);
        var pluginSymbol = CodegenUtils.getPluginSymbol(context.settings());

        var input = model.expectShape(operation.getInputShape());
        var inputSymbol = symbolProvider.toSymbol(input);

        var output = model.expectShape(operation.getOutputShape());
        var outputSymbol = symbolProvider.toSymbol(output);

        // Input/output types are used ONLY in annotations here. Import them under
        // TYPE_CHECKING and reference by bare name (with future-annotations deferring
        // the annotations) so importing the client does not eagerly build every model
        // class. Operations are resolved through the models module when invoked.
        writer.getImportContainer().enableFutureAnnotations();
        writer.getImportContainer()
                .addTypeCheckingImport(
                        inputSymbol.getNamespace(),
                        inputSymbol.getName(),
                        inputSymbol.getName());
        writer.getImportContainer()
                .addTypeCheckingImport(
                        outputSymbol.getNamespace(),
                        outputSymbol.getName(),
                        outputSymbol.getName());

        writer.putContext("input", inputSymbol.getName());
        writer.putContext("output", outputSymbol.getName());
        writer.putContext("plugin", pluginSymbol);
        writer.putContext("operationName", operationMethodSymbol.getName());
        writer.putContext("operation", "_models." + operationSymbol.getName());
        // Sync callers may omit an input that has no required members.
        var optionalInput = sync && input.members().stream().noneMatch(m -> m.hasTrait(RequiredTrait.class));
        writer.putContext("optionalInput", optionalInput);
        var template =
                """
                        async def ${operationName:L}(
                            self,
                            ${?optionalInput}input: ${input:L} | None = None,${/optionalInput}${^optionalInput}input: ${input:L},${/optionalInput}
                            plugins: list[${plugin:T}] | None = None
                        ) -> ${output:L}:
                            ${?docs}${docs:C|}
                            ${/docs}return await self._invoke(
                                input,
                                ${operation:L},
                                [
                                    ${C|}
                                ],
                                plugins,
                            )
                        """;
        writer.putContext("docs", writer.consumer(w -> writeOperationDocs(w, operation, input, output)));
        writer.write(sync ? SyncVariant.toSyncCode(template) : template,
                writer.consumer(w -> writeDefaultOperationPlugins(w, operation)));
    }

    private void writeOperationDocs(PythonWriter writer, OperationShape operation, Shape input, Shape output) {
        writeOperationDocs(writer, operation, input, output, null);
    }

    private void writeOperationDocs(
            PythonWriter writer,
            OperationShape operation,
            Shape input,
            Shape output,
            String eventStreamOutputDocs
    ) {
        writer.writeMultiLineDocs(() -> {
            var operationDocs = writer.formatDocs(operation.getTrait(DocumentationTrait.class)
                    .map(StringTrait::getValue)
                    .orElse(String.format("Invokes the %s operation.",
                            operation.getId().getName())),
                    context);

            var inputSymbolName = symbolProvider.toSymbol(input).getName();
            var outputSymbolName = symbolProvider.toSymbol(output).getName();
            var inputDocs = String.format("An instance of `%s`.", inputSymbolName);
            var outputDocs = eventStreamOutputDocs != null ? eventStreamOutputDocs
                    : String.format("An instance of `%s`.", outputSymbolName);

            writer.write("""
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
    }

    // Operation-scoped default plugins, prepended to the caller's plugins for a
    // single call. Service-scoped plugins live in self._client_plugins instead.
    private void writeDefaultOperationPlugins(PythonWriter writer, OperationShape operation) {
        var defaultPlugins = new LinkedHashSet<SymbolReference>();
        for (PythonIntegration integration : context.integrations()) {
            for (RuntimeClientPlugin runtimeClientPlugin : integration.getClientPlugins(context)) {
                if (runtimeClientPlugin.matchesOperation(model, service, operation)) {
                    runtimeClientPlugin.getPythonPlugin().ifPresent(defaultPlugins::add);
                }
            }
        }
        writeDefaultPlugins(writer, defaultPlugins);
    }

    private void generateEventStreamOperation(PythonWriter writer, OperationShape operation) {
        writer.addDependency(SmithyPythonDependency.SMITHY_CORE);
        writer.addDependency(SmithyPythonDependency.SMITHY_AWS_CORE.withOptionalDependencies("eventstream"));
        var operationSymbol = symbolProvider.toSymbol(operation);
        writer.putContext("operation", "_models." + operationSymbol.getName());
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
                writer.putContext("duplexEventStream", RuntimeTypes.DUPLEX_EVENT_STREAM);
                var outputDocs = "An `AsyncDuplexEventStream` for bidirectional streaming.";
                writer.write("""
                        async def ${operationName:L}(
                            self,
                            input: ${input:T},
                            plugins: list[${plugin:T}] | None = None
                        ) -> ${duplexEventStream:T}[${inputStream:T}, ${outputStream:T}, ${output:T}]:
                            ${C|}
                            pipeline, call = await self._prepare_call(
                                input,
                                ${operation:L},
                                [
                                    ${C|}
                                ],
                                plugins,
                            )
                            return await pipeline.duplex_stream(
                                call,
                                ${inputStream:T},
                                ${outputStream:T},
                                ${outputStreamDeserializer:T}().deserialize
                            )
                        """,
                        writer.consumer(w -> writeOperationDocs(w, operation, input, output, outputDocs)),
                        writer.consumer(w -> writeDefaultOperationPlugins(w, operation)));
            } else {
                writer.putContext("inputEventStream", RuntimeTypes.INPUT_EVENT_STREAM);
                var outputDocs = "An `AsyncInputEventStream` for client-to-server streaming.";
                writer.write("""
                        async def ${operationName:L}(
                            self,
                            input: ${input:T},
                            plugins: list[${plugin:T}] | None = None
                        ) -> ${inputEventStream:T}[${inputStream:T}, ${output:T}]:
                            ${C|}
                            pipeline, call = await self._prepare_call(
                                input,
                                ${operation:L},
                                [
                                    ${C|}
                                ],
                                plugins,
                            )
                            return await pipeline.input_stream(
                                call,
                                ${inputStream:T}
                            )
                        """,
                        writer.consumer(w -> writeOperationDocs(w, operation, input, output, outputDocs)),
                        writer.consumer(w -> writeDefaultOperationPlugins(w, operation)));
            }
        } else {
            writer.putContext("outputEventStream", RuntimeTypes.OUTPUT_EVENT_STREAM);
            var outputDocs = "An `AsyncOutputEventStream` for server-to-client streaming.";
            writer.write("""
                    async def ${operationName:L}(
                        self,
                        input: ${input:T},
                        plugins: list[${plugin:T}] | None = None
                    ) -> ${outputEventStream:T}[${outputStream:T}, ${output:T}]:
                        ${C|}
                        pipeline, call = await self._prepare_call(
                            input,
                            ${operation:L},
                            [
                                ${C|}
                            ],
                            plugins,
                        )
                        return await pipeline.output_stream(
                            call,
                            ${outputStream:T},
                            ${outputStreamDeserializer:T}().deserialize
                        )
                    """,
                    writer.consumer(w -> writeOperationDocs(w, operation, input, output, outputDocs)),
                    writer.consumer(w -> writeDefaultOperationPlugins(w, operation)));
        }
    }
}
