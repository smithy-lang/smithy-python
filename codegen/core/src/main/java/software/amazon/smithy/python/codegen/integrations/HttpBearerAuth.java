/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.integrations;

import java.util.List;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.model.shapes.ServiceShape;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.model.traits.HttpBearerAuthTrait;
import software.amazon.smithy.python.codegen.ApplicationProtocol;
import software.amazon.smithy.python.codegen.CodegenUtils;
import software.amazon.smithy.python.codegen.ConfigProperty;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.PythonSettings;
import software.amazon.smithy.python.codegen.RuntimeTypes;
import software.amazon.smithy.python.codegen.SmithyPythonDependency;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Adds support for the http bearer auth.
 * {@see https://smithy.io/2.0/spec/authentication-traits.html#smithy-api-httpbearerauth-trait}
 */
@SmithyInternalApi
public final class HttpBearerAuth implements PythonIntegration {
    private static final String OPTION_GENERATOR_NAME = "_generate_bearer_option";

    @Override
    public List<RuntimeClientPlugin> getClientPlugins(GenerationContext context) {
        return List.of(
                RuntimeClientPlugin.builder()
                        .servicePredicate((model, service) -> service.hasTrait(HttpBearerAuthTrait.class))
                        .addConfigProperty(ConfigProperty.builder()
                                .name("token")
                                .documentation("The bearer token to send along with requests.")
                                .type(Symbol.builder().name("str").build())
                                .nullable(true)
                                .build())
                        .addConfigProperty(ConfigProperty.builder()
                                .name("token_identity_resolver")
                                .documentation("Resolves the bearer token.")
                                .type(Symbol.builder()
                                        .name("AsyncIdentityResolver[TokenIdentity, TokenIdentityProperties]")
                                        .addReference(Symbol.builder()
                                                .addDependency(SmithyPythonDependency.SMITHY_CORE)
                                                .name("AsyncIdentityResolver")
                                                .namespace("smithy_core.aio.interfaces.identity", ".")
                                                .build())
                                        .addReference(Symbol.builder()
                                                .addDependency(SmithyPythonDependency.SMITHY_HTTP)
                                                .name("TokenIdentity")
                                                .namespace("smithy_http.identity", ".")
                                                .build())
                                        .addReference(Symbol.builder()
                                                .addDependency(SmithyPythonDependency.SMITHY_HTTP)
                                                .name("TokenIdentityProperties")
                                                .namespace("smithy_http.identity", ".")
                                                .build())
                                        .build())
                                .initialize(writer -> {
                                    writer.write("""
                                            self.token_identity_resolver = (
                                                token_identity_resolver or $T()
                                            )
                                            """, RuntimeTypes.TOKEN_IDENTITY_RESOLVER);
                                })
                                .build())
                        .authScheme(new BearerAuthScheme())
                        .build());
    }

    @Override
    public void customize(GenerationContext context) {
        if (!hasBearerAuth(context)) {
            return;
        }
        var resolver = CodegenUtils.getHttpAuthSchemeResolverSymbol(context.settings());

        // Add a function that generates the http auth option for bearer auth. The
        // trait has no modeled parameters, so the option is static; the function is
        // generated anyway so every scheme is wired into the resolver the same way.
        context.writerDelegator().useFileWriter(resolver.getDefinitionFile(), resolver.getNamespace(), writer -> {
            writer.addDependency(SmithyPythonDependency.SMITHY_CORE);
            writer.addDependency(SmithyPythonDependency.SMITHY_HTTP);
            writer.addStdlibImport("typing", "Any");
            writer.pushState();
            writer.write("""
                    def $1L(auth_params: $2T[Any, Any]) -> $3T | None:
                        return $4T(
                            scheme_id=$5T($6S),
                            identity_properties={},  # type: ignore
                            signer_properties={},  # type: ignore
                        )
                    """,
                    OPTION_GENERATOR_NAME,
                    RuntimeTypes.AUTH_PARAMS,
                    RuntimeTypes.AUTH_OPTION_INTERFACE,
                    RuntimeTypes.AUTH_OPTION,
                    RuntimeTypes.SHAPE_ID,
                    HttpBearerAuthTrait.ID.toString());
            writer.popState();
        });
    }

    private boolean hasBearerAuth(GenerationContext context) {
        if (context.settings().artifactType() == PythonSettings.ArtifactType.TYPES) {
            return false;
        }
        var service = context.settings().service(context.model());
        return service.hasTrait(HttpBearerAuthTrait.class);
    }

    /**
     * The AuthScheme representing bearer auth.
     */
    private static final class BearerAuthScheme implements AuthScheme {

        @Override
        public ShapeId getAuthTrait() {
            return HttpBearerAuthTrait.ID;
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
                    .name("AsyncBearerAuthScheme")
                    .namespace("smithy_http.aio.auth.bearer", ".")
                    .addDependency(SmithyPythonDependency.SMITHY_HTTP)
                    .build();
        }

        @Override
        public void initializeScheme(GenerationContext context, PythonWriter writer, ServiceShape service) {
            writer.write("$T()", getAuthSchemeSymbol(context));
        }
    }
}
