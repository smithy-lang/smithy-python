package software.amazon.smithy.python.aws.codegen;

import java.util.List;
import software.amazon.smithy.aws.traits.ServiceTrait;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.python.codegen.CodegenUtils;
import software.amazon.smithy.python.codegen.ConfigProperty;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.SmithyPythonDependency;
import software.amazon.smithy.python.codegen.integrations.EndpointsGenerator;
import software.amazon.smithy.python.codegen.writer.PythonWriter;

/**
 * Generates endpoint config and resolution logic for standard regional endpoints.
 */
public class AwsRegionalEndpointsGenerator implements EndpointsGenerator {
    @Override
    public List<ConfigProperty> endpointsConfig(GenerationContext context) {
        return List.of(ConfigProperty.builder()
                        .name("endpoint_resolver")
                        .type(Symbol.builder()
                                .name("EndpointResolver[RegionalEndpointParameters]")
                                .addReference(Symbol.builder()
                                        .name("RegionalEndpointParameters")
                                        .namespace(AwsPythonDependency.SMITHY_AWS_CORE.packageName() + ".endpoints.standard_regional", ".")
                                        .addDependency(AwsPythonDependency.SMITHY_AWS_CORE)
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
                            writer.addImport("smithy_aws_core.endpoints.standard_regional", "StandardRegionalEndpointsResolver");
                            String endpointPrefix = context.settings().service(context.model())
                                    .getTrait(ServiceTrait.class)
                                    .map(ServiceTrait::getEndpointPrefix)
                                    .orElse(context.settings().service().getName());

                            writer.write(
                                    "self.endpoint_resolver = endpoint_resolver or StandardRegionalEndpointsResolver(endpoint_prefix='$L')",
                                    endpointPrefix);
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
                        .name("region")
                        .type(Symbol.builder().name("str").build())
                        .documentation(" The AWS region to connect to. The configured region is used to "
                                + "determine the service endpoint.")
                        .build());
    }

    @Override
    public void renderEndpointParameterConstruction(GenerationContext context, PythonWriter writer) {

        writer.addDependency(AwsPythonDependency.SMITHY_AWS_CORE);
        writer.addImport("smithy_aws_core.endpoints.standard_regional", "RegionalEndpointParameters");
        writer.write("""
                        endpoint_parameters = RegionalEndpointParameters(
                            sdk_endpoint=config.endpoint_uri,
                            region=config.region
                        )
                """);
    }
}
