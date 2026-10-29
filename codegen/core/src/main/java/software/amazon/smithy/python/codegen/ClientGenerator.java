/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen;

import static software.amazon.smithy.python.codegen.SymbolProperties.DESERIALIZER;
import static software.amazon.smithy.python.codegen.SymbolProperties.OPERATION_METHOD;

import java.util.Collection;
import java.util.LinkedHashSet;
import java.util.function.UnaryOperator;
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
        // The sync variant needs a generated config to resolve; other services stay async-only.
        if (CodegenUtils.getAsyncConfigSymbol(context.settings(), context.model()).isPresent()) {
            var mapper = SyncVariant.mapper(context.settings());
            var syncClient = mapper.apply(symbolProvider.toSymbol(service));
            context.writerDelegator()
                    .useFileWriter(syncClient.getDefinitionFile(), syncClient.getNamespace(), writer -> {
                        writer.setSymbolMapper(mapper);
                        generateService(writer, true);
                    });
            writeSyncExports(syncClient, mapper);
        }
    }

    private void writeSyncExports(Symbol syncClient, UnaryOperator<Symbol> mapper) {
        var syncConfig = mapper.apply(CodegenUtils.getAsyncConfigSymbol(context.settings(), model).get());
        var syncPackage = context.settings().moduleName() + ".sync";
        var syncInit = "./src/" + context.settings().moduleName() + "/sync/__init__.py";
        context.writerDelegator().useFileWriter(syncInit, syncPackage, writer -> {
            writer.write("from .client import $L", syncClient.getName());
            writer.write("from .config import $L, Plugin", syncConfig.getName());
            writer.write("");
            writer.write("__all__ = [$S, $S, \"Plugin\"]", syncClient.getName(), syncConfig.getName());
        });

        // Lazily exported from the package root so importing the package, or the async
        // client, does not import the sync client.
        var init = "./src/" + context.settings().moduleName() + "/__init__.py";
        context.writerDelegator().useFileWriter(init, context.settings().moduleName(), writer -> {
            writer.addStdlibImport("typing", "TYPE_CHECKING");
            writer.addStdlibImport("typing", "Any");
            writer.write("""
                    if TYPE_CHECKING:
                        from .sync import $1L, $2L

                    __all__ = [$1S, $2S]


                    def __getattr__(name: str) -> Any:
                        if name in __all__:
                            from . import sync

                            return getattr(sync, name)
                        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

                    """, syncClient.getName(), syncConfig.getName());
        });
    }

    private void generateService(PythonWriter writer, boolean sync) {
        UnaryOperator<String> code = sync ? SyncVariant::toSyncCode : UnaryOperator.identity();
        var serviceSymbol = writer.getSymbolMapper().apply(symbolProvider.toSymbol(service));
        writer.addLocallyDefinedSymbol(serviceSymbol);
        var configSymbol = CodegenUtils.getConfigSymbol(context.settings());
        var pluginSymbol = CodegenUtils.getPluginSymbol(context.settings());
        writer.addLogger();

        // Services with a generated async config resolve lazily on first use;
        // the rest keep the synchronous constructor with old Config.
        var asyncConfigSymbol = CodegenUtils.getAsyncConfigSymbol(context.settings(), context.model());
        var isAsyncConfig = asyncConfigSymbol.isPresent();
        var configSym = asyncConfigSymbol.orElse(configSymbol);

        writer.openBlock("class $L($T):",
                "",
                serviceSymbol.getName(),
                RuntimeTypes.ASYNC_CLIENT,
                () -> {
                    var docs = service.getTrait(DocumentationTrait.class)
                            .map(StringTrait::getValue)
                            .orElse("Client for " + service.getId().getName());
                    writer.writeDocs(docs, context);

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

                    writer.write(code.apply("""
                            def __init__(
                                self,
                                config: $1T | None = None,
                                plugins: list[$2T] | None = None,
                            ):
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
                                input: I,
                                operation: $8T[I, O],
                                default_plugins: list[$2T],
                                plugins: list[$2T] | None,
                            ) -> tuple[$9T[Any, Any], $10T[I, O]]:
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
                            """),
                            configSym,
                            pluginSymbol,
                            writer.consumer(w -> writeConstructorDocs(w, serviceSymbol.getName())),
                            writer.consumer(w -> writeDefaultPlugins(w, servicePlugins)),
                            writer.consumer(w -> {
                                if (isAsyncConfig) {
                                    w.write(code.apply("config = await $T.resolve()"), configSym);
                                } else {
                                    w.write("config = $T()", configSym);
                                }
                            }),
                            writer.consumer(w -> {
                                w.pushState(new ClientSetupSection(sync));
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
                            RuntimeTypes.DESERIALIZEABLE_SHAPE);

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
                });

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
        // class. The operation constant below is a real runtime import.
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
        writer.putContext("operation", symbolProvider.toSymbol(operation));
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
                            ${C|}
                            ${?optionalInput}if input is None:
                                input = ${operation:T}.input()
                            ${/optionalInput}pipeline, call = await self._prepare_call(
                                input,
                                ${operation:T},
                                [
                                    ${C|}
                                ],
                                plugins,
                            )
                            return await pipeline(call)
                        """;
        writer.write(sync ? SyncVariant.toSyncCode(template) : template,
                writer.consumer(w -> writeOperationDocs(w, operation, input, output)),
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
                writer.putContext("duplexEventStream", RuntimeTypes.DUPLEX_EVENT_STREAM);
                var outputDocs = "A `DuplexEventStream` for bidirectional streaming.";
                writer.write("""
                        async def ${operationName:L}(
                            self,
                            input: ${input:T},
                            plugins: list[${plugin:T}] | None = None
                        ) -> ${duplexEventStream:T}[${inputStream:T}, ${outputStream:T}, ${output:T}]:
                            ${C|}
                            pipeline, call = await self._prepare_call(
                                input,
                                ${operation:T},
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
                var outputDocs = "An `InputEventStream` for client-to-server streaming.";
                writer.write("""
                        async def ${operationName:L}(
                            self,
                            input: ${input:T},
                            plugins: list[${plugin:T}] | None = None
                        ) -> ${inputEventStream:T}[${inputStream:T}, ${output:T}]:
                            ${C|}
                            pipeline, call = await self._prepare_call(
                                input,
                                ${operation:T},
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
            var outputDocs = "An `OutputEventStream` for server-to-client streaming.";
            writer.write("""
                    async def ${operationName:L}(
                        self,
                        input: ${input:T},
                        plugins: list[${plugin:T}] | None = None
                    ) -> ${outputEventStream:T}[${outputStream:T}, ${output:T}]:
                        ${C|}
                        pipeline, call = await self._prepare_call(
                            input,
                            ${operation:T},
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
