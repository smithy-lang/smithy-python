/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */

package software.amazon.smithy.python.codegen.integration;

import java.util.List;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.model.traits.HttpApiKeyAuthTrait;
import software.amazon.smithy.python.codegen.ApplicationProtocol;
import software.amazon.smithy.python.codegen.CodegenUtils;
import software.amazon.smithy.python.codegen.ConfigProperty;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.SmithyPythonDependency;

/**
 * Adds support for the http api key auth.
 * {@see https://smithy.io/2.0/spec/authentication-traits.html#smithy-api-httpapikeyauth-trait}
 */
public final class HttpApiKeyAuth implements PythonIntegration {
    private static final String OPTION_GENERATOR_NAME = "_generate_api_key_option";

    @Override
    public List<RuntimeClientPlugin> getClientPlugins() {
        return List.of(
            RuntimeClientPlugin.builder()
                .servicePredicate((model, service) -> service.hasTrait(HttpApiKeyAuthTrait.class))
                .addConfigProperty(ConfigProperty.builder()
                    .name("api_key_identity_resolver")
                    .documentation("Resolves the API key. Required for operations that use API key auth.")
                    .type(Symbol.builder()
                        .name("IdentityResolver[ApiKeyIdentity, IdentityProperties]")
                        .addReference(Symbol.builder()
                            .addDependency(SmithyPythonDependency.SMITHY_PYTHON)
                            .name("IdentityResolver")
                            .namespace("smithy_python.interfaces.identity", ".")
                            .build())
                        .addReference(Symbol.builder()
                            .addDependency(SmithyPythonDependency.SMITHY_PYTHON)
                            .name("ApiKeyIdentity")
                            .namespace("smithy_python._private.api_key_auth", ".")
                            .build())
                        .addReference(Symbol.builder()
                            .addDependency(SmithyPythonDependency.SMITHY_PYTHON)
                            .name("IdentityProperties")
                            .namespace("smithy_python.interfaces.identity", ".")
                            .build())
                        .build())
                    .nullable(true)
                    .build())
                .authScheme(new ApiKeyAuthScheme())
                .build()
        );
    }

    @Override
    public void customize(GenerationContext context) {
        if (!hasApiKeyAuth(context)) {
            return;
        }
        var trait = context.settings().getService(context.model()).expectTrait(HttpApiKeyAuthTrait.class);
        var params = CodegenUtils.getHttpAuthParamsSymbol(context.settings());
        var resolver = CodegenUtils.getHttpAuthSchemeResolverSymbol(context.settings());

        // Add a function that generates the http auth option for api key auth.
        // This needs to be generated because there's modeled parameters that
        // must be accounted for.
        context.writerDelegator().useFileWriter(resolver.getDefinitionFile(), resolver.getNamespace(), writer -> {
            writer.addDependency(SmithyPythonDependency.SMITHY_PYTHON);
            writer.addImport("smithy_python.interfaces.auth", "HTTPAuthOption");
            writer.addImport("smithy_python._private.api_key_auth", "ApiKeyLocation");
            writer.pushState();

            // Push the scheme into the context to allow for conditionally adding
            // it to the properties dict.
            writer.putContext("scheme", trait.getScheme().orElse(null));
            writer.write("""
                def $1L(auth_params: $2T) -> HTTPAuthOption:
                    return HTTPAuthOption(
                        scheme_id=$3S,
                        identity_properties={},
                        signer_properties={
                            "name": $4S,
                            "location": ApiKeyLocation($5S),
                            ${?scheme}
                            "scheme": ${scheme:S},
                            ${/scheme}
                        }
                    )
                """, OPTION_GENERATOR_NAME, params, HttpApiKeyAuthTrait.ID.toString(),
                trait.getName(), trait.getIn().toString());
            writer.popState();
        });
    }

    private boolean hasApiKeyAuth(GenerationContext context) {
        var service = context.settings().getService(context.model());
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
                .name("ApiKeyAuthScheme")
                .namespace("smithy_python._private.api_key_auth", ".")
                .addDependency(SmithyPythonDependency.SMITHY_PYTHON)
                .build();
        }
    }
}
