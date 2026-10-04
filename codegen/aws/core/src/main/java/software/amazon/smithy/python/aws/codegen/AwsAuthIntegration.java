/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.aws.codegen;

import static software.amazon.smithy.python.aws.codegen.AwsConfiguration.REGION;

import java.util.List;
import software.amazon.smithy.aws.traits.auth.SigV4Trait;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.model.shapes.ServiceShape;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.python.codegen.ApplicationProtocol;
import software.amazon.smithy.python.codegen.CodegenUtils;
import software.amazon.smithy.python.codegen.ConfigProperty;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.RuntimeTypes;
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
    // S3 and S3 Control share this signing name and its signing requirements.
    private static final String S3_SIGNING_NAME = "s3";

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
                                .documentation("The session token used with temporary AWS credentials.")
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
            writer.pushState();

            writer.write("""
                    def $1L(auth_params: $2T[Any, Any]) -> $3T | None:
                        return $4T(
                            scheme_id=$5T($6S),
                            identity_properties={},  # type: ignore
                            signer_properties=${7C|}  # type: ignore
                        )
                    """,
                    SIGV4_OPTION_GENERATOR_NAME,
                    RuntimeTypes.AUTH_PARAMS,
                    RuntimeTypes.AUTH_OPTION_INTERFACE,
                    RuntimeTypes.AUTH_OPTION,
                    RuntimeTypes.SHAPE_ID,
                    SigV4Trait.ID.toString(),
                    writer.consumer(w -> writeSignerProperties(context, w)));
            writer.popState();
        });
    }

    private void writeSignerProperties(GenerationContext context, PythonWriter writer) {
        if (!usesS3Signing(context.settings().service(context.model()))) {
            writer.writeInline("{}");
            return;
        }
        // S3 signs the URI path exactly as it's sent, so it must not be encoded a
        // second time or normalized. S3 also requires the payload hash to be sent
        // in the X-Amz-Content-SHA256 header.
        writer.writeInline("""
                {
                    "uri_encode_path": False,
                    "normalize_path": False,
                    "content_checksum_enabled": True,
                }""");
    }

    static boolean usesS3Signing(ServiceShape service) {
        return service.getTrait(SigV4Trait.class)
                .map(trait -> S3_SIGNING_NAME.equals(trait.getName()))
                .orElse(false);
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
                    .name("AsyncSigV4AuthScheme")
                    .namespace("smithy_aws_core.auth", ".")
                    .addDependency(AwsPythonDependency.SMITHY_AWS_CORE)
                    .build();
        }

        @Override
        public void initializeScheme(GenerationContext context, PythonWriter writer, ServiceShape service) {
            var trait = service.expectTrait(SigV4Trait.class);
            writer.write("$T(service=$S)", getAuthSchemeSymbol(context), trait.getName());
        }

        @Override
        public void initializeSyncScheme(GenerationContext context, PythonWriter writer, ServiceShape service) {
            var trait = service.expectTrait(SigV4Trait.class);
            var syncScheme = Symbol.builder()
                    .name("SigV4AuthScheme")
                    .namespace("smithy_aws_core.auth", ".")
                    .addDependency(AwsPythonDependency.SMITHY_AWS_CORE)
                    .build();
            writer.write("$T(service=$S)", syncScheme, trait.getName());
        }
    }
}
