/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.generators;

import java.util.ArrayList;
import java.util.Collection;
import java.util.Comparator;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeSet;
import java.util.function.Consumer;
import java.util.function.UnaryOperator;
import software.amazon.smithy.aws.traits.ServiceTrait;
import software.amazon.smithy.codegen.core.CodegenException;
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
import software.amazon.smithy.python.codegen.SyncVariant;
import software.amazon.smithy.python.codegen.integrations.EndpointRulesExtension;
import software.amazon.smithy.python.codegen.integrations.PythonIntegration;
import software.amazon.smithy.python.codegen.integrations.RuntimeClientPlugin;
import software.amazon.smithy.python.codegen.sections.AsyncConfigSection;
import software.amazon.smithy.python.codegen.sections.ConfigSection;
import software.amazon.smithy.python.codegen.sections.InitDefaultEndpointResolverSection;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.rulesengine.traits.ClientContextParamsTrait;
import software.amazon.smithy.utils.CaseUtils;
import software.amazon.smithy.utils.CodeInterceptor;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Generates the client's config object.
 */
@SmithyInternalApi
public final class ConfigGenerator implements Runnable {

    // This list contains any properties that should unconditionally be added to every
    // config object. This should be as minimal as possible, and importantly should
    // not contain any HTTP related config since Smithy is transport agnostic.
    private static final List<ConfigProperty> BASE_PROPERTIES = List.of(
            ConfigProperty.builder()
                    .name("interceptors")
                    .type(Symbol.builder()
                            .name("list[_ServiceInterceptor]")
                            .build())
                    .documentation(
                            "The list of interceptors, which are hooks that are called during the execution of a request.")
                    .nullable(false)
                    .initialize(writer -> writer.write("self.interceptors = interceptors or []"))
                    .build(),
            ConfigProperty.builder()
                    .name("retry_strategy")
                    .type(Symbol.builder()
                            .name("RetryStrategy | RetryStrategyOptions")
                            .addReference(Symbol.builder()
                                    .name("RetryStrategy")
                                    .namespace("smithy_core.interfaces.retries", ".")
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
                    .build());

    // This list contains any properties that must be added to any http-based
    // service client, except for the http client itself.
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

    /**
     * The config field for each {@code clientContextParams} entry.
     *
     * @param context the generation context.
     * @return the fields, in trait order.
     */
    public static List<ConfigProperty> clientContextProperties(GenerationContext context) {
        return List.copyOf(clientContextFields(context).values());
    }

    /**
     * The config field for each {@code clientContextParams} entry, by parameter name. A
     * field a client plugin declares for the parameter replaces the default one, named
     * {@code to_snake_case(name)}, typed and documented from the trait, defaulting to None,
     * and with no environment or profile sources. The endpoint BDD records each field's
     * name as the config attribute its parameter reads.
     *
     * @param context the generation context.
     * @return the fields, in trait order.
     */
    public static Map<String, ConfigProperty> clientContextFields(GenerationContext context) {
        // TODO: when porting to Python codegen, fail on a field name that is a Python keyword or
        // collides with another config field. No model does today, but a collision is dropped
        // silently and the rules read the other field's value.
        var model = context.model();
        var service = context.settings().service(model);
        var parameters = service.getTrait(ClientContextParamsTrait.class)
                .map(ClientContextParamsTrait::getParameters)
                .orElse(Map.of());
        var declared = new HashMap<String, ConfigProperty>();
        for (PythonIntegration integration : context.integrations()) {
            for (RuntimeClientPlugin plugin : integration.getClientPlugins(context)) {
                if (!plugin.matchesService(model, service)) {
                    continue;
                }
                for (ConfigProperty property : plugin.getConfigProperties()) {
                    var parameter = property.endpointParameter().orElse(null);
                    if (parameter == null) {
                        continue;
                    }
                    if (!parameters.containsKey(parameter)) {
                        throw new CodegenException(String.format(
                                "Config field %s is for %s, which is not a client context parameter of %s",
                                property.name(),
                                parameter,
                                service.getId()));
                    }
                    var previous = declared.putIfAbsent(parameter, property);
                    if (previous != null) {
                        throw new CodegenException(String.format(
                                "Config fields %s and %s are both for the client context parameter %s",
                                previous.name(),
                                property.name(),
                                parameter));
                    }
                }
            }
        }
        var fields = new LinkedHashMap<String, ConfigProperty>();
        for (var entry : parameters.entrySet()) {
            var name = entry.getKey();
            var property = declared.get(name);
            if (property == null) {
                var definition = entry.getValue();
                var type = switch (definition.getType()) {
                    case BOOLEAN -> "bool";
                    case STRING -> "str";
                    default -> throw new CodegenException(String.format(
                            "Unsupported type %s for client context parameter %s",
                            definition.getType(),
                            name));
                };
                property = ConfigProperty.builder()
                        .name(CaseUtils.toSnakeCase(name))
                        .type(Symbol.builder().name(type).build())
                        .documentation(definition.getDocumentation()
                                .orElse("The " + name + " endpoint parameter."))
                        .build();
            }
            fields.put(name, property);
        }
        return fields;
    }

    /**
     * The endpoint rules extensions that client plugins register for the service, in
     * integration order. The default endpoint resolver gets them.
     *
     * @param context the generation context.
     * @return the extensions.
     */
    public static List<EndpointRulesExtension> endpointRulesExtensions(GenerationContext context) {
        var service = context.settings().service(context.model());
        var extensions = new ArrayList<EndpointRulesExtension>();
        for (PythonIntegration integration : context.integrations()) {
            for (RuntimeClientPlugin plugin : integration.getClientPlugins(context)) {
                if (plugin.matchesService(context.model(), service)) {
                    plugin.getEndpointRulesExtension().ifPresent(extensions::add);
                }
            }
        }
        return extensions;
    }

    /**
     * Writes the expression that builds the default endpoint resolver, which evaluates
     * the service's endpoint BDD with the registered rules extensions.
     *
     * @param context the generation context.
     * @param writer the writer to write the expression with, inline.
     */
    public static void writeDefaultEndpointResolver(GenerationContext context, PythonWriter writer) {
        var bdd = EndpointBddGenerator.bddSymbol(context.settings());
        var extensions = endpointRulesExtensions(context);
        if (extensions.isEmpty()) {
            writer.writeInline("$T($T)", RuntimeTypes.BDD_ENDPOINT_RESOLVER, bdd);
            return;
        }
        writer.writeInline("$T($T, extensions=[", RuntimeTypes.BDD_ENDPOINT_RESOLVER, bdd);
        for (int i = 0; i < extensions.size(); i++) {
            writer.writeInline(i == 0 ? "$T" : ", $T", extensions.get(i).getRulesExtensionSymbol(context));
        }
        writer.writeInline("])");
    }

    private static ConfigProperty endpointResolverProperty(GenerationContext context) {
        return ConfigProperty.builder()
                .name("endpoint_resolver")
                .type(RuntimeTypes.ENDPOINT_RESOLVER)
                .documentation("""
                        The endpoint resolver used to resolve the final endpoint per-operation based on the \
                        configuration.""")
                .nullable(false)
                .initialize(writer -> {
                    writer.pushState(new InitDefaultEndpointResolverSection());
                    writer.write("self.endpoint_resolver = endpoint_resolver or $C",
                            writer.consumer(w -> writeDefaultEndpointResolver(context, w)));
                    writer.popState();
                })
                .build();
    }

    private static List<ConfigProperty> getProtocolProperties(GenerationContext context) {
        var properties = new ArrayList<ConfigProperty>();
        var protocolBuilder = ConfigProperty.builder()
                .name("protocol")
                .type(Symbol.builder()
                        .name("ClientProtocol[Any, Any]")
                        .addReference(Symbol.builder()
                                .name("ClientProtocol")
                                .namespace("smithy_core.interfaces", ".")
                                .build())
                        .build())
                .inputType(Symbol.builder()
                        .name("ClientProtocol[Any, Any] | ProtocolConstructor[ClientProtocol[Any, Any]]")
                        .addReference(Symbol.builder()
                                .name("ClientProtocol")
                                .namespace("smithy_core.interfaces", ".")
                                .build())
                        .addReference(Symbol.builder()
                                .name("ProtocolConstructor")
                                .namespace("smithy_core.interfaces", ".")
                                .addDependency(SmithyPythonDependency.SMITHY_CORE)
                                .build())
                        .build())
                .documentation("Pass a protocol class reference from smithy_aws_core.aio.protocols "
                        + "to select the protocol, e.g. protocol=AsyncAwsJson10ClientProtocol. For custom "
                        + "protocols a protocol instance may also be passed.")
                .initialize(w -> {
                    w.addStdlibImport("typing", "cast");
                    w.write("""
                            if isinstance(protocol, type):
                                protocol = protocol(_PROTOCOL_SETTINGS)
                            self.protocol = cast("$T[Any, Any]", protocol) or ${C|}""",
                            Symbol.builder()
                                    .name("ClientProtocol")
                                    .namespace("smithy_core.interfaces", ".")
                                    .build(),
                            w.consumer(writer -> context.protocolGenerator().initializeProtocol(context, writer)));
                });

        var transportBuilder = ConfigProperty.builder()
                .name("transport")
                .type(Symbol.builder()
                        .name("AsyncClientTransport[Any, Any]")
                        .addReference(Symbol.builder()
                                .name("AsyncClientTransport")
                                .namespace("smithy_core.aio.interfaces", ".")
                                .build())
                        .build())
                .documentation("The transport to use to send requests (e.g. an HTTP client). "
                        + "Operations with bidirectional event streams require a "
                        + "AsyncDuplexClientTransport, such as AsyncAWSCRTHTTPClient. Transports are "
                        + "assumed not to support duplex streaming unless they explicitly set "
                        + "SUPPORTS_DUPLEX_STREAMING to True.");

        if (context.applicationProtocol().isHttpProtocol()) {
            properties.addAll(HTTP_PROPERTIES);
            transportBuilder
                    .initialize(writer -> {
                        writer.addDependency(
                                SmithyPythonDependency.SMITHY_HTTP.withOptionalDependencies("aiohttp"));
                        writer.write("self.transport = transport or $T()",
                                RuntimeTypes.AIOHTTP_CLIENT);
                    });
        }

        properties.add(protocolBuilder.build());
        properties.add(transportBuilder.build());
        return properties;
    }

    private static List<ConfigProperty> getAuthProperties(GenerationContext context, boolean hasAuth) {
        Consumer<PythonWriter> authSchemesInit = hasAuth
                ? writer -> writeDefaultAuthSchemes(context, writer)
                : writer -> writer.write("self.auth_schemes = auth_schemes or {}");

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
        Consumer<PythonWriter> resolverInit = writer -> writer.write(
                "self.auth_scheme_resolver = auth_scheme_resolver or $T()",
                defaultResolver);

        return List.of(
                ConfigProperty.builder()
                        .name("auth_schemes")
                        .type(Symbol.builder()
                                .name("dict[ShapeID, AsyncAuthScheme[Any, Any, Any, Any]]")
                                .addReference(Symbol.builder()
                                        .name("ShapeID")
                                        .namespace("smithy_core.shapes", ".")
                                        .addDependency(SmithyPythonDependency.SMITHY_CORE)
                                        .build())
                                .addReference(ASYNC_AUTH_SCHEME)
                                .addReference(Symbol.builder()
                                        .name("Any")
                                        .namespace("typing", ".")
                                        .putProperty(SymbolProperties.STDLIB, true)
                                        .build())
                                .build())
                        .documentation("A map of auth scheme ids to auth schemes.")
                        .nullable(false)
                        .initialize(authSchemesInit)
                        .build(),
                ConfigProperty.builder()
                        .name("auth_scheme_resolver")
                        .type(resolverType)
                        .documentation(
                                "An auth scheme resolver that determines the auth scheme for each operation.")
                        .nullable(false)
                        .initialize(resolverInit)
                        .build());
    }

    private static void writeDefaultAuthSchemes(GenerationContext context, PythonWriter writer) {
        writer.pushState();
        var service = context.settings().service(context.model());

        writer.openBlock("self.auth_schemes = auth_schemes or {");
        for (PythonIntegration integration : context.integrations()) {
            for (RuntimeClientPlugin plugin : integration.getClientPlugins(context)) {
                if (plugin.matchesService(context.model(), service) && plugin.getAuthScheme().isPresent()) {
                    var scheme = plugin.getAuthScheme().get();
                    writer.write("$T($S): ${C|},",
                            RuntimeTypes.SHAPE_ID,
                            scheme.getAuthTrait(),
                            writer.consumer(w -> scheme.initializeScheme(context, writer, service)));
                }
            }
        }
        writer.closeBlock("}");
        writer.popState();
    }

    @Override
    public void run() {
        var asyncConfig = CodegenUtils.getAsyncConfigSymbol(settings, context.model());
        generateConfigModule(asyncConfig, false);
        generateConfigModule(asyncConfig, true);
    }

    private void generateConfigModule(Symbol asyncConfig, boolean sync) {
        var mapper = sync ? SyncVariant.mapper(settings) : UnaryOperator.<Symbol>identity();
        var config = mapper.apply(asyncConfig);
        var plugin = mapper.apply(CodegenUtils.getPluginSymbol(settings));
        context.writerDelegator().useFileWriter(config.getDefinitionFile(), config.getNamespace(), writer -> {
            writer.setSymbolMapper(mapper);
            writeInterceptorsType(writer, sync ? ".models" : "..models");
            stageProtocolSettings(context, writer);

            // AWS integrations intercept this section to emit a config subclass.
            if (CodegenUtils.isAwsService(context)) {
                writer.pushState(new AsyncConfigSection(sync));
                writer.popState();
            } else {
                generateConfig(context, writer, config);
            }

            // Plugins are plain callables over the config; a protocol class would add
            // nothing but ceremony.
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

    // Emit the shared _PROTOCOL_SETTINGS bag as the union of the fields every protocol
    // the service resolves needs.
    private void stageProtocolSettings(GenerationContext context, PythonWriter writer) {
        var generator = context.protocolGenerator();
        if (generator == null) {
            return;
        }

        // Map every generator any integration supplies to its protocol trait id, then
        // ask each protocol the service resolves what extra fields it needs.
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
        // The protocol reads its own eventStreamHttp off the service schema's protocol
        // trait, so pass the schema rather than a flattened per-service value.
        var serviceSchema = context.symbolProvider()
                .toSymbol(service)
                .expectProperty(SymbolProperties.SCHEMA)
                .getSymbol();
        params.append(", service_schema=$T");
        args.add(serviceSchema);

        args.add(0, RuntimeTypes.PROTOCOL_SETTINGS);
        writer.write("_PROTOCOL_SETTINGS = $T(" + params + ")", args.toArray());
    }

    private void writeInterceptorsType(PythonWriter writer, String modelsModule) {
        var symbolProvider = context.symbolProvider();
        var operationShapes = TopDownIndex.of(context.model())
                .getContainedOperations(settings.service());

        writer.addStdlibImports("typing", java.util.Set.of("TYPE_CHECKING", "Any", "Union"));
        writer.addDependency(SmithyPythonDependency.SMITHY_CORE);

        // Collect the input/output class names referenced by the interceptor union.
        // They are emitted as a TYPE_CHECKING-only import + alias so they are NOT built
        // at runtime: the models module builds classes lazily, and the interceptor union
        // is only ever read as a type (the `interceptors` field annotation is a string
        // under `from __future__ import annotations`).
        var names = new java.util.TreeSet<String>();
        var unionMembers = new java.util.ArrayList<String>();
        for (var operation : operationShapes) {
            var input = symbolProvider.toSymbol(
                    context.model().expectShape(operation.getInputShape())).getName();
            var output = symbolProvider.toSymbol(
                    context.model().expectShape(operation.getOutputShape())).getName();
            names.add(input);
            names.add(output);
            unionMembers.add(String.format("Interceptor[%s, %s, Any, Any]", input, output));
        }

        writer.write("if TYPE_CHECKING:").indent();
        writer.write("from smithy_core.interceptors import Interceptor");
        writer.openBlock("from $L import (", ")", modelsModule, () -> {
            for (var name : names) {
                writer.write("$L,", name);
            }
        });
        writer.write("");
        writer.openBlock("_ServiceInterceptor = Union[", "]", () -> {
            for (var member : unionMembers) {
                writer.write("$L,", member);
            }
        });
        writer.dedent();
        // Runtime fallback: the precise union above is TYPE_CHECKING-only (it names every
        // input/output class, which would build them all eagerly). At runtime the alias
        // is Any so the `interceptors` field annotation resolves without building models.
        writer.write("else:").indent();
        writer.write("_ServiceInterceptor = Any");
        writer.dedent();
        writer.write("");
    }

    private void generateConfig(GenerationContext context, PythonWriter writer, Symbol configSymbol) {

        // Initialize a set of config properties with our base properties.
        var properties = new TreeSet<>(Comparator.comparing(ConfigProperty::name));
        properties.addAll(BASE_PROPERTIES);
        properties.add(endpointResolverProperty(context));
        properties.addAll(getProtocolProperties(context));
        properties.addAll(clientContextProperties(context));

        var serviceIndex = ServiceIndex.of(context.model());
        boolean hasAuth = !serviceIndex.getAuthSchemes(settings.service()).isEmpty();
        properties.addAll(getAuthProperties(context, hasAuth));
        if (hasAuth) {
            writer.onSection(new AddAuthHelper());
        }

        var model = context.model();
        var service = context.settings().service(model);

        // Add any relevant config properties from plugins.
        for (PythonIntegration integration : context.integrations()) {
            for (RuntimeClientPlugin plugin : integration.getClientPlugins(context)) {
                if (plugin.matchesService(model, service)) {
                    properties.addAll(plugin.getConfigProperties());
                }
            }
        }

        var finalProperties = List.copyOf(properties);
        final String serviceId = context.settings()
                .service(context.model())
                .getTrait(ServiceTrait.class)
                .map(ServiceTrait::getSdkId)
                .orElse(context.settings().service().getName());
        writer.pushState(new ConfigSection(finalProperties));
        writer.addLocallyDefinedSymbol(configSymbol);
        writer.addStdlibImport("dataclasses", "dataclass");
        writer.write("""
                @dataclass(init=False)
                class $L:
                    \"""Configuration for $L.\"""

                    ${C|}

                    def __init__(
                        self,
                        *,
                        ${C|}
                    ):
                        ${C|}
                """,
                configSymbol.getName(),
                serviceId,
                writer.consumer(w -> writePropertyDeclarations(w, finalProperties)),
                writer.consumer(w -> writeInitParams(w, finalProperties)),
                writer.consumer(w -> initializeProperties(w, finalProperties)));
        writer.popState();
    }

    private void writePropertyDeclarations(PythonWriter writer, Collection<ConfigProperty> properties) {
        for (ConfigProperty property : properties) {
            var formatString = property.isNullable()
                    ? "$L: $T | None"
                    : "$L: $T";
            writer.write(formatString, property.name(), property.type());
            writer.writeDocs(property.documentation(), context);
            writer.write("");
        }
    }

    private void writeInitParams(PythonWriter writer, Collection<ConfigProperty> properties) {
        for (ConfigProperty property : properties) {
            writer.write("$L: $T | None = None,", property.name(), property.inputType());
        }
    }

    private void initializeProperties(PythonWriter writer, Collection<ConfigProperty> properties) {
        for (ConfigProperty property : properties) {
            property.initialize(writer);
        }
    }

    private static final Symbol ASYNC_AUTH_SCHEME = Symbol.builder()
            .name("AsyncAuthScheme")
            .namespace("smithy_core.aio.interfaces.auth", ".")
            .addDependency(SmithyPythonDependency.SMITHY_CORE)
            .build();

    private static final class AddAuthHelper implements CodeInterceptor<ConfigSection, PythonWriter> {
        @Override
        public Class<ConfigSection> sectionType() {
            return ConfigSection.class;
        }

        @Override
        public void write(PythonWriter writer, String previousText, ConfigSection section) {
            // First write the previous text, the generated config, back out. The entire
            // section would otherwise be erased and replaced with what is written in this
            // method.
            writer.write(previousText);

            // Add the helper function to the end of the config definition.
            // Note that this is indented to keep it at the proper indentation level.
            writer.write("""

                        def set_auth_scheme(self, scheme: $T[Any, Any, Any, Any]) -> None:
                            \"""
                            Sets the implementation of an auth scheme.

                            Using this method ensures the correct key is used.

                            Args:
                                scheme:
                                    The auth scheme to add.
                            \"""
                            self.auth_schemes[scheme.scheme_id] = scheme
                    """, ASYNC_AUTH_SCHEME);
        }
    }
}
