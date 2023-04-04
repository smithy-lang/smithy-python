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
import java.util.List;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.model.knowledge.TopDownIndex;
import software.amazon.smithy.python.codegen.integration.PythonIntegration;
import software.amazon.smithy.python.codegen.integration.RuntimeClientPlugin;

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
                .namespace("smithy_python.interfaces.retries", ".")
                .addDependency(SmithyPythonDependency.SMITHY_PYTHON)
                .build())
            .documentation("The retry strategy for issuing retry tokens and computing retry delays.")
            .nullable(false)
            .initialize(writer -> {
                writer.addDependency(SmithyPythonDependency.SMITHY_PYTHON);
                writer.addImport("smithy_python._private.retries", "SimpleRetryStrategy");
                writer.write("self.retry_strategy = retry_strategy or SimpleRetryStrategy()");
            })
            .build()
    );

    // This list contains any properties that must be added to any http-based
    // service client.
    private static final List<ConfigProperty> HTTP_PROPERTIES = Arrays.asList(
        ConfigProperty.builder()
            .name("http_client")
            .type(Symbol.builder()
                .name("HTTPClient")
                .namespace("smithy_python.interfaces.http", ".")
                .addDependency(SmithyPythonDependency.SMITHY_PYTHON)
                .build())
            .documentation("The HTTP client used to make requests.")
            .nullable(false)
            .initialize(writer -> {
                writer.addDependency(SmithyPythonDependency.SMITHY_PYTHON);
                writer.addImport("smithy_python._private.http.aiohttp_client", "AIOHTTPClient");
                writer.write("self.http_client = http_client or AIOHTTPClient()");
            })
            .build(),
        ConfigProperty.builder()
            .name("http_request_config")
            .type(Symbol.builder()
                .name("HTTPRequestConfiguration")
                .namespace("smithy_python.interfaces.http", ".")
                .addDependency(SmithyPythonDependency.SMITHY_PYTHON)
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
                    .putProperty("stdlib", true)
                    .build())
                .addReference(Symbol.builder()
                    .name("EndpointResolver")
                    .namespace("smithy_python.interfaces.http", ".")
                    .addDependency(SmithyPythonDependency.SMITHY_PYTHON)
                    .build())
                .build())
            .documentation("""
                    The endpoint resolver used to resolve the final endpoint per-operation based on the \
                    configuration.""")
            .nullable(false)
            .initialize(writer -> {
                writer.addImport("smithy_python._private.http", "StaticEndpointResolver");
                writer.write("self.endpoint_resolver = endpoint_resolver or StaticEndpointResolver()");
            })
            .build(),
        ConfigProperty.builder()
            .name("endpoint_uri")
            .type(Symbol.builder()
                .name("str | URI")
                .addReference(Symbol.builder()
                    .name("URI")
                    .namespace("smithy_python.interfaces", ".")
                    .addDependency(SmithyPythonDependency.SMITHY_PYTHON)
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
                .getContainedOperations(settings.getService());

        writer.addStdlibImport("typing", "Union");
        writer.addDependency(SmithyPythonDependency.SMITHY_PYTHON);
        writer.getImportContainer().addImport("smithy_python.interfaces.interceptor", "Interceptor", "Interceptor");

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
        if (context.applicationProtocol().isHttpProtocol()) {
            properties.addAll(HTTP_PROPERTIES);
        }

        var model = context.model();
        var service = context.settings().getService(model);

        // Add any relevant config properties from plugins.
        for (PythonIntegration integration : context.integrations()) {
            for (RuntimeClientPlugin plugin : integration.getClientPlugins()) {
                if (plugin.matchesService(model, service)) {
                    properties.addAll(plugin.getConfigProperties());
                }
            }
        }

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
            """, symbol.getName(), context.settings().getService().getName(),
            writer.consumer(w -> writePropertyDeclarations(w, properties)),
            writer.consumer(w -> writeInitParams(w, properties)),
            writer.consumer(w -> documentProperties(w, properties)),
            writer.consumer(w -> initializeProperties(w, properties)));
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
}
