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
        context.writerDelegator().useShapeWriter(service, this::generateService);
    }

    private void generateService(PythonWriter writer) {
        var serviceSymbol = symbolProvider.toSymbol(service);
        writer.addLocallyDefinedSymbol(serviceSymbol);
        var configSymbol = CodegenUtils.getConfigSymbol(context.settings());
        var pluginSymbol = CodegenUtils.getPluginSymbol(context.settings());
        writer.addLogger();

        writer.openBlock("class $L:", "", serviceSymbol.getName(), () -> {
            var docs = service.getTrait(DocumentationTrait.class)
                    .map(StringTrait::getValue)
                    .orElse("Client for " + service.getId().getName());
            writer.writeDocs(docs, context);

            writer.addDependency(SmithyPythonDependency.SMITHY_CORE);
            // Services with a generated async config resolve lazily on first use;
            // the rest keep the synchronous constructor with old Config.
            var asyncConfigSymbol = CodegenUtils.getAsyncConfigSymbol(context.settings(), context.model());

            // Collect service-scoped plugins applied once during setup.
            var servicePlugins = new LinkedHashSet<SymbolReference>();
            for (PythonIntegration integration : context.integrations()) {
                for (RuntimeClientPlugin runtimeClientPlugin : integration.getClientPlugins(context)) {
                    if (runtimeClientPlugin.matchesService(model, service)) {
                        runtimeClientPlugin.getPythonPlugin().ifPresent(servicePlugins::add);
                    }
                }
            }

            // Resolve or construct the config lazily before applying plugins once.
            var isAsyncConfig = asyncConfigSymbol.isPresent();
            var configSym = asyncConfigSymbol.orElse(configSymbol);
            writer.addStdlibImport("asyncio");
            // Imported privately: operation methods call it alongside modeled parameters.
            writer.addStdlibImport("copy", "deepcopy", "_deepcopy");

            writer.write("""
                    def __init__(
                        self,
                        config: $1T | None = None,
                        plugins: list[$2T] | None = None,
                    ):
                        ${3C|}
                        self._config = config
                        self._plugins = plugins
                        self._derive_lock = asyncio.Lock()
                        self._setup_done = False
                        self._closed = False
                        self._retry_strategy_resolver = $4T()
                        self._client_plugins: list[$2T] = [
                            ${5C|}
                        ]

                    async def _ensure_setup(self) -> None:
                        if not self._setup_done:
                            async with self._derive_lock:
                                if not self._setup_done:
                                    if self._config is None:
                                        ${6C|}
                                    else:
                                        # Copy so plugins don't mutate the caller's config.
                                        config = _deepcopy(self._config)
                                    for plugin in self._client_plugins:
                                        plugin(config)
                                    if self._plugins:
                                        for plugin in self._plugins:
                                            plugin(config)
                                    self._config = config
                                    ${7C|}
                                    self._setup_done = True
                    """,
                    configSym,
                    pluginSymbol,
                    writer.consumer(w -> writeConstructorDocs(w, serviceSymbol.getName())),
                    RuntimeTypes.RETRY_STRATEGY_RESOLVER,
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
                        w.popState();
                    }));

            writer.addStdlibImport("typing", "Any");
            writer.addStdlibImport("typing", "Self");
            writer.write("""

                    async def close(self) -> None:
                        \"\"\"Close this client and any resources held by its transport.\"\"\"
                        if self._closed:
                            return
                        async with self._derive_lock:
                            if self._closed:
                                return
                            self._closed = True
                            if self._setup_done and self._config is not None:
                                await $1T(self._config.transport)

                    async def __aenter__(self) -> Self:
                        if self._closed:
                            raise RuntimeError("Cannot enter a client that has been closed.")
                        return self

                    async def __aexit__(
                        self,
                        exc_type: Any,
                        exc_value: Any,
                        traceback: Any,
                    ) -> None:
                        await self.close()
                    """,
                    RuntimeTypes.ASYNC_CLOSE);

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
            writer.write("$T,", privateAlias(plugin));
        }
    }

    /**
     * Re-aliases a plugin reference so it imports under a leading underscore.
     *
     * <p>Operation-scoped plugins are referenced from inside generated operation methods,
     * whose other names are modeled. Importing them privately means a modeled member named
     * {@code user_agent_plugin} can't shadow one, and, more importantly, that no member's
     * keyword depends on which plugins happened to match its operation.
     */
    private static SymbolReference privateAlias(SymbolReference plugin) {
        return plugin.toBuilder().alias("_" + plugin.getAlias()).build();
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

    /**
     * Generates the function for a single operation.
     */
    private void generateOperation(PythonWriter writer, OperationShape operation) {
        var operationSymbol = symbolProvider.toSymbol(operation);
        var operationMethodSymbol = operationSymbol.expectProperty(OPERATION_METHOD);

        var output = model.expectShape(operation.getOutputShape());
        var outputSymbol = symbolProvider.toSymbol(output);

        writer.putContext("output", outputSymbol);
        writer.putContext("operationName", operationMethodSymbol.getName());
        writer.putContext("parameters",
                writer.consumer(new OperationInputGenerator(context, operation)::writeParameters));
        writer.write("""
                async def ${operationName:L}(
                    ${parameters:C|}
                ) -> ${output:T}:
                    ${C|}
                    return await _pipeline(_call)
                """,
                writer.consumer(w -> writeSharedOperationInit(w, operation, output, null)));
    }

    private void writeSharedOperationInit(
            PythonWriter writer,
            OperationShape operation,
            Shape output,
            String eventStreamOutputDocs
    ) {
        var operationInput = new OperationInputGenerator(context, operation);
        writer.writeMultiLineDocs(() -> {
            var operationDocs = writer.formatDocs(operation.getTrait(DocumentationTrait.class)
                    .map(StringTrait::getValue)
                    .orElse(String.format("Invokes the %s operation.",
                            operation.getId().getName())),
                    context);

            var outputSymbolName = symbolProvider.toSymbol(output).getName();
            var outputDocs = eventStreamOutputDocs != null ? eventStreamOutputDocs
                    : String.format("An instance of `%s`.", outputSymbolName);

            writer.write("""
                    $L

                    Args:
                        ${C|}
                        plugins:
                            A list of callables that modify the configuration dynamically.
                            Changes made by these plugins only apply for the duration of the
                            operation execution and will not affect any other operation
                            invocations.

                    Returns:
                        ${L|}
                    """, operationDocs, writer.consumer(operationInput::writeDocs), outputDocs);
        });

        operationInput.writeInput(writer);

        // Operation-scoped plugins are collected per-operation. Service-scoped plugins
        // are stored in self._client_plugins (built once in __init__).
        var defaultPlugins = new LinkedHashSet<SymbolReference>();
        for (PythonIntegration integration : context.integrations()) {
            for (RuntimeClientPlugin runtimeClientPlugin : integration.getClientPlugins(context)) {
                if (runtimeClientPlugin.matchesOperation(model, service, operation)) {
                    runtimeClientPlugin.getPythonPlugin().ifPresent(defaultPlugins::add);
                }
            }
        }

        writer.putContext("operation", symbolProvider.toSymbol(operation));
        // Every local below is underscore-prefixed so that it can't collide with a modeled
        // member's keyword. See OperationInputGenerator.RESERVED before adding a new one.
        writer.write(
                """
                        if self._closed:
                            raise RuntimeError(
                                "Cannot invoke an operation on a client that has been closed."
                            )

                        _operation_plugins: list[$8T] = [
                            $1C
                        ]
                        if plugins:
                            _operation_plugins.extend(plugins)
                        await self._ensure_setup()
                        assert self._config is not None
                        if _operation_plugins:
                            # Keep operation-plugin mutations scoped to this call.
                            _config = _deepcopy(self._config)
                            for _plugin in _operation_plugins:
                                _plugin(_config)
                        else:
                            _config = self._config
                        if (
                            _config.protocol is None
                            or _config.transport is None
                            or _config.endpoint_resolver is None
                            or _config.auth_scheme_resolver is None
                            or _config.auth_schemes is None
                        ):
                            raise $2T(
                                "protocol, transport, endpoint_resolver, auth_scheme_resolver,"
                                " and auth_schemes MUST be set on the config to make calls."
                            )

                        _retry_strategy = await self._retry_strategy_resolver.resolve_retry_strategy(
                            retry_strategy=_config.retry_strategy,
                            ${7C|}
                        )

                        _pipeline = $3T(
                            protocol=_config.protocol,
                            transport=_config.transport
                        )
                        _call = $4T(
                            input=_input,
                            operation=${operation:T},
                            context=$5T({"config": _config}),
                            interceptor=$6T(_config.interceptors),
                            auth_scheme_resolver=_config.auth_scheme_resolver,
                            supported_auth_schemes=_config.auth_schemes,
                            endpoint_resolver=_config.endpoint_resolver,
                            retry_strategy=_retry_strategy,
                        )
                        """,
                writer.consumer(w -> writeDefaultPlugins(w, defaultPlugins)),
                RuntimeTypes.EXPECTATION_NOT_MET_ERROR,
                RuntimeTypes.REQUEST_PIPELINE,
                RuntimeTypes.CLIENT_CALL,
                RuntimeTypes.TYPED_PROPERTIES,
                RuntimeTypes.INTERCEPTOR_CHAIN,
                writer.consumer(w -> {
                    if (CodegenUtils.getAsyncConfigSymbol(context.settings(), context.model()).isPresent()) {
                        w.write("retry_mode=_config.retry_mode,");
                        w.write("max_attempts=_config.max_attempts,");
                    }
                }),
                CodegenUtils.getPluginSymbol(context.settings()));

    }

    private void generateEventStreamOperation(PythonWriter writer, OperationShape operation) {
        writer.addDependency(SmithyPythonDependency.SMITHY_CORE);
        writer.addDependency(SmithyPythonDependency.SMITHY_AWS_CORE.withOptionalDependencies("eventstream"));
        var operationSymbol = symbolProvider.toSymbol(operation);
        writer.putContext("operation", operationSymbol);
        var operationMethodSymbol = operationSymbol.expectProperty(OPERATION_METHOD);
        writer.putContext("operationName", operationMethodSymbol.getName());
        writer.putContext("parameters",
                writer.consumer(new OperationInputGenerator(context, operation)::writeParameters));

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
                var outputDocs = "A `DuplexEventStream` for bidirectional streaming.";
                writer.write("""
                        async def ${operationName:L}(
                            ${parameters:C|}
                        ) -> ${duplexEventStream:T}[${inputStream:T}, ${outputStream:T}, ${output:T}]:
                            ${C|}
                            return await _pipeline.duplex_stream(
                                _call,
                                ${inputStream:T},
                                ${outputStream:T},
                                ${outputStreamDeserializer:T}().deserialize
                            )
                        """,
                        writer.consumer(w -> writeSharedOperationInit(w, operation, output, outputDocs)));
            } else {
                writer.putContext("inputEventStream", RuntimeTypes.INPUT_EVENT_STREAM);
                var outputDocs = "An `InputEventStream` for client-to-server streaming.";
                writer.write("""
                        async def ${operationName:L}(
                            ${parameters:C|}
                        ) -> ${inputEventStream:T}[${inputStream:T}, ${output:T}]:
                            ${C|}
                            return await _pipeline.input_stream(
                                _call,
                                ${inputStream:T}
                            )
                        """,
                        writer.consumer(w -> writeSharedOperationInit(w, operation, output, outputDocs)));
            }
        } else {
            writer.putContext("outputEventStream", RuntimeTypes.OUTPUT_EVENT_STREAM);
            var outputDocs = "An `OutputEventStream` for server-to-client streaming.";
            writer.write("""
                    async def ${operationName:L}(
                        ${parameters:C|}
                    ) -> ${outputEventStream:T}[${outputStream:T}, ${output:T}]:
                        ${C|}
                        return await _pipeline.output_stream(
                            _call,
                            ${outputStream:T},
                            ${outputStreamDeserializer:T}().deserialize
                        )
                    """,
                    writer.consumer(w -> writeSharedOperationInit(w, operation, output, outputDocs)));
        }
    }
}
