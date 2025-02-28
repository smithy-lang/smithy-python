package software.amazon.smithy.python.codegen.integrations;

import java.util.List;
import software.amazon.smithy.python.codegen.ConfigProperty;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.writer.PythonWriter;

/**
 * Interface for Endpoints Generators.
 * Endpoints Generators are responsible for defining the client configuration
 * required for resolving endpoints, this includes an appropriately typed
 * `endpoint_resolver` and any other configuration properties such as `endpoint_uri`.
 * Endpoint generators are also responsible for rendering the logic in the client's
 * request execution stack that sets the destination on the transport request.
 * Endpoints Generators are only applied to services that use an HTTP transport.
 */
public interface EndpointsGenerator {

    /**
     * Endpoints Generators are responsible for defining the client configuration
     * required for resolving endpoints, this must include an appropriately typed
     * `endpoint_resolver` and any other configuration properties such as `endpoint_uri`
     *
     * @param context generation context.
     * @return list of client config required to resolve endpoints.
     */
    List<ConfigProperty> endpointsConfig(GenerationContext context);

    /**
     * Render the logic in the client's request execution stack that constructs
     * `endpoint_parameters`. Implementations must add required dependencies and import statements
     * and must ensure the `endpoint_parameters` variable is set.
     *
     * @param context generation context
     * @param writer writer to write out logic to construct `endpoint_parameters`.
     */
    void renderEndpointParameterConstruction(GenerationContext context, PythonWriter writer);
}
