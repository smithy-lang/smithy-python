/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen;

import static software.amazon.smithy.python.codegen.SymbolProperties.DESERIALIZER;
import static software.amazon.smithy.python.codegen.SymbolProperties.OPERATION_METHOD;

import java.util.ArrayList;
import java.util.Collection;
import java.util.HashSet;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.codegen.core.SymbolProvider;
import software.amazon.smithy.codegen.core.SymbolReference;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.knowledge.EventStreamIndex;
import software.amazon.smithy.model.knowledge.EventStreamInfo;
import software.amazon.smithy.model.knowledge.TopDownIndex;
import software.amazon.smithy.model.shapes.OperationShape;
import software.amazon.smithy.model.shapes.ServiceShape;
import software.amazon.smithy.model.shapes.StructureShape;
import software.amazon.smithy.model.traits.DocumentationTrait;
import software.amazon.smithy.model.traits.StringTrait;
import software.amazon.smithy.python.codegen.ParamTypeRenderer.Parameter;
import software.amazon.smithy.python.codegen.integrations.PythonIntegration;
import software.amazon.smithy.python.codegen.integrations.RuntimeClientPlugin;
import software.amazon.smithy.python.codegen.sections.ClientSetupSection;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Generates the actual client and implements operations.
 *
 * <p>Operations take the input's members as keyword-only parameters. The runtime
 * {@code client.py} carries no operation docs; those, and the typed signatures IDEs
 * show, are in the {@code client.pyi} stub, which has the same signatures.
 */
@SmithyInternalApi
final class ClientGenerator implements Runnable {

    private final GenerationContext context;
    private final Model model;
    private final ServiceShape service;
    private final SymbolProvider symbolProvider;
    private final ParamTypeRenderer typeRenderer;
    private final EventStreamIndex eventStreamIndex;

    ClientGenerator(GenerationContext context, ServiceShape service) {
        this.context = context;
        this.symbolProvider = context.symbolProvider();
        this.model = context.model();
        this.service = service;
        this.typeRenderer = new ParamTypeRenderer(context);
        this.eventStreamIndex = EventStreamIndex.of(model);
    }

    @Override
    public void run() {
        context.writerDelegator().useShapeWriter(service, this::generateService);
        context.writerDelegator()
                .useFileWriter(
                        String.format("src/%s/client.pyi", context.settings().moduleName()),
                        symbolProvider.toSymbol(service).getNamespace(),
                        this::generateStub);
    }

    private void generateService(PythonWriter writer) {
        var serviceSymbol = symbolProvider.toSymbol(service);
        writer.addLocallyDefinedSymbol(serviceSymbol);
        var pluginSymbol = CodegenUtils.getPluginSymbol(context.settings());
        writer.addLogger();

        // Services with a generated async config resolve lazily on first use;
        // the rest keep the synchronous constructor with old Config.
        var isAsyncConfig = CodegenUtils.getAsyncConfigSymbol(context.settings(), model).isPresent();
        var configSym = configSymbol();

        writer.openBlock("class $L($T):",
                "",
                serviceSymbol.getName(),
                RuntimeTypes.ASYNC_CLIENT,
                () -> {
                    writeServiceDocs(writer);

                    writer.addDependency(SmithyPythonDependency.SMITHY_CORE);
                    writer.addStdlibImport("typing", "Any");

                    // Collect service-scoped plugins applied once during setup.
                    var servicePlugins = new LinkedHashSet<SymbolReference>();
                    for (PythonIntegration integration : context.integrations()) {
                        for (RuntimeClientPlugin runtimeClientPlugin : integration.getClientPlugins(context)) {
                            if (runtimeClientPlugin.matchesService(model, service)) {
                                runtimeClientPlugin.getPythonPlugin().ifPresent(servicePlugins::add);
                            }
                        }
                    }

                    writer.addStdlibImport("copy", "deepcopy");

                    writer.write("""
                            ${3C|}
                                super().__init__()
                                self._config = config
                                self._plugins = plugins
                                self._client_plugins: list[$2T] = [
                                    ${4C|}
                                ]

                            async def _ensure_setup(self) -> $1T:
                                if not self._setup_done:
                                    async with self._derive_lock:
                                        if self._closed:
                                            raise RuntimeError(
                                                "Cannot invoke an operation on a client that has been closed."
                                            )
                                        if not self._setup_done:
                                            if self._config is None:
                                                ${5C|}
                                            else:
                                                # Copy so plugins don't mutate the caller's config.
                                                config = deepcopy(self._config)
                                            for plugin in self._client_plugins:
                                                plugin(config)
                                            if self._plugins:
                                                for plugin in self._plugins:
                                                    plugin(config)
                                            # Publish state only after setup fully succeeds, so a
                                            # failed _post_setup leaves the caller's config untouched
                                            # (no re-applied plugins) and the transport closeable.
                                            await self._post_setup(config)
                                            self._transport = config.transport
                                            self._config = config
                                            self._setup_done = True
                                assert self._config is not None
                                return self._config

                            async def _post_setup(self, config: $1T) -> None:
                                ${6C|}

                            async def _prepare_call[
                                I: $12T, O: $13T
                            ](
                                self,
                                # The operation method's locals(), i.e. its keyword arguments.
                                params: $14A[str, Any],
                                operation: $8T[I, O],
                                default_plugins: list[$2T],
                                plugins: list[$2T] | None,
                            ) -> tuple[$9T[Any, Any], $10T[I, O]]:
                                # Build the input first, so invalid parameters raise before
                                # any client setup.
                                input = operation.input_from_params(params)
                                if self._closed:
                                    raise RuntimeError(
                                        "Cannot invoke an operation on a client that has been closed."
                                    )
                                config = await self._ensure_setup()
                                if default_plugins or plugins:
                                    # Keep operation-plugin mutations scoped to this call.
                                    config = deepcopy(config)
                                    for plugin in default_plugins:
                                        plugin(config)
                                    if plugins:
                                        for plugin in plugins:
                                            plugin(config)
                                if (
                                    config.protocol is None
                                    or config.transport is None
                                    or config.endpoint_resolver is None
                                    or config.auth_scheme_resolver is None
                                    or config.auth_schemes is None
                                ):
                                    raise $7T(
                                        "protocol, transport, endpoint_resolver, auth_scheme_resolver,"
                                        " and auth_schemes MUST be set on the config to make calls."
                                    )
                                retry_strategy = await self._retry_strategy_resolver.resolve_retry_strategy(
                                    retry_strategy=config.retry_strategy,
                                    ${11C|}
                                )
                                return self._build_call(
                                    input,
                                    operation,
                                    config=config,
                                    retry_strategy=retry_strategy,
                                )
                            """,
                            configSym,
                            pluginSymbol,
                            writer.consumer(w -> writeConstructorHeader(w, serviceSymbol.getName())),
                            writer.consumer(w -> writeDefaultPlugins(w, servicePlugins)),
                            writer.consumer(w -> {
                                if (isAsyncConfig) {
                                    w.write("config = await $T.resolve()", configSym);
                                } else {
                                    w.write("config = $T()", configSym);
                                }
                            }),
                            writer.consumer(w -> {
                                w.pushState(new ClientSetupSection());
                                w.write("pass");
                                w.popState();
                            }),
                            RuntimeTypes.EXPECTATION_NOT_MET_ERROR,
                            RuntimeTypes.API_OPERATION,
                            RuntimeTypes.REQUEST_PIPELINE,
                            RuntimeTypes.CLIENT_CALL,
                            writer.consumer(w -> {
                                if (isAsyncConfig) {
                                    w.write("retry_mode=config.retry_mode,");
                                    w.write("max_attempts=config.max_attempts,");
                                }
                            }),
                            RuntimeTypes.SERIALIZEABLE_SHAPE,
                            RuntimeTypes.DESERIALIZEABLE_SHAPE,
                            RuntimeTypes.MAPPING);

                    for (OperationShape operation : operations()) {
                        writer.write("");
                        generateOperation(writer, operation);
                    }
                });
    }

    private void generateStub(PythonWriter writer) {
        var serviceSymbol = symbolProvider.toSymbol(service);
        writer.addLocallyDefinedSymbol(serviceSymbol);

        // Only the public surface: AsyncClient declares close and the context manager.
        writer.openBlock("class $L($T):", "", serviceSymbol.getName(), RuntimeTypes.ASYNC_CLIENT, () -> {
            writeServiceDocs(writer);
            writer.write("");
            writeConstructorHeader(writer, serviceSymbol.getName());
            writer.write("");
            for (OperationShape operation : operations()) {
                var parameters = typeRenderer.parameters(writer, input(operation), false);
                var streams = eventStreams(operation);
                writeSignature(writer, operation, parameters, returnType(writer, operation, streams, false));
                writer.indent();
                writeOperationDocs(writer, operation, parameters, streams);
                writer.dedent();
                writer.write("");
            }
        });
    }

    private Symbol configSymbol() {
        return CodegenUtils.getAsyncConfigSymbol(context.settings(), model)
                .orElse(CodegenUtils.getConfigSymbol(context.settings()));
    }

    // Shared by client.py and client.pyi so the stub can't drift from the constructor.
    private void writeConstructorHeader(PythonWriter writer, String clientName) {
        writer.write("""
                def __init__(
                    self,
                    config: $T | None = None,
                    plugins: list[$T] | None = None,
                ) -> None:
                    ${C|}""",
                configSymbol(),
                CodegenUtils.getPluginSymbol(context.settings()),
                writer.consumer(w -> writeConstructorDocs(w, clientName)));
    }

    private Collection<OperationShape> operations() {
        return TopDownIndex.of(model).getContainedOperations(service);
    }

    private void writeServiceDocs(PythonWriter writer) {
        var docs = service.getTrait(DocumentationTrait.class)
                .map(StringTrait::getValue)
                .orElse("Client for " + service.getId().getName());
        writer.writeDocs(docs, context);
    }

    private void writeDefaultPlugins(PythonWriter writer, Collection<SymbolReference> plugins) {
        for (SymbolReference plugin : plugins) {
            writer.write("$T,", plugin);
        }
    }

    private void writeConstructorDocs(PythonWriter writer, String clientName) {
        writer.writeMultiLineDocs(() -> {
            writer.write("""
                    Constructor for `$L`.

                    Args:
                        config:
                            Optional configuration for the client. Here you can set things like
                            the endpoint for HTTP services or auth credentials.
                        plugins:
                            A list of callables applied once to the client's base configuration.
                            Their changes are inherited by every operation invocation.
                    """, clientName);
        });
    }

    private StructureShape input(OperationShape operation) {
        return model.expectShape(operation.getInputShape(), StructureShape.class);
    }

    // Shared by client.py and client.pyi so their signatures can't drift apart.
    private void writeSignature(
            PythonWriter writer,
            OperationShape operation,
            List<Parameter> parameters,
            String returnType
    ) {
        writer.write("async def $L(", operationMethodName(operation));
        writer.indent();
        writer.write("self,");
        writer.write("*,");
        for (Parameter parameter : parameters) {
            if (parameter.required()) {
                writer.write("$L: $L,", parameter.name(), parameter.type());
            } else {
                writer.write("$L: $L | None = None,", parameter.name(), parameter.type());
            }
        }
        writer.write("plugins: list[$T] | None = None,", CodegenUtils.getPluginSymbol(context.settings()));
        writer.dedent();
        writer.write(") -> $L:", returnType);
    }

    private String operationMethodName(OperationShape operation) {
        return symbolProvider.toSymbol(operation).expectProperty(OPERATION_METHOD).getName();
    }

    /**
     * How an event stream operation returns its streams.
     */
    private enum StreamKind {
        INPUT(RuntimeTypes.INPUT_EVENT_STREAM,
                "input_stream",
                "An `InputEventStream` for client-to-server streaming."),
        OUTPUT(RuntimeTypes.OUTPUT_EVENT_STREAM,
                "output_stream",
                "An `OutputEventStream` for server-to-client streaming."),
        DUPLEX(RuntimeTypes.DUPLEX_EVENT_STREAM,
                "duplex_stream",
                "A `DuplexEventStream` for bidirectional streaming.");

        private final Symbol type;
        private final String pipelineMethod;
        private final String returnDocs;

        StreamKind(Symbol type, String pipelineMethod, String returnDocs) {
            this.type = type;
            this.pipelineMethod = pipelineMethod;
            this.returnDocs = returnDocs;
        }
    }

    /**
     * An operation's event stream union symbols, either of which may be null.
     */
    private record EventStreams(Symbol input, Symbol output) {
        /**
         * @return Returns how the operation returns its streams, or null if it has none.
         */
        StreamKind kind() {
            if (input != null && output != null) {
                return StreamKind.DUPLEX;
            } else if (input != null) {
                return StreamKind.INPUT;
            } else if (output != null) {
                return StreamKind.OUTPUT;
            }
            return null;
        }

        /**
         * @return Returns the streams in the order the stream type and pipeline method take them.
         */
        List<Symbol> symbols() {
            var symbols = new ArrayList<Symbol>();
            if (input != null) {
                symbols.add(input);
            }
            if (output != null) {
                symbols.add(output);
            }
            return symbols;
        }
    }

    private EventStreams eventStreams(OperationShape operation) {
        return new EventStreams(
                eventStreamIndex.getInputInfo(operation)
                        .map(EventStreamInfo::getEventStreamTarget)
                        .map(symbolProvider::toSymbol)
                        .orElse(null),
                eventStreamIndex.getOutputInfo(operation)
                        .map(EventStreamInfo::getEventStreamTarget)
                        .map(symbolProvider::toSymbol)
                        .orElse(null));
    }

    private String returnType(
            PythonWriter writer,
            OperationShape operation,
            EventStreams streams,
            boolean typeCheckingOnly
    ) {
        var symbolFormat = ParamTypeRenderer.symbolFormat(typeCheckingOnly);
        var output =
                writer.format(symbolFormat, symbolProvider.toSymbol(model.expectShape(operation.getOutputShape())));
        var kind = streams.kind();
        if (kind == null) {
            return output;
        }
        var arguments = new ArrayList<String>();
        for (Symbol stream : streams.symbols()) {
            arguments.add(writer.format(symbolFormat, stream));
        }
        arguments.add(output);
        return writer.format(symbolFormat + "[$L]", kind.type, String.join(", ", arguments));
    }

    /**
     * Generates the method for a single operation.
     *
     * <p>Model types appear only in annotations, so they are imported under
     * {@code TYPE_CHECKING}: importing the client doesn't build every model class.
     */
    private void generateOperation(PythonWriter writer, OperationShape operation) {
        var parameters = typeRenderer.parameters(writer, input(operation), true);
        var streams = eventStreams(operation);
        var names = new HashSet<>(PythonSymbolProvider.OPERATION_PARAMETER_NAMES);
        for (Parameter parameter : parameters) {
            names.add(parameter.name());
            // A parameter shadows any module-level name the body refers to.
            writer.addLocallyDefinedName(parameter.name());
        }
        writeSignature(writer, operation, parameters, returnType(writer, operation, streams, true));

        var pipeline = uniqueName("pipeline", names);
        var call = uniqueName("call", names);
        writer.indent();
        writer.write("""
                $L, $L = await self._prepare_call(
                    $L,
                    $T,
                    [
                        ${C|}
                    ],
                    plugins,
                )""",
                pipeline,
                call,
                paramsArgument(writer, parameters, names),
                symbolProvider.toSymbol(operation),
                writer.consumer(w -> writeDefaultOperationPlugins(w, operation)));

        var kind = streams.kind();
        if (kind == null) {
            writer.write("return await $L($L)", pipeline, call);
        } else {
            writer.addDependency(SmithyPythonDependency.SMITHY_AWS_CORE.withOptionalDependencies("eventstream"));
            var arguments = new ArrayList<String>();
            arguments.add(call);
            for (Symbol stream : streams.symbols()) {
                arguments.add(writer.format("$T", stream));
            }
            if (streams.output() != null) {
                arguments.add(writer.format("$T().deserialize", streams.output().expectProperty(DESERIALIZER)));
            }
            writer.write("return await $L.$L($L)", pipeline, kind.pipelineMethod, String.join(", ", arguments));
        }
        writer.dedent();
    }

    private String paramsArgument(PythonWriter writer, List<Parameter> parameters, Set<String> names) {
        if (!names.contains("locals")) {
            // Evaluated before any local is assigned, so it holds exactly the arguments.
            return "locals()";
        }
        // A parameter named `locals` shadows the builtin.
        var entries = new ArrayList<String>();
        for (Parameter parameter : parameters) {
            entries.add(writer.format("$S: $L", parameter.name(), parameter.name()));
        }
        return "{" + String.join(", ", entries) + "}";
    }

    private static String uniqueName(String base, Set<String> taken) {
        var name = base;
        while (taken.contains(name)) {
            name += "_";
        }
        return name;
    }

    private void writeOperationDocs(
            PythonWriter writer,
            OperationShape operation,
            List<Parameter> parameters,
            EventStreams streams
    ) {
        writer.writeMultiLineDocs(() -> {
            // formatDocs output is a format string ("$" is escaped), so it is written
            // directly rather than through $L, as models.pyi does.
            writer.write(writer.formatDocs(operation.getTrait(DocumentationTrait.class)
                    .map(StringTrait::getValue)
                    .orElse(String.format("Invokes the %s operation.", operation.getId().getName())),
                    context));
            writer.write("");
            writer.write("Args:");
            writer.indent();
            for (Parameter parameter : parameters) {
                parameter.member().getMemberTrait(model, DocumentationTrait.class).ifPresent(trait -> {
                    writer.write("$L:", parameter.name());
                    writer.indent();
                    writer.write(writer.formatDocs(trait.getValue(), context));
                    writer.dedent();
                });
            }
            writer.write("""
                    plugins:
                        A list of callables that modify the configuration dynamically.
                        Changes made by these plugins only apply for the duration of the
                        operation execution and will not affect any other operation
                        invocations.
                    """);
            writer.dedent();
            writer.write("Returns:");
            writer.indent();
            writer.write("$L", returnDocs(operation, streams));
            writer.dedent();
        });
    }

    private String returnDocs(OperationShape operation, EventStreams streams) {
        var kind = streams.kind();
        if (kind != null) {
            return kind.returnDocs;
        }
        var output = symbolProvider.toSymbol(model.expectShape(operation.getOutputShape()));
        return String.format("An instance of `%s`.", output.getName());
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
}
