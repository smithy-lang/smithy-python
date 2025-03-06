/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.generators;

import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.python.codegen.CodegenUtils;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.PythonSettings;
import software.amazon.smithy.python.codegen.SmithyPythonDependency;
import software.amazon.smithy.python.codegen.sections.EndpointParametersSection;
import software.amazon.smithy.python.codegen.sections.EndpointResolverSection;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * This class is responsible for generating the endpoint resolver and its parameters.
 */
@SmithyInternalApi
public final class EndpointsGenerator implements Runnable {

    private final PythonSettings settings;
    private final GenerationContext context;

    public EndpointsGenerator(GenerationContext context, PythonSettings settings) {
        this.context = context;
        this.settings = settings;
    }

    @Override
    public void run() {
        var params = CodegenUtils.getEndpointParametersSymbol(settings);
        context.writerDelegator().useFileWriter(params.getDefinitionFile(), params.getNamespace(), writer -> {
            generateEndpointParameters(writer, params);
        });

        var resolver = CodegenUtils.getEndpointResolverSymbol(settings);
        context.writerDelegator().useFileWriter(resolver.getDefinitionFile(), resolver.getNamespace(), writer -> {
            generateEndpointResolver(writer, resolver);
        });
    }

    private void generateEndpointParameters(PythonWriter writer, Symbol params) {
        writer.pushState(new EndpointParametersSection());
        writer.addDependency(SmithyPythonDependency.SMITHY_HTTP);
        writer.write("from smithy_http.endpoints import StaticEndpointParams");
        writer.write("$L = StaticEndpointParams", params.getName());
        writer.popState();
    }

    private void generateEndpointResolver(PythonWriter writer, Symbol resolver) {
        writer.pushState(new EndpointResolverSection());
        writer.addDependency(SmithyPythonDependency.SMITHY_HTTP);
        writer.write("from smithy_http.aio.endpoints import StaticEndpointResolver");
        writer.write("$L = StaticEndpointResolver", resolver.getName());
        writer.popState();
    }
}
