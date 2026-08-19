/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.aws.codegen;

import java.util.List;
import software.amazon.smithy.aws.traits.auth.SigV4Trait;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.SmithyPythonDependency;
import software.amazon.smithy.python.codegen.integrations.PythonIntegration;
import software.amazon.smithy.python.codegen.sections.ClientSetupSection;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.utils.CodeInterceptor;
import software.amazon.smithy.utils.CodeSection;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Sets up the default AWS credentials identity chain during client setup.
 */
@SmithyInternalApi
public class AwsIdentityIntegration implements PythonIntegration {

    @Override
    public List<? extends CodeInterceptor<? extends CodeSection, PythonWriter>> interceptors(
            GenerationContext context
    ) {
        var service = context.settings().service(context.model());
        if (!service.hasTrait(SigV4Trait.class)) {
            return List.of();
        }
        return List.of(new CredentialsIdentitySetupInterceptor());
    }

    /**
     * Initializes the default AWS credentials identity chain during client setup.
     */
    private static final class CredentialsIdentitySetupInterceptor
            implements CodeInterceptor<ClientSetupSection, PythonWriter> {

        @Override
        public Class<ClientSetupSection> sectionType() {
            return ClientSetupSection.class;
        }

        @Override
        public void write(PythonWriter writer, String previousText, ClientSetupSection section) {
            writer.write(previousText);
            writer.addStdlibImport("typing", "cast");
            writer.write("""
                    if self._config.aws_credentials_identity_resolver is None:
                        config_context = self._config.resolution_context()
                        config_file = None
                        profile_name = None
                        if config_context is not None:
                            config_file = await config_context.parsed_profiles()
                            if config_context.profile_source is $4T.OVERRIDE:
                                profile_name = config_context.profile_name
                        self._config.aws_credentials_identity_resolver = await $1T.create(
                            $2T,
                            config_file=config_file,
                            profile_name=profile_name,
                            region_override=self._config.region,
                            http_client=cast($3T | None, self._config.transport),
                        )""",
                    Symbol.builder()
                            .name("IdentityChain")
                            .namespace("smithy_aws_core.identity.chain", ".")
                            .addDependency(AwsPythonDependency.SMITHY_AWS_CORE)
                            .build(),
                    Symbol.builder()
                            .name("AWSCredentialsIdentity")
                            .namespace("smithy_aws_core.identity", ".")
                            .addDependency(AwsPythonDependency.SMITHY_AWS_CORE)
                            .build(),
                    Symbol.builder()
                            .name("HTTPClient")
                            .namespace("smithy_http.aio.interfaces", ".")
                            .addDependency(SmithyPythonDependency.SMITHY_HTTP)
                            .build(),
                    Symbol.builder()
                            .name("ConfigSource")
                            .namespace("smithy_aws_core.config", ".")
                            .addDependency(AwsPythonDependency.SMITHY_AWS_CORE)
                            .build());
        }
    }
}
