/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.integrations;

import java.util.List;
import java.util.Locale;
import java.util.Set;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.model.shapes.ServiceShape;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.model.traits.HttpApiKeyAuthTrait;
import software.amazon.smithy.python.codegen.ApplicationProtocol;
import software.amazon.smithy.python.codegen.CodegenUtils;
import software.amazon.smithy.python.codegen.ConfigProperty;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.PythonSettings;
import software.amazon.smithy.python.codegen.SmithyPythonDependency;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Adds support for the http api key auth.
 * {@see https://smithy.io/2.0/spec/authentication-traits.html#smithy-api-httpapikeyauth-trait}
 */
@SmithyInternalApi
public final class HttpApiKeyAuth implements PythonIntegration {
    private static final String OPTION_GENERATOR_NAME = "_generate_api_key_option";

    @Override
    public List<RuntimeClientPlugin> getClientPlugins(GenerationContext context) {
        return List.of(
                RuntimeClientPlugin.builder()
                        .servicePredicate((model, service) -> service.hasTrait(HttpApiKeyAuthTrait.class))
                        .addConfigProperty(ConfigProperty.builder()
                                .name("api_key")
                                .documentation("The API key to send along with requests.")
                                .type(Symbol.builder().name("str").build())
                                .nullable(true)
                                .build())
                        .addConfigProperty(ConfigProperty.builder()
                                .name("api_key_identity_resolver")
                                .documentation("Resolves the API key.")
                                .type(Symbol.builder()
                                        .name("IdentityResolver[APIKeyIdentity, APIKeyIdentityProperties]")
                                        .addReference(Symbol.builder()
                                                .addDependency(SmithyPythonDependency.SMITHY_CORE)
                                                .name("IdentityResolver")
                                                .namespace("smithy_core.aio.interfaces.identity", ".")
                                                .build())
                                        .addReference(Symbol.builder()
                                                .addDependency(SmithyPythonDependency.SMITHY_HTTP)
                                                .name("APIKeyIdentity")
                                                .namespace("smithy_http.aio.identity.apikey", ".")
                                                .build())
                                        .addReference(Symbol.builder()
                                                .addDependency(SmithyPythonDependency.SMITHY_HTTP)
                                                .name("APIKeyIdentityProperties")
                                                .namespace("smithy_http.aio.identity.apikey", ".")
                                                .build())
                                        .build())
                                .initialize(writer -> {
                                    writer.addImport("smithy_http.aio.identity.apikey", "APIKeyIdentityResolver");
                                    writer.write("""
                                            self.api_key_identity_resolver = (
                                                api_key_identity_resolver or APIKeyIdentityResolver()
                                            )
                                            """);
                                })
                                .build())
                        .authScheme(new ApiKeyAuthScheme())
                        .build());
    }

    @Override
    public void customize(GenerationContext context) {
        if (!hasApiKeyAuth(context)) {
            return;
        }
        var resolver = CodegenUtils.getHttpAuthSchemeResolverSymbol(context.settings());

        // Add a function that generates the http auth option for api key auth.
        // This needs to be generated because there's modeled parameters that
        // must be accounted for.
        context.writerDelegator().useFileWriter(resolver.getDefinitionFile(), resolver.getNamespace(), writer -> {
            writer.addDependency(SmithyPythonDependency.SMITHY_CORE);
            writer.addDependency(SmithyPythonDependency.SMITHY_HTTP);
            writer.addImport("smithy_core.interfaces.auth", "AuthOption", "AuthOptionProtocol");
            writer.addImports("smithy_core.auth", Set.of("AuthOption", "AuthParams"));
            writer.addImport("smithy_core.shapes", "ShapeID");
            writer.addStdlibImport("typing", "Any");
            writer.pushState();
            writer.write("""
                    def $1L(auth_params: AuthParams[Any, Any]) -> AuthOptionProtocol | None:
                        return AuthOption(
                            scheme_id=ShapeID($2S),
                            identity_properties={},  # type: ignore
                            signer_properties={},  # type: ignore
                        )
                    """,
                    OPTION_GENERATOR_NAME,
                    HttpApiKeyAuthTrait.ID.toString());
            writer.popState();
        });
    }

    private boolean hasApiKeyAuth(GenerationContext context) {
        if (context.settings().artifactType() == PythonSettings.ArtifactType.TYPES) {
            return false;
        }
        var service = context.settings().service(context.model());
        return service.hasTrait(HttpApiKeyAuthTrait.class);
    }

    /**
     * The AuthScheme representing api key auth.
     */
    private static final class ApiKeyAuthScheme implements AuthScheme {

        @Override
        public ShapeId getAuthTrait() {
            return HttpApiKeyAuthTrait.ID;
        }

        @Override
        public ApplicationProtocol getApplicationProtocol() {
            return ApplicationProtocol.createDefaultHttpApplicationProtocol();
        }

        @Override
        public Symbol getAuthOptionGenerator(GenerationContext context) {
            var resolver = CodegenUtils.getHttpAuthSchemeResolverSymbol(context.settings());
            return Symbol.builder()
                    .name(OPTION_GENERATOR_NAME)
                    .namespace(resolver.getNamespace(), ".")
                    .definitionFile(resolver.getDefinitionFile())
                    .build();
        }

        @Override
        public Symbol getAuthSchemeSymbol(GenerationContext context) {
            return Symbol.builder()
                    .name("APIKeyAuthScheme")
                    .namespace("smithy_http.aio.auth.apikey", ".")
                    .addDependency(SmithyPythonDependency.SMITHY_HTTP)
                    .build();
        }

        @Override
        public void initializeScheme(GenerationContext context, PythonWriter writer, ServiceShape service) {
            var trait = service.expectTrait(HttpApiKeyAuthTrait.class);
            writer.pushState();
            writer.putContext("scheme", trait.getScheme().orElse(null));
            writer.addImport("smithy_core.traits", "APIKeyLocation");
            writer.write("""
                    $T(
                        name=$S,
                        location=APIKeyLocation.$L,
                        ${?scheme}
                        scheme=${scheme:S},
                        ${/scheme}
                    )
                    """,
                    getAuthSchemeSymbol(context),
                    trait.getName(),
                    trait.getIn().name().toUpperCase(Locale.ENGLISH));
            writer.popState();
        }
    }
}
