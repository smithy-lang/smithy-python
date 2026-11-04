/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.generators;

import software.amazon.smithy.codegen.core.SymbolProvider;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.knowledge.ServiceIndex;
import software.amazon.smithy.model.shapes.OperationShape;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.SymbolProperties;
import software.amazon.smithy.python.codegen.writer.PythonWriter;
import software.amazon.smithy.utils.SmithyInternalApi;

@SmithyInternalApi
public final class OperationGenerator implements Runnable {
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

        writer.write("""
                _operation_data[$1S] = (
                    $2S,
                    (
                        $3C
                    ),
                    (
                        $4C
                    ),
                )
                """,
                opSymbol.getName(),
                opSymbol.expectProperty(SymbolProperties.SCHEMA).getSymbol().getName(),
                writer.consumer(this::writeErrorIds),
                writer.consumer(this::writeAuthSchemes));
    }

    private void writeErrorIds(PythonWriter writer) {
        for (var error : shape.getErrors()) {
            writer.write("$S,", error);
        }
    }

    private void writeAuthSchemes(PythonWriter writer) {
        var authSchemes = ServiceIndex.of(model)
                .getEffectiveAuthSchemes(context.settings().service(),
                        shape.getId(),
                        ServiceIndex.AuthSchemeMode.NO_AUTH_AWARE);

        for (var authSchemeId : authSchemes.keySet()) {
            writer.write("$S,", authSchemeId);
        }
    }
}
