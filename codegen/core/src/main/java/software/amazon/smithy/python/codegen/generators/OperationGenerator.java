/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.generators;

import java.util.logging.Logger;
import software.amazon.smithy.codegen.core.SymbolProvider;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.knowledge.ServiceIndex;
import software.amazon.smithy.model.shapes.OperationShape;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.RuntimeTypes;
import software.amazon.smithy.python.codegen.SmithyPythonDependency;
import software.amazon.smithy.python.codegen.SymbolProperties;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.utils.SmithyInternalApi;

@SmithyInternalApi
public final class OperationGenerator implements Runnable {
    private static final Logger LOGGER = Logger.getLogger(OperationGenerator.class.getName());

    private final GenerationContext context;
    private final PythonWriter writer;
    private final OperationShape shape;
    private final SymbolProvider symbolProvider;
    private final Model model;

    public OperationGenerator(GenerationContext context, PythonWriter writer, OperationShape shape) {
        this.context = context;
        this.writer = writer;
        this.shape = shape;
        this.symbolProvider = context.symbolProvider();
        this.model = context.model();
    }

    @Override
    public void run() {
        var opSymbol = symbolProvider.toSymbol(shape);
        writer.addLocallyDefinedSymbol(opSymbol);

        writer.addDependency(SmithyPythonDependency.SMITHY_CORE);

        writer.write("""
                $1L = $2T(
                        static_schema = $3T,
                        model_registry = _registry,
                        error_ids = [
                            $4C
                        ],
                        effective_auth_schemes = [
                            $5C
                        ],
                )
                """,
                opSymbol.getName(),
                RuntimeTypes.API_OPERATION,
                opSymbol.expectProperty(SymbolProperties.SCHEMA),
                writer.consumer(this::writeErrorIds),
                writer.consumer(this::writeAuthSchemes));
    }

    private void writeErrorIds(PythonWriter writer) {
        for (var error : shape.getErrors()) {
            writer.write("$1T($2S),", RuntimeTypes.SHAPE_ID, error);
        }
    }

    private void writeAuthSchemes(PythonWriter writer) {
        var authSchemes = ServiceIndex.of(model)
                .getEffectiveAuthSchemes(context.settings().service(),
                        shape.getId(),
                        ServiceIndex.AuthSchemeMode.NO_AUTH_AWARE);

        for (var authSchemeId : authSchemes.keySet()) {
            writer.write("$1T($2S),", RuntimeTypes.SHAPE_ID, authSchemeId);
        }

    }
}
