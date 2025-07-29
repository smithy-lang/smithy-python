/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.aws.codegen;

import static software.amazon.smithy.python.aws.codegen.AwsConfiguration.REGION;

import java.util.List;
import java.util.Set;
import software.amazon.smithy.aws.traits.auth.SigV4Trait;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.model.shapes.ServiceShape;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.python.codegen.ApplicationProtocol;
import software.amazon.smithy.python.codegen.CodegenUtils;
import software.amazon.smithy.python.codegen.ConfigProperty;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.SmithyPythonDependency;
import software.amazon.smithy.python.codegen.integrations.AuthScheme;
import software.amazon.smithy.python.codegen.integrations.PythonIntegration;
import software.amazon.smithy.python.codegen.integrations.RuntimeClientPlugin;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Adds support for AWS auth traits.
 */
@SmithyInternalApi
public class AwsAuthIntegration implements PythonIntegration {
    private static final String SIGV4_OPTION_GENERATOR_NAME = "_generate_sigv4_option";

    @Override
    public List<RuntimeClientPlugin> getClientPlugins(GenerationContext context) {
        if (!hasSigV4Auth(context)) {
            return List.of();
        }
        return List.of(
                RuntimeClientPlugin.builder()
                        .servicePredicate((model, service) -> service.hasTrait(SigV4Trait.class))
                        .addConfigProperty(ConfigProperty.builder()
                                // TODO: Naming of this config RE: backwards compatability/migation considerations
                                .name("aws_credentials_identity_resolver")
                                .documentation("Resolves AWS Credentials. Required for operations that use Sigv4 Auth.")
                                .type(Symbol.builder()
                                        .name("IdentityResolver[AWSCredentialsIdentity, AWSIdentityProperties]")
                                        .addReference(Symbol.builder()
                                                .addDependency(SmithyPythonDependency.SMITHY_CORE)
                                                .name("IdentityResolver")
                                                .namespace("smithy_core.aio.interfaces.identity", ".")
                                                .build())
                                        .addReference(Symbol.builder()
                                                .addDependency(AwsPythonDependency.SMITHY_AWS_CORE)
                                                .name("AWSCredentialsIdentity")
                                                .namespace("smithy_aws_core.identity", ".")
                                                .build())
                                        .addReference(Symbol.builder()
                                                .addDependency(SmithyPythonDependency.SMITHY_CORE)
                                                .name("AWSIdentityProperties")
                                                .namespace("smithy_aws_core.identity", ".")
                                                .build())
                                        .build())
                                // TODO: Initialize with the provider chain?
                                .nullable(true)
                                .build())
                        .addConfigProperty(REGION)
                        .addConfigProperty(ConfigProperty.builder()
                                .name("aws_access_key_id")
                                .type(Symbol.builder().name("str").build())
                                .documentation("The identifier for a secret access key.")
                                .nullable(true)
                                .build())
                        .addConfigProperty(ConfigProperty.builder()
                                .name("aws_secret_access_key")
                                .type(Symbol.builder().name("str").build())
                                .nullable(true)
                                .documentation("A secret access key that can be used to sign requests.")
                                .build())
                        .addConfigProperty(ConfigProperty.builder()
                                .name("aws_session_token")
                                .type(Symbol.builder().name("str").build())
                                .documentation("An access key ID that identifies temporary security credentials.")
                                .nullable(true)
                                .build())
                        .authScheme(new Sigv4AuthScheme())
                        .build());
    }

    @Override
    public void customize(GenerationContext context) {
        if (!hasSigV4Auth(context)) {
            return;
        }
        var resolver = CodegenUtils.getHttpAuthSchemeResolverSymbol(context.settings());

        // Add a function that generates the http auth option for api key auth.
        // This needs to be generated because there's modeled parameters that
        // must be accounted for.
        context.writerDelegator().useFileWriter(resolver.getDefinitionFile(), resolver.getNamespace(), writer -> {
            writer.addDependency(SmithyPythonDependency.SMITHY_HTTP);
            writer.addImport("smithy_core.interfaces.auth", "AuthOption", "AuthOptionProtocol");
            writer.addImports("smithy_core.auth", Set.of("AuthOption", "AuthParams"));
            writer.pushState();

            writer.write("""
                    def $1L(auth_params: AuthParams[Any, Any]) -> AuthOptionProtocol | None:
                        return AuthOption(
                            scheme_id=$2S,
                            identity_properties={},  # type: ignore
                            signer_properties={}  # type: ignore
                        )
                    """,
                    SIGV4_OPTION_GENERATOR_NAME,
                    SigV4Trait.ID.toString());
            writer.popState();
        });
    }

    private boolean hasSigV4Auth(GenerationContext context) {
        var service = context.settings().service(context.model());
        return service.hasTrait(SigV4Trait.class);
    }

    /**
     * The AuthScheme representing api key auth.
     */
    private static final class Sigv4AuthScheme implements AuthScheme {

        @Override
        public ShapeId getAuthTrait() {
            return SigV4Trait.ID;
        }

        @Override
        public ApplicationProtocol getApplicationProtocol() {
            return ApplicationProtocol.createDefaultHttpApplicationProtocol();
        }

        @Override
        public Symbol getAuthOptionGenerator(GenerationContext context) {
            var resolver = CodegenUtils.getHttpAuthSchemeResolverSymbol(context.settings());
            return Symbol.builder()
                    .name(SIGV4_OPTION_GENERATOR_NAME)
                    .namespace(resolver.getNamespace(), ".")
                    .definitionFile(resolver.getDefinitionFile())
                    .build();
        }

        @Override
        public Symbol getAuthSchemeSymbol(GenerationContext context) {
            return Symbol.builder()
                    .name("SigV4AuthScheme")
                    .namespace("smithy_aws_core.auth", ".")
                    .addDependency(AwsPythonDependency.SMITHY_AWS_CORE)
                    .build();
        }

        @Override
        public void initializeScheme(GenerationContext context, PythonWriter writer, ServiceShape service) {
            var trait = service.expectTrait(SigV4Trait.class);
            writer.write("$T(service=$S)", getAuthSchemeSymbol(context), trait.getName());
        }
    }
}
