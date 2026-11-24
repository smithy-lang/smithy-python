/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen;

import static software.amazon.smithy.python.codegen.SymbolProperties.DESERIALIZER;
import static software.amazon.smithy.python.codegen.SymbolProperties.OPERATION_METHOD;

import java.util.Collection;
import java.util.EnumSet;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.TreeMap;
import java.util.function.Consumer;
import java.util.function.Function;
import java.util.function.UnaryOperator;
import java.util.stream.Collectors;
import software.amazon.smithy.codegen.core.CodegenException;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.codegen.core.SymbolProvider;
import software.amazon.smithy.codegen.core.SymbolReference;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.knowledge.EventStreamIndex;
import software.amazon.smithy.model.knowledge.EventStreamInfo;
import software.amazon.smithy.model.knowledge.PaginatedIndex;
import software.amazon.smithy.model.knowledge.PaginationInfo;
import software.amazon.smithy.model.knowledge.TopDownIndex;
import software.amazon.smithy.model.shapes.ListShape;
import software.amazon.smithy.model.shapes.MapShape;
import software.amazon.smithy.model.shapes.MemberShape;
import software.amazon.smithy.model.shapes.OperationShape;
import software.amazon.smithy.model.shapes.ServiceShape;
import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.model.shapes.ShapeType;
import software.amazon.smithy.model.shapes.StructureShape;
import software.amazon.smithy.model.traits.DocumentationTrait;
import software.amazon.smithy.model.traits.PaginatedTrait;
import software.amazon.smithy.model.traits.SparseTrait;
import software.amazon.smithy.model.traits.StreamingTrait;
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

    // The types a paginated trait's settings may target, as Smithy validates them.
    private static final Set<ShapeType> TOKEN_TARGETS = EnumSet.of(ShapeType.STRING, ShapeType.MAP);
    private static final Set<ShapeType> PAGE_SIZE_TARGETS = EnumSet.of(
            ShapeType.BYTE,
            ShapeType.SHORT,
            ShapeType.INTEGER,
            ShapeType.LONG);
    private static final Set<ShapeType> ITEMS_TARGETS = EnumSet.of(ShapeType.LIST, ShapeType.MAP);

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
                    var paginatedIndex = PaginatedIndex.of(model);
                    var operations = topDownIndex.getContainedOperations(service);
                    var paginatorNames = paginatorNames(operations, eventStreamIndex);
                    for (OperationShape operation : operations) {
                        if (eventStreamIndex.getInputInfo(operation).isPresent()
                                || eventStreamIndex.getOutputInfo(operation).isPresent()) {
                            // Sync clients don't support event streams.
                            if (!sync) {
                                generateEventStreamOperation(writer, operation);
                            }
                        } else {
                            generateOperation(writer, operation, sync);
                            var paginatorName = paginatorNames.get(operation.getId());
                            if (paginatorName != null) {
                                generatePaginator(writer,
                                        operation,
                                        paginatorName,
                                        paginationInfo(paginatedIndex, operation),
                                        sync);
                            }
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
                true,
                false,
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
     * Names the paginator of each operation that gets one.
     *
     * <p>A paginator is named like its operation's method with a {@code paginate_}
     * prefix. Operation methods keep their names. A paginator whose name is an
     * operation method's or an inherited client method's gets trailing underscores
     * until its name is also free of every other paginator's preferred name, so no
     * name depends on the order of operations. Paginators are named in shape ID order.
     *
     * <p>Event stream operations get no paginator, nor do operations with a
     * streaming input member, since that input can't be sent again for each page.
     */
    private Map<ShapeId, String> paginatorNames(
            Collection<OperationShape> operations,
            EventStreamIndex eventStreamIndex
    ) {
        var methods = new HashSet<>(PythonSymbolProvider.CLIENT_RESERVED_METHOD_NAMES);
        var preferred = new TreeMap<ShapeId, String>();
        for (OperationShape operation : operations) {
            var method = symbolProvider.toSymbol(operation).expectProperty(OPERATION_METHOD).getName();
            methods.add(method);
            if (operation.hasTrait(PaginatedTrait.class)
                    && eventStreamIndex.getInputInfo(operation).isEmpty()
                    && eventStreamIndex.getOutputInfo(operation).isEmpty()
                    && !hasStreamingInput(operation)) {
                preferred.put(operation.getId(), "paginate_" + method);
            }
        }
        var taken = new HashSet<>(methods);
        taken.addAll(preferred.values());
        var names = new LinkedHashMap<ShapeId, String>();
        for (var entry : preferred.entrySet()) {
            var name = entry.getValue();
            if (methods.contains(name)) {
                while (taken.contains(name)) {
                    name += "_";
                }
                taken.add(name);
            }
            names.put(entry.getKey(), name);
        }
        return names;
    }

    private boolean hasStreamingInput(OperationShape operation) {
        return model.expectShape(operation.getInputShape())
                .members()
                .stream()
                .anyMatch(member -> model.expectShape(member.getTarget()).hasTrait(StreamingTrait.class));
    }

    /**
     * Resolves the operation's effective pagination settings: its own trait, with
     * the service's filling each setting it omits.
     *
     * <p>Each token must be configured, and each configured setting must resolve to
     * a member of a supported type, as Smithy's own validation requires: tokens
     * target a string or map, the page size an integral number, and the items a list
     * or map. Both tokens must target the same type, since each output token is sent
     * as the next input token. An omitted page size or items is fine. Generation fails otherwise,
     * since a model built without validation could make a setting silently vanish.
     */
    private PaginationInfo paginationInfo(PaginatedIndex index, OperationShape operation) {
        var own = operation.expectTrait(PaginatedTrait.class);
        var trait = service.getTrait(PaginatedTrait.class).map(own::merge).orElse(own);
        var input = model.expectShape(operation.getInputShape(), StructureShape.class);
        var output = model.expectShape(operation.getOutputShape(), StructureShape.class);
        Function<String, List<MemberShape>> inputMember = name -> input.getMember(name)
                .map(List::of)
                .orElse(List.of());
        Function<String, List<MemberShape>> outputPath = path -> PaginatedTrait.resolveFullPath(path, model, output);
        var inputToken =
                checkPaginated(operation, "inputToken", trait.getInputToken(), true, inputMember, TOKEN_TARGETS);
        var outputToken = checkPaginated(operation,
                "outputToken",
                trait.getOutputToken(),
                true,
                outputPath,
                TOKEN_TARGETS);
        // Each output token is sent as the next input token, unconverted.
        if (inputToken != outputToken) {
            throw new CodegenException(String.format(
                    "The paginated inputToken of %s, \"%s\", targets a %s, but its outputToken, \"%s\", targets a %s.",
                    operation.getId(),
                    trait.getInputToken().get(),
                    inputToken,
                    trait.getOutputToken().get(),
                    outputToken));
        }
        checkPaginated(operation, "pageSize", trait.getPageSize(), false, inputMember, PAGE_SIZE_TARGETS);
        checkPaginated(operation, "items", trait.getItems(), false, outputPath, ITEMS_TARGETS);
        return index.getPaginationInfo(service, operation)
                .orElseThrow(() -> new CodegenException(String.format(
                        "The paginated trait of %s does not resolve to members of its input and output.",
                        operation.getId())));
    }

    // Fails unless a setting is omitted and optional, or resolves to members whose
    // last targets one of the given types. Returns that type, or null if omitted.
    private ShapeType checkPaginated(
            OperationShape operation,
            String setting,
            Optional<String> path,
            boolean required,
            Function<String, List<MemberShape>> resolve,
            Set<ShapeType> targets
    ) {
        if (path.isEmpty()) {
            if (required) {
                throw new CodegenException(String.format(
                        "The paginated trait of %s configures no %s, on the operation or its service.",
                        operation.getId(),
                        setting));
            }
            return null;
        }
        var members = resolve.apply(path.get());
        if (members.isEmpty()) {
            throw new CodegenException(String.format(
                    "The paginated %s of %s, \"%s\", does not resolve to a member.",
                    setting,
                    operation.getId(),
                    path.get()));
        }
        var target = model.expectShape(members.get(members.size() - 1).getTarget());
        if (!targets.contains(target.getType())) {
            throw new CodegenException(String.format(
                    "The paginated %s of %s, \"%s\", targets a %s, but must target one of %s.",
                    setting,
                    operation.getId(),
                    path.get(),
                    target.getType(),
                    targets));
        }
        return target.getType();
    }

    /**
     * Generates the method that iterates a paginated operation's pages.
     *
     * <p>It takes the same request as the operation's method, and checks and builds it
     * at once, but sends nothing: the runtime paginator calls the operation's method
     * for each page as it is iterated, so each call runs the operation's default
     * plugins and the caller's. It also takes the keyword-only SDK option
     * {@code stop_on_same_token}, which it hands to the runtime paginator, never to
     * the request. The async client's method is not a coroutine, since it returns an
     * async iterator.
     */
    private void generatePaginator(
            PythonWriter writer,
            OperationShape operation,
            String paginatorName,
            PaginationInfo info,
            boolean sync
    ) {
        var operationSymbol = symbolProvider.toSymbol(operation);
        var methodName = operationSymbol.expectProperty(OPERATION_METHOD).getName();
        var input = model.expectShape(operation.getInputShape());
        var outputName = symbolProvider.toSymbol(info.getOutput()).getName();
        var page = annotation(writer, symbolProvider.toSymbol(info.getOutput()));
        var itemsPath = info.getItemsMemberPath();

        // Page and item types are spelled through the models module, so they import
        // no model, and the runtime type is imported through $T, so a name the
        // client already uses is aliased.
        Symbol runtime;
        String returns;
        if (itemsPath.isEmpty()) {
            runtime = RuntimeTypes.ASYNC_PAGINATOR;
            returns = writer.format("$T[$L]", runtime, page);
        } else {
            runtime = RuntimeTypes.ASYNC_ITEM_PAGINATOR;
            var items = model.expectShape(itemsPath.get(itemsPath.size() - 1).getTarget());
            returns = writer.format("$T[$L, $L]", runtime, page, itemType(writer, items));
        }

        writer.putContext("operationName", paginatorName);
        writer.putContext("operation", "_models." + operationSymbol.getName());
        writer.putContext("plugin", CodegenUtils.getPluginSymbol(context.settings()));
        writeOverloadedOperation(writer,
                input,
                sync,
                false,
                true,
                returns,
                w -> writePaginatorDocs(w, operation, methodName, outputName, !itemsPath.isEmpty()),
                """
                        return $T(
                            self._build_input(
                                self._select_input(${operation:L}, args, kwargs),
                                ${operation:L},
                            ),
                            self.$L,
                            plugins,
                            ${C|}
                        )""",
                runtime,
                methodName,
                writer.consumer(w -> {
                    w.write("input_token=$L,", quote(symbolProvider.toMemberName(info.getInputTokenMember())));
                    w.write("output_token=$L,", pythonPath(info.getOutputTokenMemberPath()));
                    if (!itemsPath.isEmpty()) {
                        w.write("items=$L,", pythonPath(itemsPath));
                    }
                    w.write("stop_on_same_token=stop_on_same_token,");
                }));
    }

    // A tuple of the members' Python names.
    private String pythonPath(List<MemberShape> path) {
        var names = path.stream()
                .map(member -> quote(symbolProvider.toMemberName(member)))
                .collect(Collectors.joining(", "));
        return path.size() == 1 ? "(" + names + ",)" : "(" + names + ")";
    }

    private static String quote(String name) {
        return '"' + name + '"';
    }

    /**
     * Spells the type of the items a paginator yields from a page's collection: a
     * list's element, or a map's key and value as a tuple. A sparse collection's
     * items may be None.
     */
    private String itemType(PythonWriter writer, Shape collection) {
        if (collection instanceof MapShape map) {
            return "tuple[str, " + elementType(writer, map.getValue(), map.hasTrait(SparseTrait.class)) + "]";
        }
        if (collection instanceof ListShape list) {
            return elementType(writer, list.getMember(), list.hasTrait(SparseTrait.class));
        }
        throw new CodegenException("Paginated items must be a list or a map, but " + collection.getId()
                + " is a " + collection.getType());
    }

    private String elementType(PythonWriter writer, MemberShape member, boolean sparse) {
        var type = valueType(writer, model.expectShape(member.getTarget()));
        return sparse ? type + " | None" : type;
    }

    // Spelled as the models spell it, but with nested models qualified through the
    // models module, which the symbols of collections don't do. Other types, such as
    // Decimal or Document, are written as symbols so that the writer aliases one
    // named like the client.
    private String valueType(PythonWriter writer, Shape shape) {
        if (shape instanceof MapShape map) {
            return "dict[str, " + elementType(writer, map.getValue(), map.hasTrait(SparseTrait.class)) + "]";
        }
        if (shape instanceof ListShape list) {
            return "list[" + elementType(writer, list.getMember(), list.hasTrait(SparseTrait.class)) + "]";
        }
        var symbol = symbolProvider.toSymbol(shape);
        if (writer.getSymbolMapper().apply(symbol).getNamespace().equals(modelsNamespace)) {
            return annotation(writer, symbol);
        }
        return writer.format("$T", symbol);
    }

    private void writePaginatorDocs(
            PythonWriter writer,
            OperationShape operation,
            String methodName,
            String outputName,
            boolean hasItems
    ) {
        writer.writeMultiLineDocs(() -> {
            writer.write("""
                    Iterates the pages of the $L operation.

                    Takes the same request as `$L`, and checks it now, but sends nothing \
                    until iteration starts. Each page is the output of one call. The \
                    request's token, if any, starts the first page. Pagination ends at a \
                    page with no token or an empty one. By default, it also ends, normally, \
                    at a page whose token equals the one its request sent, including the \
                    starting token.$L
                    """,
                    operation.getId().getName(),
                    methodName,
                    hasItems ? " `items()` iterates the items of each page instead." : "");
            writer.write("Args:");
            writer.write("""
                        plugins:
                            A list of callables that modify the configuration dynamically.
                            They apply to each call of this iteration only, and will not
                            affect any other operation invocations.
                        stop_on_same_token:
                            Whether to end pagination at a page whose token equals, by
                            value, the one its request sent. Set to False to keep requesting
                            pages when tokens repeat, such as when polling for new results.
                            A page with no token, or an empty one, still ends pagination.
                            This option is not sent to the service.

                    Returns:
                        An iterator of `$L` pages.
                    """, outputName);
        });
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
     * @param coroutine Whether the async client's method is a coroutine. A sync
     *     client's method never is.
     * @param paginator Whether the method is a paginator, which also takes the
     *     SDK's keyword-only {@code stop_on_same_token} option in every definition.
     *     The option is not a member of the request, so it is never sent.
     * @param returns The method's return type, as written.
     * @param docs Writes the method's documentation.
     * @param body The async code template of the implementation's body.
     * @param bodyArgs The positional arguments of the body template.
     */
    private void writeOverloadedOperation(
            PythonWriter writer,
            Shape input,
            boolean sync,
            boolean coroutine,
            boolean paginator,
            String returns,
            Consumer<PythonWriter> docs,
            String body,
            Object... bodyArgs
    ) {
        UnaryOperator<String> code = sync ? SyncVariant::toSyncCode : UnaryOperator.identity();
        UnaryOperator<String> signature = coroutine ? code : SyncVariant::toSyncCode;
        // Aliased because a method defined in the class body shadows a module name
        // for the rest of the class, and an operation may be named Overload.
        writer.addStdlibImport("typing", "overload", "_overload");
        writer.addStdlibImport("typing", "Unpack", "_Unpack");
        // Set on every call, since the writer's context outlives this method.
        writer.putContext("paginator", paginator);
        writer.putContext("returns", returns);
        writer.putContext("request", requestType(writer, input, sync));
        writer.putContext("keywords", keywordsType(writer, input, sync));
        writer.putContext("docs", writer.consumer(docs));
        writer.putContext("body", writer.consumer(w -> w.write(code.apply(body), bodyArgs)));
        writer.write(signature.apply("""
                @_overload
                async def ${operationName:L}(
                    self,
                    request: ${request:L},
                    /,
                    *,
                    plugins: list[${plugin:T}] | None = None,
                    ${?paginator}
                    stop_on_same_token: bool = True,
                    ${/paginator}
                ) -> ${returns:L}: ...

                @_overload
                async def ${operationName:L}(
                    self,
                    /,
                    *,
                    plugins: list[${plugin:T}] | None = None,
                    ${?paginator}
                    stop_on_same_token: bool = True,
                    ${/paginator}
                    **kwargs: _Unpack[${keywords:L}],
                ) -> ${returns:L}:
                    ${docs:C|}

                async def ${operationName:L}(
                    self,
                    /,
                    *args: object,
                    plugins: list[${plugin:T}] | None = None,
                    ${?paginator}
                    stop_on_same_token: bool = True,
                    ${/paginator}
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
                true,
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
