/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.aws.codegen.customizations.s3;

import java.util.List;
import java.util.Map;
import java.util.Set;
import software.amazon.smithy.aws.traits.ServiceTrait;
import software.amazon.smithy.codegen.core.CodegenException;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.model.shapes.ShapeType;
import software.amazon.smithy.python.aws.codegen.AwsPythonDependency;
import software.amazon.smithy.python.codegen.ConfigProperty;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.integrations.PythonIntegration;
import software.amazon.smithy.python.codegen.integrations.RuntimeClientPlugin;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.rulesengine.traits.ClientContextParamsTrait;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Adds the S3 and S3 Control config fields for client context parameters that resolve
 * from the environment and the shared config file, and names the {@code Accelerate} field
 * {@code use_accelerate_endpoint}, as botocore does.
 */
@SmithyInternalApi
public final class S3EndpointConfigIntegration implements PythonIntegration {

    private static final Set<String> SDK_IDS = Set.of("S3", "S3 Control");

    /**
     * The field for each client context parameter, by parameter. A field with an environment
     * variable and a profile key resolves from them; one without is set in code only.
     */
    private static final Map<String, S3Field> FIELDS = Map.of(
            "Accelerate",
            new S3Field("use_accelerate_endpoint", null, null),
            "UseArnRegion",
            new S3Field("use_arn_region", "AWS_S3_USE_ARN_REGION", "s3_use_arn_region"),
            "DisableMultiRegionAccessPoints",
            new S3Field("disable_multi_region_access_points",
                    "AWS_S3_DISABLE_MULTIREGION_ACCESS_POINTS",
                    "s3_disable_multiregion_access_points"),
            "DisableS3ExpressSessionAuth",
            new S3Field("disable_s3_express_session_auth",
                    "AWS_S3_DISABLE_EXPRESS_SESSION_AUTH",
                    "s3_disable_express_session_auth"));

    private static final Symbol ASYNC_SHARED_CONFIG_CONTEXT = awsCoreSymbol(
            "smithy_aws_core.aio.config",
            "AsyncSharedConfigContext");
    private static final Symbol RESOLVED = awsCoreSymbol("smithy_aws_core.config.types", "Resolved");
    private static final Symbol RESOLVE_BOOL = awsCoreSymbol(
            "smithy_aws_core.aio.config.resolvers",
            "resolve_bool");

    /**
     * A config field for a client context parameter.
     *
     * @param name the field name.
     * @param envVar the environment variable it resolves from, or null.
     * @param profileKey the shared config file key it resolves from, or null.
     */
    private record S3Field(String name, String envVar, String profileKey) {
        boolean resolves() {
            return envVar != null;
        }
    }

    @Override
    public List<RuntimeClientPlugin> getClientPlugins(GenerationContext context) {
        var service = context.settings().service(context.model());
        var sdkId = service.getTrait(ServiceTrait.class).map(ServiceTrait::getSdkId).orElse("");
        var trait = service.getTrait(ClientContextParamsTrait.class);
        if (!SDK_IDS.contains(sdkId) || trait.isEmpty()) {
            return List.of();
        }
        var plugin = RuntimeClientPlugin.builder();
        for (var entry : trait.get().getParameters().entrySet()) {
            var parameter = entry.getKey();
            var field = FIELDS.get(parameter);
            if (field == null) {
                continue;
            }
            var definition = entry.getValue();
            if (definition.getType() != ShapeType.BOOLEAN) {
                throw new CodegenException(String.format(
                        "Expected the client context parameter %s of %s to be a boolean",
                        parameter,
                        service.getId()));
            }
            var property = ConfigProperty.builder()
                    .name(field.name())
                    .type(Symbol.builder().name("bool").build())
                    .documentation(definition.getDocumentation().orElse("The " + parameter + " endpoint parameter."))
                    .endpointParameter(parameter);
            if (field.resolves()) {
                var function = "_resolve_" + field.name();
                property.resolver(writer -> writer.writeInline("$L", function))
                        .definitions(writer -> writeResolver(writer, function, field));
            }
            plugin.addConfigProperty(property.build());
        }
        return List.of(plugin.build());
    }

    private static void writeResolver(PythonWriter writer, String function, S3Field field) {
        writer.write("""
                async def $L(ctx: $T) -> $T[bool | None]:
                    return await $T(ctx, env_vars=($S,), profile_keys=($S,))""",
                function,
                ASYNC_SHARED_CONFIG_CONTEXT,
                RESOLVED,
                RESOLVE_BOOL,
                field.envVar(),
                field.profileKey());
    }

    private static Symbol awsCoreSymbol(String namespace, String name) {
        return Symbol.builder()
                .name(name)
                .namespace(namespace, ".")
                .addDependency(AwsPythonDependency.SMITHY_AWS_CORE)
                .build();
    }
}
