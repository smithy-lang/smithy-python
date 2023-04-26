/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */

package software.amazon.smithy.python.codegen;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.model.knowledge.ServiceIndex;
import software.amazon.smithy.model.knowledge.TopDownIndex;
import software.amazon.smithy.model.shapes.OperationShape;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.model.traits.AuthTrait;
import software.amazon.smithy.python.codegen.integration.AuthScheme;
import software.amazon.smithy.python.codegen.integration.PythonIntegration;
import software.amazon.smithy.python.codegen.integration.RuntimeClientPlugin;
import software.amazon.smithy.python.codegen.sections.GenerateHttpAuthParametersSection;
import software.amazon.smithy.python.codegen.sections.GenerateHttpAuthSchemeResolverSection;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * This class is responsible for generating the http auth scheme resolver and its configuration.
 */
@SmithyInternalApi
final class HttpAuthGenerator implements Runnable {

    private final PythonSettings settings;
    private final GenerationContext context;

    HttpAuthGenerator(GenerationContext context, PythonSettings settings) {
        this.settings = settings;
        this.context = context;
    }

    @Override
    public void run() {
        var supportedAuthSchemes = new HashMap<ShapeId, AuthScheme>();
        var properties = new ArrayList<DerivedProperty>();
        var service = context.settings().getService(context.model());
        for (PythonIntegration integration : context.integrations()) {
            for (RuntimeClientPlugin plugin : integration.getClientPlugins()) {
                if (plugin.matchesService(context.model(), service)
                        && plugin.getAuthScheme().isPresent()
                        && plugin.getAuthScheme().get().getApplicationProtocol().isHttpProtocol()) {
                    var scheme = plugin.getAuthScheme().get();
                    supportedAuthSchemes.put(scheme.getAuthTrait(), scheme);
                    properties.addAll(scheme.getAuthProperties());
                }
            }
        }

        var params = CodegenUtils.getHttpAuthParamsSymbol(settings);
        context.writerDelegator().useFileWriter(params.getDefinitionFile(), params.getNamespace(), writer -> {
            generateAuthParameters(writer, params, properties);
        });

        var resolver = CodegenUtils.getHttpAuthSchemeResolverSymbol(settings);
        context.writerDelegator().useFileWriter(resolver.getDefinitionFile(), resolver.getNamespace(), writer -> {
            generateAuthSchemeResolver(writer, params, resolver, supportedAuthSchemes);
        });
    }

    private void generateAuthParameters(PythonWriter writer, Symbol symbol, List<DerivedProperty> properties) {
        var propertyMap = new LinkedHashMap<String, Symbol>();
        for (DerivedProperty property : properties) {
            propertyMap.put(property.name(), property.type());
        }
        writer.pushState(new GenerateHttpAuthParametersSection(Map.copyOf(propertyMap)));
        writer.addStdlibImport("dataclasses", "dataclass");
        writer.write("""
            @dataclass
            class $L:
                operation: str
                ${#properties}
                ${key:L}: ${value:T} | None
                ${/properties}
            """, symbol.getName());
        writer.popState();
    }

    private void generateAuthSchemeResolver(
        PythonWriter writer,
        Symbol paramsSymbol,
        Symbol resolverSymbol,
        Map<ShapeId, AuthScheme> supportedAuthSchemes
    ) {
        var resolvedAuthSchemes = ServiceIndex.of(context.model())
            .getEffectiveAuthSchemes(settings.getService()).keySet().stream()
            .filter(supportedAuthSchemes::containsKey)
            .map(supportedAuthSchemes::get)
            .toList();

        writer.pushState(new GenerateHttpAuthSchemeResolverSection(resolvedAuthSchemes));
        writer.addDependency(SmithyPythonDependency.SMITHY_PYTHON);
        writer.addImport("smithy_python.interfaces.auth", "HTTPAuthOption");
        writer.write("""
            class $1L:
                def resolve_auth_scheme(self, auth_parameters: $2T) -> list[HTTPAuthOption]:
                    auth_options: list[HTTPAuthOption] = []

                    ${3C|}
                    ${4C|}

            """, resolverSymbol.getName(), paramsSymbol,
            writer.consumer(w -> writeOperationAuthOptions(w, supportedAuthSchemes)),
            writer.consumer(w -> writeAuthOptions(w, resolvedAuthSchemes)));
        writer.popState();
    }

    private void writeOperationAuthOptions(PythonWriter writer, Map<ShapeId, AuthScheme> supportedAuthSchemes) {
        var operations = TopDownIndex.of(context.model()).getContainedOperations(settings.getService());
        var serviceIndex = ServiceIndex.of(context.model());
        for (OperationShape operation : operations) {
            if (!operation.hasTrait(AuthTrait.class)) {
                continue;
            }

            var operationAuthSchemes = serviceIndex
                .getEffectiveAuthSchemes(settings.getService(), operation).keySet().stream()
                .filter(supportedAuthSchemes::containsKey)
                .map(supportedAuthSchemes::get)
                .toList();

            writer.write("""
                if auth_parameters.operation == $S:
                    ${C|}

                """, operation.getId().getName(), writer.consumer(w -> writeAuthOptions(w, operationAuthSchemes)));
        }
    }

    private void writeAuthOptions(PythonWriter writer, List<AuthScheme> authSchemes) {
        var authOptionInitializers = authSchemes.stream()
            .map(scheme -> scheme.getAuthOptionGenerator(context))
            .toList();
        writer.pushState();
        writer.putContext("authOptionInitializers", authOptionInitializers);
        writer.write("""
            ${#authOptionInitializers}
            if ((option := ${value:T}(auth_parameters)) is not None):
                auth_options.append(option)

            ${/authOptionInitializers}
            return auth_options
            """);
        writer.popState();
    }
}
