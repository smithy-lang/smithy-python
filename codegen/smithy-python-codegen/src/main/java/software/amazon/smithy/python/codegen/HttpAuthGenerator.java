/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */

package software.amazon.smithy.python.codegen;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import software.amazon.smithy.codegen.core.Symbol;
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
        // TODO: populate this list
        var properties = new ArrayList<DerivedProperty>();

        var params = CodegenUtils.getHttpAuthParamsSymbol(settings);
        context.writerDelegator().useFileWriter(params.getDefinitionFile(), params.getNamespace(), writer -> {
            generateAuthParameters(writer, params, properties);
        });

        var resolver = CodegenUtils.getHttpAuthSchemeResolverSymbol(settings);
        context.writerDelegator().useFileWriter(resolver.getDefinitionFile(), resolver.getNamespace(), writer -> {
            generateAuthSchemeResolver(writer, params, resolver);
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

    private void generateAuthSchemeResolver(PythonWriter writer, Symbol paramsSymbol, Symbol resolverSymbol) {
        writer.pushState(new GenerateHttpAuthSchemeResolverSection());
        writer.addDependency(SmithyPythonDependency.SMITHY_PYTHON);
        writer.addImport("smithy_python.interfaces.auth", "HTTPAuthOption");
        writer.write("""
            class $1L:
                def resolve_auth_scheme(self, auth_parameters: $2T) -> list[HTTPAuthOption]:
                    return []
            """, resolverSymbol.getName(), paramsSymbol);
        writer.popState();
    }
}
