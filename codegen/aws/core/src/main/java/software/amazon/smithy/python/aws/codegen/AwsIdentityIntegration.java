/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.aws.codegen;

import java.util.List;
import software.amazon.smithy.aws.traits.auth.SigV4Trait;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.model.traits.HttpBearerAuthTrait;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.RuntimeTypes;
import software.amazon.smithy.python.codegen.SmithyPythonDependency;
import software.amazon.smithy.python.codegen.SyncVariant;
import software.amazon.smithy.python.codegen.integrations.PythonIntegration;
import software.amazon.smithy.python.codegen.sections.ClientSetupSection;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.utils.CodeInterceptor;
import software.amazon.smithy.utils.CodeSection;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Sets up the default identity resolvers during client setup.
 *
 * <p>For services using SigV4 this wires the default AWS credentials identity chain.
 * For services using {@code smithy.api#httpBearerAuth} it wires a static token
 * resolver so a configured {@code token} is honored, matching the generic client
 * config. A default token provider chain is not yet wired here.
 */
@SmithyInternalApi
public class AwsIdentityIntegration implements PythonIntegration {

    @Override
    public List<? extends CodeInterceptor<? extends CodeSection, PythonWriter>> interceptors(
            GenerationContext context
    ) {
        var service = context.settings().service(context.model());
        var hasSigV4 = service.hasTrait(SigV4Trait.class);
        var hasBearer = service.hasTrait(HttpBearerAuthTrait.class);
        if (!hasSigV4 && !hasBearer) {
            return List.of();
        }
        return List.of(new IdentitySetupInterceptor(hasSigV4, hasBearer));
    }

    /**
     * Initializes the default identity resolvers during client setup.
     */
    private static final class IdentitySetupInterceptor
            implements CodeInterceptor<ClientSetupSection, PythonWriter> {

        private final boolean hasSigV4;
        private final boolean hasBearer;

        IdentitySetupInterceptor(boolean hasSigV4, boolean hasBearer) {
            this.hasSigV4 = hasSigV4;
            this.hasBearer = hasBearer;
        }

        @Override
        public Class<ClientSetupSection> sectionType() {
            return ClientSetupSection.class;
        }

        @Override
        public void write(PythonWriter writer, String previousText, ClientSetupSection section) {
            if (!previousText.isBlank()) {
                writer.write(previousText);
            }
            var header = "async def _post_setup(self, config: $T) -> None:";
            writer.openBlock(section.sync() ? SyncVariant.toSyncCode(header) : header,
                    "",
                    section.config(),
                    () -> {
                        if (hasSigV4) {
                            writeCredentialsSetup(writer, section);
                        }
                        if (hasBearer) {
                            writeBearerTokenSetup(writer, section);
                        }
                    });
        }

        private void writeCredentialsSetup(PythonWriter writer, ClientSetupSection section) {
            writer.addStdlibImport("typing", "cast");
            var template = """
                    if config.aws_credentials_identity_resolver is None:
                        config_context = config.resolution_context()
                        config_file = None
                        profile_name = None
                        if config_context is not None:
                            config_file = await config_context.parsed_profiles()
                            if config_context.profile_source is $4T.OVERRIDE:
                                profile_name = config_context.profile_name
                        config.aws_credentials_identity_resolver = await $1T.create(
                            $2T,
                            config_file=config_file,
                            profile_name=profile_name,
                            region_override=config.region,
                            http_client=cast($3T | None, config.transport),
                        )
                    """;
            writer.write(section.sync() ? SyncVariant.toSyncCode(template) : template,
                    identityChain(section.sync()),
                    AwsRuntimeTypes.AWS_CREDENTIALS_IDENTITY,
                    Symbol.builder()
                            .name("AsyncHTTPClient")
                            .namespace("smithy_http.aio.interfaces", ".")
                            .addDependency(SmithyPythonDependency.SMITHY_HTTP)
                            .build(),
                    Symbol.builder()
                            .name("ConfigSource")
                            .namespace("smithy_aws_core.config.types", ".")
                            .addDependency(AwsPythonDependency.SMITHY_AWS_CORE)
                            .build());
        }

        // The static resolver reads the configured ``token`` from the identity
        // properties the bearer auth scheme supplies, so ``token="..."`` works
        // without an explicit resolver. The sync writer maps the symbol to its twin.
        private void writeBearerTokenSetup(PythonWriter writer, ClientSetupSection section) {
            writer.write("""
                    if config.token_identity_resolver is None:
                        config.token_identity_resolver = $T()
                    """, RuntimeTypes.TOKEN_IDENTITY_RESOLVER);
        }

        // The sync twin is defined in a submodule the aio-stripping convention can't derive.
        private static Symbol identityChain(boolean sync) {
            return Symbol.builder()
                    .name(sync ? "IdentityChain" : "AsyncIdentityChain")
                    .namespace(sync
                            ? "smithy_aws_core.identity.chain.resolver"
                            : "smithy_aws_core.aio.identity.chain", ".")
                    .addDependency(AwsPythonDependency.SMITHY_AWS_CORE)
                    .build();
        }
    }
}
