package software.amazon.smithy.python.codegen.generators;

import java.util.List;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.python.codegen.CodegenUtils;
import software.amazon.smithy.python.codegen.ConfigProperty;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.SmithyPythonDependency;
import software.amazon.smithy.python.codegen.SymbolProperties;
import software.amazon.smithy.python.codegen.integrations.EndpointsGenerator;
import software.amazon.smithy.python.codegen.writer.PythonWriter;

public class StaticEndpointsGenerator implements EndpointsGenerator {
    @Override
    public List<ConfigProperty> endpointsConfig(GenerationContext context) {
        return List.of(ConfigProperty.builder()
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
                        .build());
    }

    @Override
    public void generateEndpoints(GenerationContext context, PythonWriter writer) {
        var errorSymbol = CodegenUtils.getServiceError(context.settings());

        writer.addDependency(SmithyPythonDependency.SMITHY_CORE);
        writer.addDependency(SmithyPythonDependency.SMITHY_HTTP);
        writer.addImport("smithy_http.endpoints", "StaticEndpointParams");
        writer.addImport("smithy_core", "URI");
        writer.write("""
                            if config.endpoint_uri is None:
                                raise $1T(
                                    "No endpoint_uri found on the operation config."
                                )

                            endpoint = await config.endpoint_resolver.resolve_endpoint(
                                StaticEndpointParams(uri=config.endpoint_uri)
                            )
                            if not endpoint.uri.path:
                                path = ""
                            elif endpoint.uri.path.endswith("/"):
                                path = endpoint.uri.path[:-1]
                            else:
                                path = endpoint.uri.path
                            if context.transport_request.destination.path:
                                path += context.transport_request.destination.path
                            context._transport_request.destination = URI(
                                scheme=endpoint.uri.scheme,
                                host=context.transport_request.destination.host + endpoint.uri.host,
                                path=path,
                                port=endpoint.uri.port,
                                query=context.transport_request.destination.query,
                            )
                            context._transport_request.fields.extend(endpoint.headers)

                    """, errorSymbol);
    }
}
