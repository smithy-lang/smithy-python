/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.model.knowledge.EventStreamIndex;
import software.amazon.smithy.model.knowledge.ServiceIndex;
import software.amazon.smithy.model.knowledge.TopDownIndex;
import software.amazon.smithy.model.node.ArrayNode;
import software.amazon.smithy.model.node.StringNode;
import software.amazon.smithy.model.shapes.OperationShape;
import software.amazon.smithy.python.codegen.integration.PythonIntegration;
import software.amazon.smithy.python.codegen.integration.RuntimeClientPlugin;
import software.amazon.smithy.python.codegen.sections.ConfigSection;
import software.amazon.smithy.utils.CodeInterceptor;

/**
 * Generates the client's config object.
 */
final class ConfigGenerator implements Runnable {

    // This list contains any properties that should unconditionally be added to every
    // config object. This should be as minimal as possible, and importantly should
    // not contain any HTTP related config since Smithy is transport agnostic.
    private static final List<ConfigProperty> BASE_PROPERTIES = Arrays.asList(
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
            .build()
    );

    // This list contains any properties that must be added to any http-based
    // service client, except for the http client itself.
    private static final List<ConfigProperty> HTTP_PROPERTIES = Arrays.asList(
        ConfigProperty.builder()
            .name("http_request_config")
            .type(Symbol.builder()
                .name("HTTPRequestConfiguration")
                .namespace("smithy_http.interfaces", ".")
                .addDependency(SmithyPythonDependency.SMITHY_HTTP)
                .build())
            .documentation("Configuration for individual HTTP requests.")
            .build(),
        ConfigProperty.builder()
            .name("endpoint_resolver")
            .type(Symbol.builder()
                .name("EndpointResolver[Any]")
                .addReference(Symbol.builder()
                    .name("Any")
                    .namespace("typing", ".")
                    .putProperty(SymbolProperties.STDLIB, true)
                    .build())
                .addReference(Symbol.builder()
                    .name("EndpointResolver")
                    .namespace("smithy_http.aio.interfaces", ".")
                    .addDependency(SmithyPythonDependency.SMITHY_HTTP)
                    .build())
                .build())
            .documentation("""
                    The endpoint resolver used to resolve the final endpoint per-operation based on the \
                    configuration.""")
            .nullable(false)
            .initialize(writer -> {
                writer.addImport("smithy_http.aio.endpoints", "StaticEndpointResolver");
                writer.write("self.endpoint_resolver = endpoint_resolver or StaticEndpointResolver()");
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
            .build()
    );

    private final PythonSettings settings;
    private final GenerationContext context;

    ConfigGenerator(PythonSettings settings, GenerationContext context) {
        this.context = context;
        this.settings = settings;
    }

    private static List<ConfigProperty> getHttpProperties(GenerationContext context) {
        var properties = new ArrayList<ConfigProperty>(HTTP_PROPERTIES.size() + 1);
        var clientBuilder = ConfigProperty.builder()
                .name("http_client")
                .type(Symbol.builder()
                        .name("HTTPClient")
                        .namespace("smithy_http.aio.interfaces", ".")
                        .addDependency(SmithyPythonDependency.SMITHY_HTTP)
                        .build())
                .documentation("The HTTP client used to make requests.")
                .nullable(false);

        if (usesHttp2(context)) {
            clientBuilder
                .initialize(writer -> {
                    writer.addDependency(SmithyPythonDependency.SMITHY_HTTP.withOptionalDependencies("awscrt"));
                    writer.addImport("smithy_http.aio.crt", "AWSCRTHTTPClient");
                    writer.write("self.http_client = http_client or AWSCRTHTTPClient()");
                });

        } else {
            clientBuilder
                .initialize(writer -> {
                    writer.addDependency(SmithyPythonDependency.SMITHY_HTTP.withOptionalDependencies("aiohttp"));
                    writer.addImport("smithy_http.aio.aiohttp", "AIOHTTPClient");
                    writer.write("self.http_client = http_client or AIOHTTPClient()");
                });
        }
        properties.add(clientBuilder.build());

        properties.addAll(HTTP_PROPERTIES);
        return List.copyOf(properties);
    }

    private static boolean usesHttp2(GenerationContext context) {
        var configuration = context.applicationProtocol().configuration();
        var httpVersions = configuration.getArrayMember("http")
                .orElse(ArrayNode.arrayNode())
                .getElementsAs(StringNode.class)
                .stream().map(node -> node.getValue().toLowerCase(Locale.ENGLISH)).toList();

        // An explicit http2 configuration
        if (httpVersions.contains("h2")) {
            return true;
        }

        // Bidirectional streaming REQUIRES h2 inherently
        var eventIndex = EventStreamIndex.of(context.model());
        var topDownIndex = TopDownIndex.of(context.model());
        for (OperationShape operation : topDownIndex.getContainedOperations(context.settings().service())) {
            if (eventIndex.getInputInfo(operation).isPresent() && eventIndex.getOutputInfo(operation).isPresent()) {
                return true;
            }
        }

        return false;
    }

    private static List<ConfigProperty> getHttpAuthProperties(GenerationContext context) {
        return List.of(
            ConfigProperty.builder()
                .name("http_auth_schemes")
                .type(Symbol.builder()
                    .name("dict[str, HTTPAuthScheme[Any, Any, Any, Any]]")
                    .addReference(Symbol.builder()
                        .name("HTTPAuthScheme")
                        .namespace("smithy_http.aio.interfaces.auth", ".")
                        .addDependency(SmithyPythonDependency.SMITHY_HTTP)
                        .build())
                    .addReference(Symbol.builder()
                        .name("Any")
                        .namespace("typing", ".")
                        .putProperty(SymbolProperties.STDLIB, true)
                        .build())
                    .build())
                .documentation("A map of http auth scheme ids to http auth schemes.")
                .nullable(false)
                .initialize(writer -> writeDefaultHttpAuthSchemes(context, writer))
                .build(),
            ConfigProperty.builder()
                .name("http_auth_scheme_resolver")
                .type(CodegenUtils.getHttpAuthSchemeResolverSymbol(context.settings()))
                .documentation("An http auth scheme resolver that determines the auth scheme for each operation.")
                .nullable(false)
                .initialize(writer -> writer.write(
                    "self.http_auth_scheme_resolver = http_auth_scheme_resolver or HTTPAuthSchemeResolver()"))
                .build()
        );
    }

    private static void writeDefaultHttpAuthSchemes(GenerationContext context, PythonWriter writer) {
        var supportedAuthSchemes = new LinkedHashMap<String, Symbol>();
        var service = context.settings().service(context.model());
        for (PythonIntegration integration : context.integrations()) {
            for (RuntimeClientPlugin plugin : integration.getClientPlugins()) {
                if (plugin.matchesService(context.model(), service)
                        && plugin.getAuthScheme().isPresent()
                        && plugin.getAuthScheme().get().getApplicationProtocol().isHttpProtocol()) {
                    var scheme = plugin.getAuthScheme().get();
                    supportedAuthSchemes.put(scheme.getAuthTrait().toString(), scheme.getAuthSchemeSymbol(context));
                }
            }
        }
        writer.pushState();
        writer.putContext("authSchemes", supportedAuthSchemes);
        writer.write("""
            self.http_auth_schemes = http_auth_schemes or {
                ${#authSchemes}
                ${key:S}: ${value:T}(),
                ${/authSchemes}
            }
            """);
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
        var symbol = CodegenUtils.getConfigSymbol(context.settings());

        // Initialize the list of config properties with our base properties. Here a new
        // list is constructed because that base list is immutable.
        var properties = new ArrayList<>(BASE_PROPERTIES);

        // Smithy is transport agnostic, so we don't add http-related properties by default.
        // Nevertheless, HTTP is the most common use case so we standardize those settings
        // and add them in if the protocol is going to need them.
        var serviceIndex = ServiceIndex.of(context.model());
        if (context.applicationProtocol().isHttpProtocol()) {
            properties.addAll(getHttpProperties(context));
            if (!serviceIndex.getAuthSchemes(settings.service()).isEmpty()) {
                properties.addAll(getHttpAuthProperties(context));
                writer.onSection(new AddAuthHelper());
            }
        }

        var model = context.model();
        var service = context.settings().service(model);

        // Add any relevant config properties from plugins.
        for (PythonIntegration integration : context.integrations()) {
            for (RuntimeClientPlugin plugin : integration.getClientPlugins()) {
                if (plugin.matchesService(model, service)) {
                    properties.addAll(plugin.getConfigProperties());
                }
            }
        }

        var finalProperties = List.copyOf(properties);
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
            """, symbol.getName(), context.settings().service().getName(),
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

                    def set_http_auth_scheme(self, scheme: HTTPAuthScheme[Any, Any, Any, Any]) -> None:
                        \"""Sets the implementation of an auth scheme.

                        Using this method ensures the correct key is used.

                        :param scheme: The auth scheme to add.
                        \"""
                        self.http_auth_schemes[scheme.scheme_id] = scheme
                """);
        }
    }
}
