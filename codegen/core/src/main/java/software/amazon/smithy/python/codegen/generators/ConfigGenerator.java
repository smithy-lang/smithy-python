/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.generators;

import java.util.ArrayList;
import java.util.Collection;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import java.util.TreeSet;
import software.amazon.smithy.aws.traits.ServiceTrait;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.model.knowledge.EventStreamIndex;
import software.amazon.smithy.model.knowledge.ServiceIndex;
import software.amazon.smithy.model.knowledge.TopDownIndex;
import software.amazon.smithy.model.node.ArrayNode;
import software.amazon.smithy.model.node.StringNode;
import software.amazon.smithy.model.shapes.OperationShape;
import software.amazon.smithy.python.codegen.CodegenUtils;
import software.amazon.smithy.python.codegen.ConfigProperty;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.PythonSettings;
import software.amazon.smithy.python.codegen.SmithyPythonDependency;
import software.amazon.smithy.python.codegen.SymbolProperties;
import software.amazon.smithy.python.codegen.integrations.PythonIntegration;
import software.amazon.smithy.python.codegen.integrations.RuntimeClientPlugin;
import software.amazon.smithy.python.codegen.sections.ConfigSection;
import software.amazon.smithy.python.codegen.sections.InitDefaultEndpointResolverSection;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
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
                            .name("RetryStrategy")
                            .namespace("smithy_core.interfaces.retries", ".")
                            .addDependency(SmithyPythonDependency.SMITHY_CORE)
                            .build())
                    .documentation("The retry strategy for issuing retry tokens and computing retry delays.")
                    .nullable(false)
                    .initialize(writer -> {
                        writer.addDependency(SmithyPythonDependency.SMITHY_CORE);
                        writer.addImport("smithy_core.retries", "SimpleRetryStrategy");
                        writer.write("self.retry_strategy = retry_strategy or SimpleRetryStrategy()");
                    })
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
                    .type(Symbol.builder()
                            .name("_EndpointResolver")
                            .build())
                    .documentation("""
                            The endpoint resolver used to resolve the final endpoint per-operation based on the \
                            configuration.""")
                    .nullable(false)
                    .initialize(writer -> {
                        writer.addImport("smithy_core.aio.interfaces", "EndpointResolver", "_EndpointResolver");
                        writer.pushState(new InitDefaultEndpointResolverSection());
                        writer.addImport("smithy_core.aio.endpoints", "StaticEndpointResolver");
                        writer.write("self.endpoint_resolver = endpoint_resolver or StaticEndpointResolver()");
                        writer.popState();
                    })
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
                .documentation("The protocol to serialize and deserialize requests with.")
                .initialize(w -> {
                    w.write("self.protocol = protocol or ${C|}",
                            w.consumer(writer -> context.protocolGenerator().initializeProtocol(context, writer)));
                });

        var transportBuilder = ConfigProperty.builder()
                .name("transport")
                .type(Symbol.builder()
                        .name("ClientTransport[Any, Any]")
                        .addReference(Symbol.builder()
                                .name("ClientTransport")
                                .namespace("smithy_core.aio.interfaces", ".")
                                .build())
                        .build())
                .documentation("The transport to use to send requests (e.g. an HTTP client).");

        if (context.applicationProtocol().isHttpProtocol()) {
            properties.addAll(HTTP_PROPERTIES);
            if (usesHttp2(context)) {
                transportBuilder
                        .initialize(writer -> {
                            writer.addDependency(SmithyPythonDependency.SMITHY_HTTP.withOptionalDependencies("awscrt"));
                            writer.addImport("smithy_http.aio.crt", "AWSCRTHTTPClient");
                            writer.write("self.transport = transport or AWSCRTHTTPClient()");
                        });

            } else {
                transportBuilder
                        .initialize(writer -> {
                            writer.addDependency(
                                    SmithyPythonDependency.SMITHY_HTTP.withOptionalDependencies("aiohttp"));
                            writer.addImport("smithy_http.aio.aiohttp", "AIOHTTPClient");
                            writer.write("self.transport = transport or AIOHTTPClient()");
                        });
            }
        }

        properties.add(protocolBuilder.build());
        properties.add(transportBuilder.build());
        return properties;
    }

    private static boolean usesHttp2(GenerationContext context) {
        var configuration = context.applicationProtocol().configuration();
        var httpVersions = configuration.getArrayMember("http")
                .orElse(ArrayNode.arrayNode())
                .getElementsAs(StringNode.class)
                .stream()
                .map(node -> node.getValue().toLowerCase(Locale.ENGLISH))
                .toList();

        // An explicit http2 configuration
        if (httpVersions.contains("h2")) {
            return true;
        }

        // enable CRT/http2 client if the service supports any event streams (single or bi-directional)
        // TODO: Long term, only bi-directional evenstreams strictly require h2
        var eventIndex = EventStreamIndex.of(context.model());
        var topDownIndex = TopDownIndex.of(context.model());
        for (OperationShape operation : topDownIndex.getContainedOperations(context.settings().service())) {
            if (eventIndex.getInputInfo(operation).isPresent() || eventIndex.getOutputInfo(operation).isPresent()) {
                return true;
            }
        }

        return false;
    }

    private static List<ConfigProperty> getAuthProperties(GenerationContext context) {
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
                        .initialize(writer -> writeDefaultAuthSchemes(context, writer))
                        .build(),
                ConfigProperty.builder()
                        .name("auth_scheme_resolver")
                        .type(CodegenUtils.getHttpAuthSchemeResolverSymbol(context.settings()))
                        .documentation(
                                "An auth scheme resolver that determines the auth scheme for each operation.")
                        .nullable(false)
                        .initialize(writer -> writer.write(
                                "self.auth_scheme_resolver = auth_scheme_resolver or HTTPAuthSchemeResolver()"))
                        .build());
    }

    private static void writeDefaultAuthSchemes(GenerationContext context, PythonWriter writer) {
        writer.pushState();
        var service = context.settings().service(context.model());

        writer.openBlock("self.auth_schemes = auth_schemes or {");
        writer.addImport("smithy_core.shapes", "ShapeID");
        for (PythonIntegration integration : context.integrations()) {
            for (RuntimeClientPlugin plugin : integration.getClientPlugins(context)) {
                if (plugin.matchesService(context.model(), service) && plugin.getAuthScheme().isPresent()) {
                    var scheme = plugin.getAuthScheme().get();
                    writer.write("ShapeID($S): ${C|},",
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
        var config = CodegenUtils.getConfigSymbol(context.settings());
        context.writerDelegator().useFileWriter(config.getDefinitionFile(), config.getNamespace(), writer -> {
            writeInterceptorsType(writer);
            generateConfig(context, writer);
        });

        // Generate the plugin symbol. This is just a callable. We could do something
        // like have a class to implement, but that seems unnecessarily burdensome for
        // a single function.
        var plugin = CodegenUtils.getPluginSymbol(context.settings());
        context.writerDelegator().useFileWriter(plugin.getDefinitionFile(), plugin.getNamespace(), writer -> {
            writer.addStdlibImport("typing", "Callable");
            writer.addStdlibImport("typing", "TypeAlias");
            writer.writeComment("A callable that allows customizing the config object on each request.");
            writer.write("$L: TypeAlias = Callable[[$T], None]", plugin.getName(), config);
        });
    }

    private void writeInterceptorsType(PythonWriter writer) {
        var symbolProvider = context.symbolProvider();
        var operationShapes = TopDownIndex.of(context.model())
                .getContainedOperations(settings.service());

        writer.addStdlibImport("typing", "Union");
        writer.addDependency(SmithyPythonDependency.SMITHY_CORE);
        writer.getImportContainer().addImport("smithy_core.interceptors", "Interceptor", "Interceptor");

        writer.writeInline("_ServiceInterceptor = Union[");
        var iter = operationShapes.iterator();
        while (iter.hasNext()) {
            var operation = iter.next();
            var input = symbolProvider.toSymbol(context.model().expectShape(operation.getInputShape()));
            var output = symbolProvider.toSymbol(context.model().expectShape(operation.getOutputShape()));

            // TODO: pull the transport request/response types off of the application protocol
            writer.addStdlibImport("typing", "Any");
            writer.writeInline("Interceptor[$T, $T, Any, Any]", input, output);
            if (iter.hasNext()) {
                writer.writeInline(", ");
            } else {
                writer.writeInline("]");
            }
        }
        writer.write("");
    }

    private void generateConfig(GenerationContext context, PythonWriter writer) {
        var configSymbol = CodegenUtils.getConfigSymbol(context.settings());

        // Initialize a set of config properties with our base properties.
        var properties = new TreeSet<>(Comparator.comparing(ConfigProperty::name));
        properties.addAll(BASE_PROPERTIES);
        properties.addAll(getProtocolProperties(context));

        // Add in auth configuration if the service supports auth.
        var serviceIndex = ServiceIndex.of(context.model());
        if (!serviceIndex.getAuthSchemes(settings.service()).isEmpty()) {
            properties.addAll(getAuthProperties(context));
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
                        \"""Constructor.

                        ${C|}
                        \"""
                        ${C|}
                """,
                configSymbol.getName(),
                serviceId,
                writer.consumer(w -> writePropertyDeclarations(w, finalProperties)),
                writer.consumer(w -> writeInitParams(w, finalProperties)),
                writer.consumer(w -> documentProperties(w, finalProperties)),
                writer.consumer(w -> initializeProperties(w, finalProperties)));
        writer.popState();
    }

    private void writePropertyDeclarations(PythonWriter writer, Collection<ConfigProperty> properties) {
        for (ConfigProperty property : properties) {
            var formatString = property.isNullable()
                    ? "$L: $T | None"
                    : "$L: $T";
            writer.write(formatString, property.name(), property.type());
        }
    }

    private void writeInitParams(PythonWriter writer, Collection<ConfigProperty> properties) {
        for (ConfigProperty property : properties) {
            writer.write("$L: $T | None = None,", property.name(), property.type());
        }
    }

    private void documentProperties(PythonWriter writer, Collection<ConfigProperty> properties) {
        var iter = properties.iterator();
        while (iter.hasNext()) {
            var property = iter.next();
            var docs = writer.formatDocs(String.format(":param %s: %s", property.name(), property.documentation()));

            if (iter.hasNext()) {
                docs += "\n";
            }

            writer.write(docs);
        }
    }

    private void initializeProperties(PythonWriter writer, Collection<ConfigProperty> properties) {
        for (ConfigProperty property : properties) {
            property.initialize(writer);
        }
    }

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

                        def set_auth_scheme(self, scheme: AuthScheme[Any, Any, Any, Any]) -> None:
                            \"""Sets the implementation of an auth scheme.

                            Using this method ensures the correct key is used.

                            :param scheme: The auth scheme to add.
                            \"""
                            self.auth_schemes[scheme.scheme_id] = scheme
                    """);
        }
    }
}
