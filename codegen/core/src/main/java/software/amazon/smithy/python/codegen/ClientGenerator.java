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
import java.util.function.Consumer;
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
    private final InputParams inputParams;
    private final String modelsNamespace;

    ClientGenerator(GenerationContext context, ServiceShape service) {
        this.context = context;
        this.symbolProvider = context.symbolProvider();
        this.model = context.model();
        this.service = service;
        this.inputParams = new InputParams(context);
        this.modelsNamespace = context.settings().moduleName() + ".models";
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
        // Model types in annotations are qualified with this module alias, so the
        // client refers to them without importing every model class eagerly.
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

        var output = model.expectShape(operation.getOutputShape());
        var outputSymbol = symbolProvider.toSymbol(output);

        // The output type is used ONLY in an annotation here. Import it under
        // TYPE_CHECKING and reference it by bare name (with future-annotations
        // deferring the annotations) so importing the client does not eagerly build
        // every model class. Operations are resolved through the models module when
        // invoked.
        writer.getImportContainer().enableFutureAnnotations();
        writer.getImportContainer()
                .addTypeCheckingImport(
                        outputSymbol.getNamespace(),
                        outputSymbol.getName(),
                        outputSymbol.getName());

        writer.putContext("operationName", operationMethodSymbol.getName());
        writer.putContext("operation", "_models." + operationSymbol.getName());
        writer.putContext("plugin", pluginSymbol);
        writeOverloadedOperation(writer,
                input,
                sync,
                outputSymbol.getName(),
                w -> writeOperationDocs(w, operation, output),
                """
                        return await self._invoke(
                            self._select_input(${operation:L}, args, kwargs),
                            ${operation:L},
                            [
                                ${C|}
                            ],
                            plugins,
                        )""",
                writer.consumer(w -> writeDefaultOperationPlugins(w, operation)));
    }

    /**
     * Writes an operation method: two overloads for callers and one implementation.
     *
     * <p>A caller passes either the whole request, positional-only so that it takes
     * no keyword away from the members, or the request's members as keyword
     * arguments. The keyword overload types them as {@code **kwargs} unpacking the
     * request's dictionary form, so editors find each argument's type and
     * documentation on that form's keys, which carry the members' full docs. The
     * keyword overload carries the operation's own documentation; {@code ClientBase}
     * copies it onto the implementation for {@code help()}. The implementation takes
     * either, and its body hands {@code args} and {@code kwargs} to
     * {@code _select_input}.
     *
     * <p>Expects {@code operationName}, {@code operation} and {@code plugin} in the
     * writer's context.
     *
     * @param writer The writer to write the method with.
     * @param input The operation's input shape.
     * @param sync Whether the method is for the sync client.
     * @param returns The method's return type, as written.
     * @param docs Writes the method's documentation.
     * @param body The async code template of the implementation's body.
     * @param bodyArgs The positional arguments of the body template.
     */
    private void writeOverloadedOperation(
            PythonWriter writer,
            Shape input,
            boolean sync,
            String returns,
            Consumer<PythonWriter> docs,
            String body,
            Object... bodyArgs
    ) {
        UnaryOperator<String> code = sync ? SyncVariant::toSyncCode : UnaryOperator.identity();
        // Aliased because a method defined in the class body shadows a module name
        // for the rest of the class, and an operation may be named Overload.
        writer.addStdlibImport("typing", "overload", "_overload");
        writer.addStdlibImport("typing", "Unpack", "_Unpack");
        writer.putContext("returns", returns);
        writer.putContext("request", requestType(writer, input, sync));
        writer.putContext("keywords", keywordsType(writer, input, sync));
        writer.putContext("docs", writer.consumer(docs));
        writer.putContext("body", writer.consumer(w -> w.write(code.apply(body), bodyArgs)));
        writer.write(code.apply("""
                @_overload
                async def ${operationName:L}(
                    self,
                    request: ${request:L},
                    /,
                    *,
                    plugins: list[${plugin:T}] | None = None,
                ) -> ${returns:L}: ...

                @_overload
                async def ${operationName:L}(
                    self,
                    /,
                    *,
                    plugins: list[${plugin:T}] | None = None,
                    **kwargs: _Unpack[${keywords:L}],
                ) -> ${returns:L}:
                    ${docs:C|}

                async def ${operationName:L}(
                    self,
                    /,
                    *args: object,
                    plugins: list[${plugin:T}] | None = None,
                    **kwargs: object,
                ) -> ${returns:L}:
                    ${body:C|}
                """));
    }

    /**
     * Spells the dictionary form an operation method's keyword overload unpacks.
     *
     * <p>An input with a streaming body has a second form whose body may also be an
     * async stream; the async client unpacks that one, and the sync client the plain
     * form, whose bodies it accepts.
     */
    private String keywordsType(PythonWriter writer, Shape input, boolean sync) {
        var params = !sync && inputParams.hasAsyncParams(input)
                ? inputParams.asyncParamsSymbol(input)
                : inputParams.paramsSymbol(input);
        return annotation(writer, params);
    }

    /**
     * Spells the type of an operation's whole request: its input model or its
     * dictionary form. An input with a streaming body has a second dictionary form
     * whose body may be an async stream, which only the async client accepts.
     */
    private String requestType(PythonWriter writer, Shape input, boolean sync) {
        var type = annotation(writer, symbolProvider.toSymbol(input))
                + " | " + annotation(writer, inputParams.paramsSymbol(input));
        if (!sync && inputParams.hasAsyncParams(input)) {
            type += " | " + annotation(writer, inputParams.asyncParamsSymbol(input));
        }
        return type;
    }

    /**
     * Refers to a type that is used only in an annotation, without importing it at
     * runtime: importing the client must not build model classes.
     *
     * <p>Models are reached through the {@code _models} module the client already
     * imports, which also keeps a shape named like another imported type (for example
     * {@code Plugin} or {@code Sequence}) from shadowing it. Everything else is
     * imported under {@code TYPE_CHECKING}.
     */
    private String annotation(PythonWriter writer, Symbol unmapped) {
        var symbol = writer.getSymbolMapper().apply(unmapped);
        if (symbol.getNamespace().equals(modelsNamespace)) {
            return "_models." + symbol.getName();
        }
        var imports = writer.getImportContainer();
        if (!symbol.getNamespace().isEmpty()) {
            imports.addTypeCheckingImport(symbol.getNamespace(), symbol.getName(), symbol.getName());
        }
        for (var reference : symbol.getReferences()) {
            var referenced = reference.getSymbol();
            if (!referenced.getNamespace().isEmpty()) {
                imports.addTypeCheckingImport(
                        referenced.getNamespace(),
                        referenced.getName(),
                        referenced.getName());
            }
        }
        return symbol.getName();
    }

    private void writeOperationDocs(PythonWriter writer, OperationShape operation, Shape output) {
        writeOperationDocs(writer, operation, output, null);
    }

    private void writeOperationDocs(
            PythonWriter writer,
            OperationShape operation,
            Shape output,
            String eventStreamOutputDocs
    ) {
        writer.writeMultiLineDocs(() -> {
            var operationDocs = writer.formatDocs(operation.getTrait(DocumentationTrait.class)
                    .map(StringTrait::getValue)
                    .orElse(String.format("Invokes the %s operation.",
                            operation.getId().getName())),
                    context);

            var outputSymbolName = symbolProvider.toSymbol(output).getName();
            var outputDocs = eventStreamOutputDocs != null ? eventStreamOutputDocs
                    : String.format("An instance of `%s`.", outputSymbolName);

            writer.write("$L\n", operationDocs);
            // The members are not repeated here: the keyword overload unpacks the
            // request's dictionary form, whose keys carry each member's full docs,
            // so an editor shows them from there. Only the method's own parameter
            // is documented.
            writer.write("Args:");
            writer.write("""
                        plugins:
                            A list of callables that modify the configuration dynamically.
                            Changes made by these plugins only apply for the duration of the
                            operation execution and will not affect any other operation
                            invocations.

                    Returns:
                        ${L|}
                    """, outputDocs);
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
        // Annotations must be deferred: the parameter types are not imported at runtime.
        writer.getImportContainer().enableFutureAnnotations();

        var eventStreamIndex = EventStreamIndex.of(model);
        var inputStreamSymbol = eventStreamIndex.getInputInfo(operation)
                .map(EventStreamInfo::getEventStreamTarget)
                .map(symbolProvider::toSymbol);
        writer.putContext("inputStream", inputStreamSymbol.orElse(null));

        var output = model.expectShape(operation.getOutputShape());
        var outputSymbol = symbolProvider.toSymbol(output);

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
        String returns;
        String outputDocs;
        String stream;
        if (inputStreamSymbol.isPresent() && outputStreamSymbol.isPresent()) {
            returns = writer.format("$T[$T, $T, $T]",
                    RuntimeTypes.DUPLEX_EVENT_STREAM,
                    inputStreamSymbol.get(),
                    outputStreamSymbol.get(),
                    outputSymbol);
            outputDocs = "An `AsyncDuplexEventStream` for bidirectional streaming.";
            stream = """
                    return await pipeline.duplex_stream(
                        call,
                        ${inputStream:T},
                        ${outputStream:T},
                        ${outputStreamDeserializer:T}().deserialize
                    )""";
        } else if (inputStreamSymbol.isPresent()) {
            returns = writer.format("$T[$T, $T]",
                    RuntimeTypes.INPUT_EVENT_STREAM,
                    inputStreamSymbol.get(),
                    outputSymbol);
            outputDocs = "An `AsyncInputEventStream` for client-to-server streaming.";
            stream = """
                    return await pipeline.input_stream(
                        call,
                        ${inputStream:T}
                    )""";
        } else {
            returns = writer.format("$T[$T, $T]",
                    RuntimeTypes.OUTPUT_EVENT_STREAM,
                    outputStreamSymbol.orElseThrow(),
                    outputSymbol);
            outputDocs = "An `AsyncOutputEventStream` for server-to-client streaming.";
            stream = """
                    return await pipeline.output_stream(
                        call,
                        ${outputStream:T},
                        ${outputStreamDeserializer:T}().deserialize
                    )""";
        }
        // Sync clients don't support event streams, so this is only ever async.
        writeOverloadedOperation(writer,
                input,
                false,
                returns,
                w -> writeOperationDocs(w, operation, output, outputDocs),
                """
                        pipeline, call = await self._prepare_call(
                            self._select_input(${operation:L}, args, kwargs),
                            ${operation:L},
                            [
                                ${C|}
                            ],
                            plugins,
                        )
                        """ + stream,
                writer.consumer(w -> writeDefaultOperationPlugins(w, operation)));
    }
}
