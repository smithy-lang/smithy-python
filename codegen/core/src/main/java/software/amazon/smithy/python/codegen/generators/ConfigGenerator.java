/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.generators;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Optional;
import java.util.TreeSet;
import java.util.function.Consumer;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.model.knowledge.ServiceIndex;
import software.amazon.smithy.model.knowledge.TopDownIndex;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.model.traits.XmlNamespaceTrait;
import software.amazon.smithy.python.codegen.CodegenUtils;
import software.amazon.smithy.python.codegen.ConfigProperty;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.PythonSettings;
import software.amazon.smithy.python.codegen.RuntimeTypes;
import software.amazon.smithy.python.codegen.SmithyPythonDependency;
import software.amazon.smithy.python.codegen.SymbolProperties;
import software.amazon.smithy.python.codegen.integrations.PythonIntegration;
import software.amazon.smithy.python.codegen.integrations.RuntimeClientPlugin;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Generates the client's config objects.
 *
 * <p>Every service, AWS or not, gets a shared field-carrying base
 * ({@code _<Svc>ConfigBase}) and two concrete configs, {@code <Svc>Config}
 * (synchronous) and {@code Async<Svc>Config} (asynchronous), each with a plain
 * {@code resolve()}. The sync/async split and the {@code FieldSpec} resolution
 * engine are universal; a {@link ConfigBackend} supplies what is
 * resolution-source specific (the base classes, extra resolve parameters, extra
 * fields). AWS-ness never gates the shape.
 */
@SmithyInternalApi
public final class ConfigGenerator implements Runnable {

    // Generic config fields present on every service. None carry HTTP specifics;
    // Smithy is transport agnostic.
    private static final List<ConfigProperty> BASE_PROPERTIES = List.of(
            ConfigProperty.builder()
                    .name("interceptors")
                    .type(Symbol.builder()
                            .name("list[_ServiceInterceptor]")
                            .build())
                    .documentation(
                            "The list of interceptors, which are hooks that are called during the execution of a request.")
                    .nullable(false)
                    .defaultFactory(writer -> writer.writeInline("[]"))
                    .build(),
            ConfigProperty.builder()
                    .name("retry_strategy")
                    .type(Symbol.builder()
                            .name("RetryStrategy | AsyncRetryStrategy | RetryStrategyOptions")
                            .addReference(Symbol.builder()
                                    .name("RetryStrategy")
                                    .namespace("smithy_core.interfaces.retries", ".")
                                    .addDependency(SmithyPythonDependency.SMITHY_CORE)
                                    .build())
                            .addReference(Symbol.builder()
                                    .name("AsyncRetryStrategy")
                                    .namespace("smithy_core.aio.interfaces.retries", ".")
                                    .addDependency(SmithyPythonDependency.SMITHY_CORE)
                                    .build())
                            .addReference(Symbol.builder()
                                    .name("RetryStrategyOptions")
                                    .namespace("smithy_core.retries", ".")
                                    .addDependency(SmithyPythonDependency.SMITHY_CORE)
                                    .build())
                            .build())
                    .documentation(
                            "The retry strategy or options for configuring retry behavior. Can be either a configured RetryStrategy or RetryStrategyOptions to create one.")
                    .build(),
            ConfigProperty.builder()
                    .name("endpoint_uri")
                    .type(Symbol.builder()
                            .name("str | URI")
                            .addReference(Symbol.builder()
                                    .name("URI")
                                    .namespace("smithy_core.interfaces", ".")
                                    .addDependency(SmithyPythonDependency.SMITHY_CORE)
                                    .build())
                            .build())
                    .documentation("A static URI to route requests to.")
                    .build(),
            ConfigProperty.builder()
                    .name("endpoint_resolver")
                    .type(RuntimeTypes.ENDPOINT_RESOLVER)
                    .documentation("""
                            The endpoint resolver used to resolve the final endpoint per-operation based on the \
                            configuration.""")
                    .nullable(false)
                    .defaultFactory(writer -> writer.writeInline("$T()", RuntimeTypes.STATIC_ENDPOINT_RESOLVER))
                    .build());

    // Fields for any http-based service client, except the transport itself.
    private static final List<ConfigProperty> HTTP_PROPERTIES = List.of(
            ConfigProperty.builder()
                    .name("http_request_config")
                    .type(Symbol.builder()
                            .name("HTTPRequestConfiguration")
                            .namespace("smithy_http.interfaces", ".")
                            .addDependency(SmithyPythonDependency.SMITHY_HTTP)
                            .build())
                    .documentation("Configuration for individual HTTP requests.")
                    .build());

    private final PythonSettings settings;
    private final GenerationContext context;

    public ConfigGenerator(PythonSettings settings, GenerationContext context) {
        this.context = context;
        this.settings = settings;
    }

    private static List<ConfigProperty> getProtocolProperties(GenerationContext context) {
        var properties = new ArrayList<ConfigProperty>();
        var protocolBuilder = ConfigProperty.builder()
                .name("protocol")
                .type(Symbol.builder()
                        .name("ClientProtocol[Any, Any]")
                        .addReference(Symbol.builder()
                                .name("ClientProtocol")
                                .namespace("smithy_core.aio.interfaces", ".")
                                .build())
                        .build())
                .inputType(Symbol.builder()
                        .name("ClientProtocol[Any, Any] | ProtocolConstructor[ClientProtocol[Any, Any]]")
                        .addReference(Symbol.builder()
                                .name("ClientProtocol")
                                .namespace("smithy_core.aio.interfaces", ".")
                                .build())
                        .addReference(Symbol.builder()
                                .name("ProtocolConstructor")
                                .namespace("smithy_core.aio.interfaces", ".")
                                .addDependency(SmithyPythonDependency.SMITHY_CORE)
                                .build())
                        .build())
                .documentation("Pass a protocol class reference to select the protocol, e.g. "
                        + "protocol=AwsJson10ClientProtocol. For custom protocols a protocol "
                        + "instance may also be passed.")
                .defaultFactory(w -> context.protocolGenerator().initializeSyncProtocol(context, w))
                .asyncDefaultFactory(w -> context.protocolGenerator().initializeProtocol(context, w))
                .converter(w -> w.writeInline(
                        "p(_PROTOCOL_SETTINGS) if isinstance(p, type) else p"));

        var transportBuilder = ConfigProperty.builder()
                .name("transport")
                .type(Symbol.builder()
                        .name("ClientTransport[Any, Any]")
                        .addReference(Symbol.builder()
                                .name("ClientTransport")
                                .namespace("smithy_core.aio.interfaces", ".")
                                .build())
                        .build())
                .documentation("The transport to use to send requests (e.g. an HTTP client). "
                        + "Operations with bidirectional event streams require a "
                        + "DuplexClientTransport, such as AWSCRTHTTPClient. Transports are "
                        + "assumed not to support duplex streaming unless they explicitly set "
                        + "SUPPORTS_DUPLEX_STREAMING to True.");

        if (context.applicationProtocol().isHttpProtocol()) {
            properties.addAll(HTTP_PROPERTIES);
            transportBuilder
                    .defaultFactory(writer -> {
                        writer.addDependency(
                                SmithyPythonDependency.SMITHY_HTTP.withOptionalDependencies("urllib3"));
                        writer.writeInline("$T()", RuntimeTypes.URLLIB3_CLIENT);
                    })
                    .asyncDefaultFactory(writer -> {
                        writer.addDependency(
                                SmithyPythonDependency.SMITHY_HTTP.withOptionalDependencies("aiohttp"));
                        writer.writeInline("$T()", RuntimeTypes.AIOHTTP_CLIENT);
                    });
        }

        properties.add(protocolBuilder.build());
        properties.add(transportBuilder.build());
        return properties;
    }

    private static List<ConfigProperty> getAuthProperties(GenerationContext context, boolean hasAuth) {
        Consumer<PythonWriter> authSchemesDefault = hasAuth
                ? writer -> writeDefaultAuthSchemes(context, writer, true)
                : writer -> writer.writeInline("{}");
        // Only a non-empty scheme map differs by mode (sync vs async scheme instances);
        // an empty default is identical, so it takes no async_default_factory.
        Consumer<PythonWriter> authSchemesAsyncDefault = hasAuth
                ? writer -> writeDefaultAuthSchemes(context, writer, false)
                : null;

        Symbol defaultResolver = hasAuth
                ? CodegenUtils.getHttpAuthSchemeResolverSymbol(context.settings())
                : Symbol.builder()
                        .name("DefaultAuthResolver")
                        .namespace("smithy_core.auth", ".")
                        .addDependency(SmithyPythonDependency.SMITHY_CORE)
                        .build();
        Symbol resolverType = Symbol.builder()
                .name("AuthSchemeResolver")
                .namespace("smithy_core.interfaces.auth", ".")
                .addDependency(SmithyPythonDependency.SMITHY_CORE)
                .build();

        return List.of(
                ConfigProperty.builder()
                        .name("auth_schemes")
                        .type(Symbol.builder()
                                .name("dict[ShapeID, AuthScheme[Any, Any, Any, Any]]")
                                .addReference(Symbol.builder()
                                        .name("ShapeID")
                                        .namespace("smithy_core.shapes", ".")
                                        .addDependency(SmithyPythonDependency.SMITHY_CORE)
                                        .build())
                                .addReference(Symbol.builder()
                                        .name("AuthScheme")
                                        .namespace("smithy_core.aio.interfaces.auth", ".")
                                        .addDependency(SmithyPythonDependency.SMITHY_CORE)
                                        .build())
                                .addReference(Symbol.builder()
                                        .name("Any")
                                        .namespace("typing", ".")
                                        .putProperty(SymbolProperties.STDLIB, true)
                                        .build())
                                .build())
                        .documentation("A map of auth scheme ids to auth schemes.")
                        .nullable(false)
                        .defaultFactory(authSchemesDefault)
                        .asyncDefaultFactory(authSchemesAsyncDefault)
                        .build(),
                ConfigProperty.builder()
                        .name("auth_scheme_resolver")
                        .type(resolverType)
                        .documentation(
                                "An auth scheme resolver that determines the auth scheme for each operation.")
                        .nullable(false)
                        .defaultFactory(writer -> writer.writeInline("$T()", defaultResolver))
                        .build());
    }

    private static void writeDefaultAuthSchemes(GenerationContext context, PythonWriter writer, boolean sync) {
        var service = context.settings().service(context.model());
        writer.openBlock("{");
        for (PythonIntegration integration : context.integrations()) {
            for (RuntimeClientPlugin plugin : integration.getClientPlugins(context)) {
                if (plugin.matchesService(context.model(), service) && plugin.getAuthScheme().isPresent()) {
                    var scheme = plugin.getAuthScheme().get();
                    writer.write("$T($S): ${C|},",
                            RuntimeTypes.SHAPE_ID,
                            scheme.getAuthTrait(),
                            writer.consumer(w -> {
                                if (sync) {
                                    scheme.initializeSyncScheme(context, w, service);
                                } else {
                                    scheme.initializeScheme(context, w, service);
                                }
                            }));
                }
            }
        }
        writer.closeBlock("}");
    }

    @Override
    public void run() {
        var config = CodegenUtils.getConfigSymbol(context.settings(), context.model());

        context.writerDelegator().useFileWriter(config.getDefinitionFile(), config.getNamespace(), writer -> {
            writeInterceptorsType(writer);
            stageProtocolSettings(context, writer);
            generateConfig(context, writer);
        });

        // The plugin is a callable taking the async config (the superset shape).
        var plugin = CodegenUtils.getPluginSymbol(context.settings());
        var asyncConfig = CodegenUtils.getAsyncConfigSymbol(context.settings(), context.model());
        context.writerDelegator().useFileWriter(plugin.getDefinitionFile(), plugin.getNamespace(), writer -> {
            writer.addStdlibImport("typing", "Callable");
            writer.addStdlibImport("typing", "TypeAlias");
            writer.write("$L: TypeAlias = Callable[[$T], None]", plugin.getName(), asyncConfig);
            writer.writeDocs("""
                    A callable that customizes a client configuration. Service-level plugins are
                    applied once to the base configuration inherited by every operation.
                    Operation-level plugins apply only to a single operation invocation.
                    """, context);
        });
    }

    private ConfigBackend resolveBackend() {
        for (PythonIntegration integration : context.integrations()) {
            Optional<ConfigBackend> backend = integration.configBackend(context);
            if (backend.isPresent()) {
                return backend.get();
            }
        }
        return new GenericConfigBackend();
    }

    private List<ConfigProperty> collectProperties() {
        var properties = new TreeSet<>(Comparator.comparing(ConfigProperty::name));
        properties.addAll(BASE_PROPERTIES);
        properties.addAll(getProtocolProperties(context));

        var serviceIndex = ServiceIndex.of(context.model());
        boolean hasAuth = !serviceIndex.getAuthSchemes(settings.service()).isEmpty();
        properties.addAll(getAuthProperties(context, hasAuth));

        var model = context.model();
        var service = context.settings().service(model);
        for (PythonIntegration integration : context.integrations()) {
            for (RuntimeClientPlugin plugin : integration.getClientPlugins(context)) {
                if (plugin.matchesService(model, service)) {
                    properties.addAll(plugin.getConfigProperties());
                }
            }
        }
        return List.copyOf(properties);
    }

    private void generateConfig(GenerationContext context, PythonWriter writer) {
        var baseSymbol = CodegenUtils.getConfigBaseSymbol(context.settings(), context.model());
        var syncSymbol = CodegenUtils.getConfigSymbol(context.settings(), context.model());
        var asyncSymbol = CodegenUtils.getAsyncConfigSymbol(context.settings(), context.model());
        var backend = resolveBackend();
        var properties = collectProperties();
        var serviceIndex = ServiceIndex.of(context.model());
        boolean hasAuth = !serviceIndex.getAuthSchemes(settings.service()).isEmpty();

        final String serviceId = CodegenUtils.getServiceIdName(context.settings(), context.model());

        writer.addStdlibImport("typing", "ClassVar");
        writer.addStdlibImport("typing", "Any");
        writer.addStdlibImport("typing", "Self");
        writer.addStdlibImport("typing", "Unpack");
        writer.addStdlibImport("dataclasses", "dataclass");
        writer.addStdlibImport("dataclasses", "field");

        var fieldSpecSymbol = Symbol.builder()
                .name("FieldSpec")
                .namespace("smithy_core.config", ".")
                .addDependency(SmithyPythonDependency.SMITHY_CORE)
                .build();

        var overridesName = "_" + stripAsyncPrefix(asyncSymbol.getName()) + "Overrides";

        // Overrides TypedDict: lets callers type the keyword overrides accepted by resolve().
        writer.addStdlibImport("typing", "TypedDict");
        writer.write("");
        writer.openBlock("class $L($T, total=False):", overridesName, backend.overridesBaseSymbol());
        boolean wroteOverride = false;
        for (ConfigProperty property : properties) {
            if (!backend.isPredefinedField(property.name())) {
                writer.write("$L: $T | None", property.name(), property.inputType());
                wroteOverride = true;
            }
        }
        if (!wroteOverride) {
            writer.write("pass");
        }
        writer.closeBlock("");
        writer.write("");

        // Shared field-carrying base.
        writer.write("@dataclass(kw_only=True, repr=False, init=False)");
        writer.openBlock("class $L($T):", baseSymbol.getName(), backend.baseSymbol());
        writer.writeDocs("Shared fields for the sync and async " + serviceId + " config classes.",
                context);
        writer.write("");

        for (ConfigProperty property : properties) {
            writeFieldDeclaration(writer, property);
        }

        writer.openBlock("_FIELDS: ClassVar[dict[str, $T]] = {", fieldSpecSymbol);
        for (ConfigProperty property : properties) {
            if (!backend.isPredefinedField(property.name())) {
                writeFieldSpecEntry(writer, property, fieldSpecSymbol);
            }
        }
        backend.writeExtraFields(context, writer);
        writer.closeBlock("}");
        writer.write("");

        if (hasAuth) {
            writer.write("def set_auth_scheme(self, scheme: AuthScheme[Any, Any, Any, Any]) -> None:");
            writer.indent();
            writer.writeDocs("""
                    Set an auth scheme implementation using its scheme ID.

                    :param scheme: The auth scheme to add or replace.
                    """, context);
            writer.write("auth_schemes = dict(self.auth_schemes or {})");
            writer.write("auth_schemes[scheme.scheme_id] = scheme");
            writer.write("self.auth_schemes = auth_schemes");
            writer.dedent();
            writer.write("");
        }
        writer.closeBlock("");
        writer.write("");

        // Sync config.
        writeConcreteConfig(writer,
                syncSymbol.getName(),
                baseSymbol,
                backend.syncConfigSymbol(),
                backend,
                overridesName,
                serviceId,
                false);
        writer.write("");
        // Async config.
        writeConcreteConfig(writer,
                asyncSymbol.getName(),
                baseSymbol,
                backend.asyncConfigSymbol(),
                backend,
                overridesName,
                serviceId,
                true);
    }

    private void writeFieldDeclaration(PythonWriter writer, ConfigProperty property) {
        if (property.name().equals("interceptors")) {
            writer.write("interceptors: list[_ServiceInterceptor] = field(default_factory=lambda: [])");
        } else {
            // Every field resolves to a value or None via the engine, so all declare | None = None.
            writer.write("$L: $T | None = None", property.name(), property.type());
        }
        writer.writeDocs(property.documentation(), context);
        writer.write("");
    }

    private void writeFieldSpecEntry(PythonWriter writer, ConfigProperty property, Symbol fieldSpecSymbol) {
        boolean hasDefaultFactory = property.defaultFactory().isPresent();
        boolean hasAsync = property.asyncDefaultFactory().isPresent();
        boolean hasConverter = property.converter().isPresent();

        if (!hasDefaultFactory && !hasAsync && !hasConverter) {
            writer.write("\"$L\": $T(default=None),", property.name(), fieldSpecSymbol);
            return;
        }

        writer.write("\"$L\": $T(", property.name(), fieldSpecSymbol);
        writer.indent();
        if (hasDefaultFactory) {
            writer.write("default_factory=lambda: ${C|},",
                    writer.consumer(w -> property.defaultFactory().get().accept(w)));
        } else {
            writer.write("default=None,");
        }
        if (hasAsync) {
            writer.write("async_default_factory=lambda: ${C|},",
                    writer.consumer(w -> property.asyncDefaultFactory().get().accept(w)));
        }
        if (hasConverter) {
            writer.write("converter=lambda p: ${C|},",
                    writer.consumer(w -> property.converter().get().accept(w)));
        }
        writer.dedent();
        writer.write("),");
    }

    private void writeConcreteConfig(
            PythonWriter writer,
            String className,
            Symbol baseSymbol,
            Symbol modeSymbol,
            ConfigBackend backend,
            String overridesName,
            String serviceId,
            boolean async
    ) {
        writer.write("@dataclass(kw_only=True, repr=False, init=False)");
        writer.openBlock("class $L($T, $T):", className, baseSymbol, modeSymbol);
        writer.writeDocs(serviceId + " configuration (" + (async ? "asynchronous" : "synchronous") + ").",
                context);
        writer.write("");
        writer.write("@classmethod");
        writer.write("$Ldef resolve(  # pyright: ignore[reportIncompatibleMethodOverride]",
                async ? "async " : "");
        writer.indent();
        writer.write("cls,");
        if (!backend.resolveParams().isEmpty()) {
            writer.write("*,");
            for (var param : backend.resolveParams()) {
                writer.write("$L: $T | None = None,", param.name(), param.type());
            }
            writer.write("**overrides: Unpack[$L],", overridesName);
        } else {
            writer.write("**overrides: Unpack[$L],", overridesName);
        }
        writer.dedent();
        writer.write(") -> Self:");
        writer.indent();
        writer.writeDocs(
                "Resolve config from environment, defaults, and explicit overrides.",
                context);
        if (async) {
            writer.write("return await cls._resolve_async(");
        } else {
            writer.write("return cls._resolve(");
        }
        writer.indent();
        writer.write("overrides=overrides,");
        for (var param : backend.resolveParams()) {
            writer.write("$1L=$1L,", param.name());
        }
        writer.dedent();
        writer.write(")");
        writer.dedent();
        writer.closeBlock("");
    }

    private static String stripAsyncPrefix(String name) {
        return name.startsWith("Async") ? name.substring("Async".length()) : name;
    }

    // Emit the shared _PROTOCOL_SETTINGS bag as the union of the fields every protocol
    // the service resolves needs.
    private void stageProtocolSettings(GenerationContext context, PythonWriter writer) {
        var generator = context.protocolGenerator();
        if (generator == null) {
            return;
        }

        var generators = new java.util.HashMap<ShapeId, ProtocolGenerator>();
        for (var integration : context.integrations()) {
            for (var g : integration.getProtocolGenerators()) {
                generators.put(g.getProtocol(), g);
            }
        }

        var required = java.util.EnumSet.of(
                ProtocolSettingsField.NAMESPACE,
                ProtocolSettingsField.SERVICE_TARGET);
        var service = context.settings().service(context.model());
        var resolved = ServiceIndex.of(context.model()).getProtocols(service).keySet();
        for (var protocolId : resolved) {
            var g = generators.get(protocolId);
            if (g != null) {
                required.addAll(g.requiredProtocolSettings(context));
            }
        }

        var args = new ArrayList<Object>();
        var params = new StringBuilder("namespace=$S, service_target=$S");
        args.add(service.getId().getNamespace());
        args.add(service.getId().getName());
        if (required.contains(ProtocolSettingsField.VERSION)) {
            params.append(", version=$S");
            args.add(service.getVersion());
        }
        var xmlNamespace = service.getTrait(XmlNamespaceTrait.class);
        if (required.contains(ProtocolSettingsField.XML_NAMESPACE) && xmlNamespace.isPresent()) {
            params.append(", xml_namespace=$S");
            args.add(xmlNamespace.get().getUri());
        }

        args.add(0, RuntimeTypes.PROTOCOL_SETTINGS);
        writer.write("_PROTOCOL_SETTINGS = $T(" + params + ")", args.toArray());
    }

    private void writeInterceptorsType(PythonWriter writer) {
        var symbolProvider = context.symbolProvider();
        var operationShapes = TopDownIndex.of(context.model())
                .getContainedOperations(settings.service());

        writer.addStdlibImport("typing", "Union");
        writer.addDependency(SmithyPythonDependency.SMITHY_CORE);

        writer.writeInline("_ServiceInterceptor = Union[");
        var iter = operationShapes.iterator();
        while (iter.hasNext()) {
            var operation = iter.next();
            var input = symbolProvider.toSymbol(context.model().expectShape(operation.getInputShape()));
            var output = symbolProvider.toSymbol(context.model().expectShape(operation.getOutputShape()));

            writer.addStdlibImport("typing", "Any");
            writer.writeInline("$T[$T, $T, Any, Any]", RuntimeTypes.INTERCEPTOR, input, output);
            if (iter.hasNext()) {
                writer.writeInline(", ");
            } else {
                writer.writeInline("]");
            }
        }
        writer.write("");
    }

    /**
     * The generic (non-AWS) config backend: the plain {@code smithy_core.config}
     * base classes, a {@code resolve(**overrides)} with no resolution source, and
     * no extra fields.
     */
    private static final class GenericConfigBackend implements ConfigBackend {
        @Override
        public Symbol baseSymbol() {
            return coreConfig("ConfigBase");
        }

        @Override
        public Symbol syncConfigSymbol() {
            return coreConfig("Config");
        }

        @Override
        public Symbol asyncConfigSymbol() {
            return coreConfig("AsyncConfig");
        }

        @Override
        public Symbol overridesBaseSymbol() {
            // A bare TypedDict base; emit as a stdlib TypedDict with no extra keys.
            return Symbol.builder()
                    .name("TypedDict")
                    .putProperty(SymbolProperties.STDLIB, true)
                    .namespace("typing", ".")
                    .build();
        }

        @Override
        public List<ResolveParam> resolveParams() {
            return List.of();
        }

        @Override
        public void writeExtraFields(GenerationContext context, PythonWriter writer) {
            // No resolution-source fields for the generic backend.
        }

        private static Symbol coreConfig(String name) {
            return Symbol.builder()
                    .name(name)
                    .namespace("smithy_core.config", ".")
                    .addDependency(SmithyPythonDependency.SMITHY_CORE)
                    .build();
        }
    }
}
