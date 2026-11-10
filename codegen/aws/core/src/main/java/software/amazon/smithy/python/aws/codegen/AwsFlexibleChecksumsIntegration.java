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
import software.amazon.smithy.python.codegen.SyncVariant;
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

    // The sync plugin gets FlexibleChecksumsInterceptor, this symbol's sync twin.
    private static final Symbol ASYNC_INTERCEPTOR = Symbol.builder()
            .namespace("smithy_aws_core.aio.interceptors.checksums", ".")
            .name("AsyncFlexibleChecksumsInterceptor")
            .addDependency(AwsPythonDependency.SMITHY_AWS_CORE.withOptionalDependencies("checksums"))
            .build();

    private static final ConfigProperty REQUEST_CHECKSUM_CALCULATION = checksumSetting(
            "request_checksum_calculation",
            "RequestChecksumCalculation",
            "When to calculate checksums of request payloads: ``when_supported`` (the "
                    + "default) calculates them for every operation that supports request "
                    + "checksums, and ``when_required`` only when the operation requires one or "
                    + "an algorithm is set on the request, such as with ``checksum_algorithm``. "
                    + "A checksum set on the request is sent as is.");

    private static final ConfigProperty RESPONSE_CHECKSUM_VALIDATION = checksumSetting(
            "response_checksum_validation",
            "ResponseChecksumValidation",
            "When to validate the checksums of response payloads: ``when_supported`` "
                    + "(the default) validates them for every operation that models response "
                    + "checksums, and ``when_required`` only when validation is enabled on the "
                    + "request, such as with ``checksum_mode``. A payload is validated when it's "
                    + "read to the end, and a mismatch raises ``ChecksumMismatchError``.");

    // The type, resolver program, and validator of each setting are named after
    // it in smithy-aws-core.
    private static ConfigProperty checksumSetting(String name, String typeName, String documentation) {
        return ConfigProperty.builder()
                .name(name)
                .type(Symbol.builder()
                        .namespace("smithy_aws_core.config.types", ".")
                        .name(typeName)
                        .addDependency(AwsPythonDependency.SMITHY_AWS_CORE)
                        .build())
                .nullable(true)
                .documentation(documentation)
                .defaultValue("when_supported")
                .resolver(writer -> writer.writeInline("$T",
                        Symbol.builder()
                                .namespace("smithy_aws_core.config.resolvers", ".")
                                .name("resolve_" + name + "_program")
                                .addDependency(AwsPythonDependency.SMITHY_AWS_CORE)
                                .build()))
                .validator(Symbol.builder()
                        .namespace("smithy_aws_core.config.validators", ".")
                        .name("validate_" + name)
                        .addDependency(AwsPythonDependency.SMITHY_AWS_CORE)
                        .build())
                .build();
    }

    @Override
    public List<RuntimeClientPlugin> getClientPlugins(GenerationContext context) {
        var model = context.model();
        var service = context.settings().service(model);
        var traits = checksumTraits(model, service);
        if (traits.isEmpty() || !CodegenUtils.isAwsService(context)) {
            return List.of();
        }

        final SymbolReference plugin = SymbolReference.builder()
                .symbol(CodegenUtils.aioSymbol(context.settings(), PLUGIN_FILE, "flexible_checksums_plugin"))
                .build();

        // Each setting is only added to clients it has an effect on.
        var builder = RuntimeClientPlugin.builder();
        if (traits.stream().anyMatch(AwsFlexibleChecksumsIntegration::hasRequestChecksum)) {
            builder.addConfigProperty(REQUEST_CHECKSUM_CALCULATION);
        }
        if (traits.stream().anyMatch(AwsFlexibleChecksumsIntegration::hasResponseChecksum)) {
            builder.addConfigProperty(RESPONSE_CHECKSUM_VALIDATION);
        }
        return List.of(
                builder
                        .pythonPlugin(plugin)
                        .writeAdditionalFiles((c) -> {
                            var filename = plugin.getSymbol().getDefinitionFile();
                            var asyncConfig = CodegenUtils.getAsyncConfigSymbol(c.settings(), c.model());
                            c.writerDelegator()
                                    .useFileWriter(filename,
                                            plugin.getSymbol().getNamespace(),
                                            writer -> writer.write(CHECKSUMS_PLUGIN,
                                                    asyncConfig,
                                                    ASYNC_INTERCEPTOR));
                            var syncFile = SyncVariant.writeSyncTwin(c,
                                    plugin.getSymbol(),
                                    CHECKSUMS_PLUGIN,
                                    asyncConfig,
                                    ASYNC_INTERCEPTOR);
                            return List.of(filename, syncFile);
                        })
                        .build());
    }

    static List<HttpChecksumTrait> checksumTraits(Model model, ServiceShape service) {
        return TopDownIndex.of(model)
                .getContainedOperations(service)
                .stream()
                .flatMap(operation -> operation.getTrait(HttpChecksumTrait.class).stream())
                .toList();
    }

    static boolean hasRequestChecksum(HttpChecksumTrait trait) {
        return trait.isRequestChecksumRequired() || trait.getRequestAlgorithmMember().isPresent();
    }

    static boolean hasResponseChecksum(HttpChecksumTrait trait) {
        return !trait.getResponseAlgorithms().isEmpty() && trait.getRequestValidationModeMember().isPresent();
    }
}
