/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.aws.codegen;

import java.util.List;
import software.amazon.smithy.aws.traits.HttpChecksumTrait;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.codegen.core.SymbolReference;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.knowledge.TopDownIndex;
import software.amazon.smithy.model.shapes.ServiceShape;
import software.amazon.smithy.python.codegen.CodegenUtils;
import software.amazon.smithy.python.codegen.ConfigProperty;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.integrations.PythonIntegration;
import software.amazon.smithy.python.codegen.integrations.RuntimeClientPlugin;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Adds the flexible checksums interceptor to clients of services with operations that
 * have the {@code aws.protocols#httpChecksum} trait.
 *
 * <p>The interceptor is added once for the whole client and passes through operations
 * without the trait. Adding it per operation would copy the client's config on every
 * call to those operations.
 */
@SmithyInternalApi
public final class AwsFlexibleChecksumsIntegration implements PythonIntegration {

    private static final String PLUGIN_FILE = "checksums";

    private static final String CHECKSUMS_PLUGIN = """
            def flexible_checksums_plugin(config: $1T) -> None:
                config.interceptors.append($2T())
            """;

    private static final ConfigProperty RESPONSE_CHECKSUM_VALIDATION = ConfigProperty.builder()
            .name("response_checksum_validation")
            .type(Symbol.builder()
                    .namespace("smithy_aws_core.config.types", ".")
                    .name("ResponseChecksumValidation")
                    .addDependency(AwsPythonDependency.SMITHY_AWS_CORE)
                    .build())
            .nullable(true)
            .documentation("When to validate the checksums of response payloads: ``when_supported`` "
                    + "(the default) validates them for every operation that models response "
                    + "checksums, and ``when_required`` only when validation is enabled on the "
                    + "request, such as with ``checksum_mode``. A payload is validated when it's "
                    + "read to the end, and a mismatch raises ``ChecksumMismatchError``.")
            .defaultValue("when_supported")
            .resolver(writer -> writer.writeInline("$T",
                    Symbol.builder()
                            .namespace("smithy_aws_core.aio.config.resolvers", ".")
                            .name("resolve_response_checksum_validation")
                            .addDependency(AwsPythonDependency.SMITHY_AWS_CORE)
                            .build()))
            .validator(Symbol.builder()
                    .namespace("smithy_aws_core.config.validators", ".")
                    .name("validate_response_checksum_validation")
                    .addDependency(AwsPythonDependency.SMITHY_AWS_CORE)
                    .build())
            .build();

    @Override
    public List<RuntimeClientPlugin> getClientPlugins(GenerationContext context) {
        var model = context.model();
        var service = context.settings().service(model);
        if (!hasHttpChecksumOperation(model, service)
                || CodegenUtils.getAsyncConfigSymbol(context.settings(), model).isEmpty()) {
            return List.of();
        }

        final String moduleName = context.settings().moduleName();
        final SymbolReference plugin = SymbolReference.builder()
                .symbol(Symbol.builder()
                        .namespace(String.format("%s.%s", moduleName, PLUGIN_FILE), ".")
                        .definitionFile(String.format("./src/%s/%s.py", moduleName, PLUGIN_FILE))
                        .name("flexible_checksums_plugin")
                        .build())
                .build();
        final Symbol interceptor = Symbol.builder()
                .namespace("smithy_aws_core.interceptors.checksums", ".")
                .name("FlexibleChecksumsInterceptor")
                .addDependency(AwsPythonDependency.SMITHY_AWS_CORE.withOptionalDependencies("checksums"))
                .build();

        return List.of(
                RuntimeClientPlugin.builder()
                        .addConfigProperty(RESPONSE_CHECKSUM_VALIDATION)
                        .pythonPlugin(plugin)
                        .writeAdditionalFiles((c) -> {
                            String filename = "src/%s/%s.py".formatted(moduleName, PLUGIN_FILE);
                            c.writerDelegator()
                                    .useFileWriter(filename, moduleName + ".", writer -> {
                                        writer.write(CHECKSUMS_PLUGIN,
                                                CodegenUtils.getAsyncConfigSymbol(c.settings(), c.model())
                                                        .orElseThrow(),
                                                interceptor);
                                    });
                            return List.of(filename);
                        })
                        .build());
    }

    static boolean hasHttpChecksumOperation(Model model, ServiceShape service) {
        return TopDownIndex.of(model)
                .getContainedOperations(service)
                .stream()
                .anyMatch(operation -> operation.hasTrait(HttpChecksumTrait.class));
    }
}
